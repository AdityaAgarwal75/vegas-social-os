"""Control observations must describe real work and preserve original media."""
import base64
from datetime import datetime, timezone
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from vso import activity, control, projects, recovery, tools
from vso.engine import Engine
from vso.store import Store


class ControlPanelTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.e = Engine(Store(self.temp.name))
        self.s = self.e.store

    def tearDown(self):
        self.temp.cleanup()

    def asset(self, suffix=b'one'):
        return self.e.asset_import(base64.b64encode(b'\x89PNG\r\n\x1a\n'+suffix).decode(), 'image/png')

    def test_named_projects_keep_media_bytes_and_membership(self):
        a = self.asset(); b = self.asset(b'two')
        first = projects.create(self.e, 'First video', 'first')
        second = projects.create(self.e, 'Second video', 'second')
        before = self.e.asset_path(a['id']).read_bytes()
        projects.attach(self.e, first['id'], a['id'], 'storyboard', 0)
        self.assertEqual(projects.create(self.e, 'First video', 'first'), first)
        with self.assertRaises(ValueError): projects.create(self.e, 'Other name', 'first')
        with self.assertRaises(ValueError): projects.attach(self.e, second['id'], a['id'], 'clip')
        result = projects.collect(self.e)
        by_id = {p['id']:p for p in result['projects']}
        self.assertEqual(by_id[first['id']]['image_count'], 1)
        self.assertEqual(by_id[second['id']]['assets'], [])
        self.assertEqual([v['id'] for v in result['unassigned']], [b['id']])
        self.assertEqual(self.e.asset_path(a['id']).read_bytes(), before)
        projects.collect(self.e)
        self.assertEqual(len(self.s.all('project-asset')), 1)

    def test_native_import_can_attach_to_a_named_scene(self):
        p=projects.create(self.e,'Native image scene','native')
        a=self.e.asset_import(base64.b64encode(b'\x89PNG\r\n\x1a\nnative').decode(),'image/png',p['id'],'storyboard',1)
        media=projects.collect(self.e)['projects'][0]['assets'][0]
        self.assertEqual((media['id'],media['category'],media['scene']),(a['id'],'storyboard',1))

    def test_concurrent_host_reports_reuse_one_run(self):
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=4) as pool:
            runs=list(pool.map(lambda _:activity.report(self.e,'writer','One task','stable'),range(4)))
        self.assertEqual(len({r['id'] for r in runs}),1)
        self.assertEqual(activity.snapshot(self.e)['running'],1)

    def test_only_proven_job_relationships_are_grouped(self):
        a = self.asset(); p = projects.create(self.e, 'Real project', 'project')
        self.s.put('image-job', 'j', {'id':'j','status':'completed','project_id':p['id'],'asset_ids':[a['id']], 'created_at':time.time(), 'worker':{'token':'private'}})
        result = projects.collect(self.e)['projects'][0]
        self.assertEqual(result['status'], 'media_ready')
        self.assertEqual(result['assets'][0]['id'], a['id'])
        self.assertNotIn('worker', result['jobs'][0])

    def test_existing_project_keeps_script_and_plan_jobs_together(self):
        project=projects.create(self.e,'One complete production','whole')
        channel=self.e.channel_save('Test channel','Test audience')
        concepts=[{'title':name,'hook':'An opening','script':'A script','scenes':[{'image_prompt':'A scene','video_prompt':'A move'}]} for name in ['First concept','Second concept']]
        plan=self.e.plan_save(channel['id'],concepts,'one-plan',project['id'])
        a=self.asset()
        self.s.put('job','scene-job',{'id':'scene-job','plan_id':plan['id'],'scene':0,'status':'completed','asset_id':a['id'],'created_at':time.time()})
        # Use a video-shaped record to model the real plan worker output.
        self.s.put('asset',a['id'],{**a,'media_type':'video/mp4'})
        result=projects.collect(self.e)['projects']
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]['name'],'One complete production')
        self.assertEqual(result[0]['plan']['id'],plan['id'])
        self.assertEqual(result[0]['assets'][0]['category'],'clip')
        with self.assertRaises(ValueError):self.e.plan_save(channel['id'],concepts,'another-plan',project['id'])

    def test_unknown_balances_excluded_and_reconnected_identities_deduped(self):
        for key, credits in [('known',50),('zero',0),('unknown',None),('invalid',-1)]:
            self.s.put('account',key,{'id':key,'provider':'flow','status':'login_required','credits':credits})
        for key in ['first','reconnected']:
            self.s.put('account',key,{'id':key,'provider':'youtube','remote_id':'same-channel','status':'connected'})
        with patch('vso.flow_service.inspect') as inspect:
            result = control.snapshot(self.e)
            control.refresh_accounts(self.e)
            inspect.assert_not_called()
        self.assertEqual(result['credits']['total_observed'],50)
        self.assertEqual(result['credits']['unknown_accounts'],2)
        self.assertEqual(len(result['connected_identities']),1)

    def test_dates_distinguish_editorial_from_approved_uploads(self):
        when=datetime.fromtimestamp(time.time()+86400,timezone.utc).isoformat()
        projects.create(self.e,'Tomorrow idea','tomorrow',planned_for=when)
        self.s.put('publication','scheduled',{'id':'scheduled','account_id':'a','provider':'youtube','status':'scheduled','scheduled_at':time.time()+86400,'title':'Approved upload'})
        self.s.put('publication','review',{'id':'review','provider':'youtube','status':'review','options':{'schedule_at':when}})
        self.s.put('content-request','week',{'id':'week','items':[{'date':'2030-01-01','angle':'Editorial idea'}]})
        rows=control.schedules(self.e, projects.collect(self.e))
        self.assertEqual(sorted(r['kind'] for r in rows),['editorial','planned','release','scheduled'])
        with self.assertRaises(ValueError): projects.create(self.e,'No zone','bad',planned_for='2030-01-01T10:00')

    def test_tool_run_is_visible_while_work_is_happening(self):
        entered=threading.Event();release=threading.Event()
        def work():entered.set();release.wait(3);return {'ok':True}
        with patch('vso.tools.registry',return_value={'caption_review':work}):
            thread=threading.Thread(target=lambda:tools.call(self.e,'caption_review',{}))
            thread.start()
            try:
                self.assertTrue(entered.wait(2))
                observed=activity.snapshot(self.e)
                self.assertEqual(observed['running'],1)
                self.assertEqual(next(r for r in observed['roles'] if r['id']=='caption')['status'],'running')
            finally:release.set();thread.join(3)
        self.assertEqual(activity.snapshot(self.e)['running'],0)
        self.assertEqual(activity.snapshot(self.e)['runs'][0]['status'],'completed')

    def test_idle_host_and_restart_are_honest(self):
        run=activity.report(self.e,'strategist','Fixture task','one')
        with self.assertRaises(ValueError):activity.report(self.e,'writer','Fixture task','one')
        with patch('vso.activity.time.time',return_value=run['expires_at']+1):
            self.assertEqual(activity.snapshot(self.e)['runs'][0]['status'],'unconfirmed')
            self.assertEqual(activity.snapshot(self.e)['running'],0)
        recovery.startup(self.e)
        self.assertEqual(activity.snapshot(self.e)['runs'][0]['status'],'interrupted')
        self.assertIsNone(activity.role_for('control_snapshot'))

    def test_resources_start_with_observations_and_no_seeded_history(self):
        first=control.resources(self.e);second=control.resources(self.e)
        self.assertIsNone(first['cpu_percent'])
        self.assertEqual(len(second['history']),1)
        self.assertGreater(second['disk_total'],0)
        self.assertGreaterEqual(second['memory_percent'],0)
        self.assertLessEqual(second['memory_percent'],100)

    def test_control_scope_is_read_and_mutations_are_write(self):
        from vso.auth import tool_scope
        self.assertEqual(tool_scope('control_snapshot'),'social:read')
        self.assertEqual(tool_scope('project_list'),'social:read')
        self.assertEqual(tool_scope('project_create'),'social:write')
        self.assertEqual(tool_scope('activity_report'),'social:write')

if __name__=='__main__':unittest.main()
