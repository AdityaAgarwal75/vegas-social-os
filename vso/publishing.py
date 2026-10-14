"""Exact, approved releases; network failures never cause a blind second post."""
import json
import time
from datetime import datetime
from urllib.parse import urlencode

from . import net


def prepare(engine, account_id, asset_ids, title, caption, visibility, options, request_id, plan_id=""):
    if not request_id or len(request_id) > 200: raise ValueError('A stable request ID is required')
    a = engine.store.get('account', account_id)
    provider = a['provider']
    if provider not in ('youtube', 'instagram', 'facebook') or a['status'] != 'connected':
        raise ValueError('Choose a connected publishing destination')
    if not isinstance(asset_ids, list) or len(asset_ids) > 10 or any(not isinstance(x, str) for x in asset_ids):
        raise ValueError('Choose up to ten imported assets')
    assets = [engine.store.get('asset', i) for i in asset_ids]
    for i in asset_ids: engine.asset_path(i)
    types = [x['media_type'] for x in assets]
    if not isinstance(options, dict) or set(options) - {'thumbnail_id', 'tags', 'category_id', 'made_for_kids', 'schedule_at', 'link'}:
        raise ValueError('Unsupported release option')
    options = dict(options)
    if visibility not in ('public', 'private', 'unlisted'): raise ValueError('Invalid visibility')
    if not isinstance(title, str) or len(title) > 100 or not isinstance(caption, str): raise ValueError('Invalid copy')
    if len(caption) > (2200 if provider == 'instagram' else 5000 if provider == 'youtube' else 60000): raise ValueError('Caption exceeds platform limit')
    if provider == 'youtube':
        if types != ['video/mp4'] or not title.strip(): raise ValueError('YouTube needs one MP4 and a title')
        if type(options.get('made_for_kids')) is not bool: raise ValueError('Choose the YouTube audience setting explicitly')
        tags = options.get('tags', [])
        if not isinstance(tags, list) or any(not isinstance(x, str) for x in tags) or sum(len(x) + 1 for x in tags) > 500:
            raise ValueError('YouTube tags exceed the limit')
        if not str(options.get('category_id', '22')).isdigit(): raise ValueError('Invalid YouTube category')
    else:
        if visibility != 'public': raise ValueError(provider.title() + ' releases are public; choose public explicitly')
        if provider == 'instagram' and not assets: raise ValueError('Instagram requires media')
        if provider == 'instagram' and any(t not in ('image/jpeg', 'video/mp4') for t in types):
            raise ValueError('Instagram publishing requires JPEG images or MP4 video; import a JPEG export')
        if provider == 'facebook' and any(t not in ('image/jpeg', 'image/png', 'video/mp4') for t in types):
            raise ValueError('Facebook supports JPEG/PNG photos or one MP4 in this composer')
        if 'video/mp4' in types and (provider == 'facebook' and len(types) != 1): raise ValueError('A Facebook video must be its own post')
        if not assets and not caption.strip() and not options.get('link'): raise ValueError('Enter text, a link or media')
    if options.get('link'):
        from urllib.parse import urlsplit
        p = urlsplit(options['link'])
        if provider != 'facebook' or assets or p.scheme != 'https' or not p.hostname or p.username or p.password:
            raise ValueError('Use HTTPS links only for a Facebook text/link post')
    thumbnail = options.get('thumbnail_id')
    if thumbnail:
        thumb = engine.store.get('asset', thumbnail)
        engine.asset_path(thumbnail)
        if provider == 'facebook': raise ValueError('Facebook custom thumbnails are not implemented; leave cover empty')
        if thumb['media_type'] not in ('image/jpeg', 'image/png'): raise ValueError('Cover must be JPEG or PNG')
        if provider == 'instagram' and (types != ['video/mp4'] or thumb['media_type'] != 'image/jpeg'):
            raise ValueError('Instagram cover is a JPEG for a single Reel only')
        if provider == 'youtube' and thumb['size'] > 50 * 1024 * 1024: raise ValueError('YouTube thumbnail exceeds 50 MiB')
    scheduled = options.get('schedule_at')
    if scheduled:
        try:
            dt = datetime.fromisoformat(scheduled.replace('Z', '+00:00'))
            if dt.tzinfo is None or dt.timestamp() <= time.time() + 30: raise ValueError()
        except (ValueError, TypeError): raise ValueError('Schedule must be a future ISO time including timezone') from None
    body = {'kind': 'composer', 'account_id': account_id, 'destination_name': a.get('name', a.get('label')),
            'provider': provider, 'asset_ids': asset_ids, 'title': title, 'caption': caption,
            'visibility': visibility, 'options': options}
    if plan_id:
        plan=engine.store.get('plan',plan_id);channel=engine.store.get('channel',plan['channel_id'])
        if plan['status']!='video_review' or asset_ids!=[plan.get('video')] or account_id not in channel['account_ids'] or plan.get('revision_requested'):raise ValueError('Release must match the reviewed final video and channel destination')
        body['plan_id']=plan_id
    ident = engine.store.digest('post:' + request_id)[:32]
    try:
        old = engine.store.get('publication', ident)
        if any(old[k] != v for k, v in body.items()): raise ValueError('Request ID belongs to another release')
        return old
    except ValueError as e:
        if str(e) != 'publication not found': raise
    body.update(id=ident, status='review', created_at=time.time(), remote_id=None)
    engine.store.put('publication', ident, body)
    return body


def media_url(engine, ident):
    if not engine.base.startswith('https://'): raise ValueError('Meta needs a publicly accessible HTTPS installation')
    ticket = engine.store.ticket('media', {'asset_id': ident}, ttl=86400)
    engine.store.put('media-link', engine.store.digest(ticket), {'asset_id': ident, 'expires': time.time() + 86400})
    return engine.base + '/media?ticket=' + ticket


def save(engine, p):
    engine.store.put('publication', p['id'], p)
    return p


def execute(engine, ident):
    with engine.store.db() as db:
        p = engine._load(db, 'publication', ident)
        if p.get('kind') != 'composer': raise ValueError('Use the production publishing action for this release')
        if p['status'] != 'approved': return p
        # Claim once before touching a provider. Unknown results require reconciliation.
        p['status'] = 'uploading'
        engine.store.write(db, 'publication', ident, p)
    try:
        a = engine.store.get('account', p['account_id'])
        if a['status'] != 'connected': raise ValueError('Destination disconnected')
        token = engine.accounts.token(a['id'])
        if p['provider'] == 'youtube': youtube(engine, p, a, token)
        elif p['provider'] == 'facebook': facebook(engine, p, a, token)
        else: instagram(engine, p, a, token)
    except Exception:
        p['status'] = 'unknown'
        p['error'] = 'Provider rejected or interrupted the request. Check the provider before retrying; no automatic repost.'
    engine.store.log('post.execute', ident)
    return save(engine, p)


def youtube(engine, p, a, token):
    file = engine.asset_path(p['asset_ids'][0])
    options = p['options']
    metadata = {'snippet': {'title': p['title'], 'description': p['caption'], 'tags': options.get('tags', []),
                           'categoryId': str(options.get('category_id', '22'))},
                'status': {'privacyStatus': p['visibility'], 'selfDeclaredMadeForKids': options['made_for_kids']}}
    _, headers = net.request('https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status',
        method='POST', token=token, payload=metadata,
        headers={'X-Upload-Content-Type': 'video/mp4', 'X-Upload-Content-Length': str(file.stat().st_size)})
    url = headers.get('Location') or headers.get('location')
    if not url: raise ValueError('Upload session missing')
    engine.store.secret('upload:' + p['id'], {'url': url})
    with file.open('rb') as source:
        result, _ = net.request(url, method='PUT', token=token, raw=source, headers={'Content-Type':'video/mp4','Content-Length':str(file.stat().st_size)})
    p.update(status='published', remote_id=result['id'], url='https://www.youtube.com/watch?v=' + result['id'])
    save(engine, p)  # A failed cover cannot cause a second video upload.
    thumbnail(engine, p, token)


def thumbnail(engine, p, token):
    ident = p['options'].get('thumbnail_id')
    if not ident: return
    try:
        asset = engine.store.get('asset', ident)
        net.request('https://www.googleapis.com/upload/youtube/v3/thumbnails/set?' + urlencode({'videoId': p['remote_id'], 'uploadType': 'media'}),
                    method='POST', token=token, raw=engine.asset_path(ident).read_bytes(), headers={'Content-Type': asset['media_type']})
        p.update(thumbnail_status='applied', status='published')
        p.pop('warning', None)
    except Exception:
        p.update(thumbnail_status='failed', status='published', warning='Video uploaded; custom thumbnail failed. Check channel eligibility and retry the cover only.')


def retry_thumbnail(engine, publication_id):
    p = engine.store.get('publication', publication_id)
    if p.get('kind') != 'composer' or p['provider'] != 'youtube' or p['status'] != 'published' or not p.get('remote_id'):
        raise ValueError('Choose an already published YouTube release')
    thumbnail(engine, p, engine.accounts.token(p['account_id']))
    return save(engine, p)


def facebook(engine, p, a, token):
    root = 'https://graph.facebook.com/' + engine.accounts.config.version('facebook') + '/' + a['remote_id']
    assets = [engine.store.get('asset', i) for i in p['asset_ids']]
    if assets and assets[0]['media_type'] == 'video/mp4':
        result, _ = net.request(root + '/videos', method='POST', token=token,
            form={'file_url': media_url(engine, assets[0]['id']), 'title': p['title'], 'description': p['caption']})
        p.update(status='provider_processing', remote_id=result['id'])
    elif assets:
        children = []
        for asset in assets:
            result, _ = net.request(root + '/photos', method='POST', token=token,
                form={'url': media_url(engine, asset['id']), 'published': 'false'})
            children.append(result['id'])
            p['child_ids'] = children[:]
            save(engine, p)
        result, _ = net.request(root + '/feed', method='POST', token=token,
            form={'message': p['caption'], 'attached_media': json.dumps([{'media_fbid': i} for i in children])})
        p.update(status='published', remote_id=result['id'])
    else:
        form = {'message': p['caption']}
        if p['options'].get('link'): form['link'] = p['options']['link']
        result, _ = net.request(root + '/feed', method='POST', token=token, form=form)
        p.update(status='published', remote_id=result['id'])
    p['url'] = 'https://www.facebook.com/' + p['remote_id']


def instagram(engine, p, a, token):
    root = 'https://graph.instagram.com/' + engine.accounts.config.version('instagram') + '/' + a['remote_id']
    assets = [engine.store.get('asset', i) for i in p['asset_ids']]
    if len(assets) > 1:
        children = []
        for asset in assets:
            form = {'is_carousel_item': 'true'}
            if asset['media_type'] == 'video/mp4': form.update(media_type='VIDEO', video_url=media_url(engine, asset['id']))
            else: form['image_url'] = media_url(engine, asset['id'])
            result, _ = net.request(root + '/media', method='POST', token=token, form=form)
            children.append(result['id'])
            p['child_ids'] = children[:]
            save(engine, p)
        p.update(status='children_processing')
    else:
        form = {'caption': p['caption']}
        if assets[0]['media_type'] == 'video/mp4':
            form.update(media_type='REELS', video_url=media_url(engine, assets[0]['id']))
            if p['options'].get('thumbnail_id'): form['cover_url'] = media_url(engine, p['options']['thumbnail_id'])
        else: form['image_url'] = media_url(engine, assets[0]['id'])
        result, _ = net.request(root + '/media', method='POST', token=token, form=form)
        p.update(status='processing', container_id=result['id'])


def poll(engine, ident):
    # Serialize the complete poll/write sequence; no simultaneous poll can create two parents/posts.
    with engine.store.db() as db:
        p = engine._load(db, 'publication', ident)
        if p['provider'] == 'facebook' and p['status'] == 'provider_processing':
            pass
        elif p['provider'] != 'instagram' or p['status'] not in ('children_processing', 'processing'):
            return p
        original = p['status']
        p['status'] = 'polling'
        engine.store.write(db, 'publication', ident, p)
    try:
        a = engine.store.get('account', p['account_id'])
        token = engine.accounts.token(p['account_id'])
        provider = p['provider']
        root = ('https://graph.facebook.com/' if provider == 'facebook' else 'https://graph.instagram.com/') + engine.accounts.config.version(provider)
        if provider == 'facebook':
            info, _ = net.request(root + '/' + p['remote_id'] + '?fields=status', token=token)
            p['provider_status'] = info.get('status')
            if info.get('status', {}).get('video_status') == 'ready': p['status'] = 'published'
            else: p['status'] = original
            return save(engine, p)
        if original == 'children_processing':
            statuses = [net.request(root + '/' + i + '?fields=status_code', token=token)[0].get('status_code') for i in p['child_ids']]
            if any(x in ('ERROR', 'EXPIRED') for x in statuses):
                p.update(status='failed', error='A carousel item failed or expired; review provider media before preparing another release')
            elif all(x == 'FINISHED' for x in statuses):
                result, _ = net.request(root + '/' + a['remote_id'] + '/media', method='POST', token=token,
                    form={'media_type': 'CAROUSEL', 'children': ','.join(p['child_ids']), 'caption': p['caption']})
                p.update(container_id=result['id'], status='processing')
            else: p['status'] = original
        else:
            info, _ = net.request(root + '/' + p['container_id'] + '?fields=status_code', token=token)
            p['provider_status'] = info.get('status_code')
            if info.get('status_code') == 'FINISHED':
                result, _ = net.request(root + '/' + a['remote_id'] + '/media_publish', method='POST', token=token, form={'creation_id': p['container_id']})
                p.update(status='published', remote_id=result['id'])
            elif info.get('status_code') in ('ERROR', 'EXPIRED'): p.update(status='failed', error='Container failed or expired')
            else: p['status'] = original
    except Exception:
        p.update(status='unknown', error='Processing outcome interrupted; reconcile at provider before another write')
    return save(engine, p)


def schedule(engine, publication_id, schedule_at):
    try:
        dt = datetime.fromisoformat(schedule_at.replace('Z', '+00:00'))
        if not dt.tzinfo or dt.timestamp() <= time.time() + 30: raise ValueError()
    except (ValueError, TypeError): raise ValueError('Choose a future time with timezone') from None
    with engine.store.db() as db:
        p = engine._load(db, 'publication', publication_id)
        if p.get('kind') != 'composer' or p['status'] != 'approved': raise ValueError('Approve the exact release before scheduling')
        if p['options'].get('schedule_at') != schedule_at: raise ValueError('Scheduled time differs from the reviewed release; prepare a new review')
        p.update(status='scheduled', scheduled_at=dt.timestamp())
        engine.store.write(db, 'publication', publication_id, p)
    engine.store.log('post.schedule', publication_id)
    return p


def cancel(engine, publication_id):
    with engine.store.db() as db:
        p = engine._load(db, 'publication', publication_id)
        if p['status'] not in ('review', 'approved', 'scheduled'): raise ValueError('Provider operation already started; cancellation cannot delete a live post')
        p['status'] = 'cancelled'
        engine.store.write(db, 'publication', publication_id, p)
    return p


def reconcile(engine, publication_id):
    p = engine.store.get('publication', publication_id)
    if p.get('kind') != 'composer' or p['provider'] != 'youtube' or p['status'] not in ('unknown', 'resumable'):
        raise ValueError('This release requires manual provider reconciliation; no automatic repost')
    url = engine.store.secret('upload:' + p['id'])['url']
    size = engine.asset_path(p['asset_ids'][0]).stat().st_size
    result, headers = net.request(url, method='PUT', token=engine.accounts.token(p['account_id']), raw=b'',
        headers={'Content-Length': '0', 'Content-Range': 'bytes */' + str(size)}, allow_statuses=(308,))
    if headers.get(':status') == '308':
        import re
        progress = headers.get('Range') or headers.get('range') or ''
        match = re.fullmatch(r'bytes=0-(\d+)', progress)
        offset = int(match[1]) + 1 if match else 0
        if not 0 <= offset < size: raise ValueError('Upload offset invalid; inspect provider')
        p.update(status='resumable', uploaded_bytes=offset)
    elif result.get('id'):
        p.update(status='published', remote_id=result['id'], url='https://www.youtube.com/watch?v=' + result['id'])
    else: raise ValueError('Provider did not identify this upload; no second upload created')
    p.pop('error', None)
    return save(engine, p)


def resume(engine, publication_id):
    with engine.store.db() as db:
        p = engine._load(db, 'publication', publication_id)
        if p.get('kind') != 'composer' or p['provider'] != 'youtube' or p['status'] != 'resumable':
            raise ValueError('Inspect the original upload session before resuming')
        p['status'] = 'uploading'
        engine.store.write(db, 'publication', publication_id, p)
    try:
        url = engine.store.secret('upload:' + p['id'])['url']
        file = engine.asset_path(p['asset_ids'][0]); size = file.stat().st_size
        offset = p['uploaded_bytes']
        token = engine.accounts.token(p['account_id'])
        with file.open('rb') as source:
            source.seek(offset)
            result, _ = net.request(url, method='PUT', token=token, raw=source,
                headers={'Content-Type':'video/mp4','Content-Length':str(size-offset),'Content-Range':f'bytes {offset}-{size-1}/{size}'})
        p.update(status='published', remote_id=result['id'], url='https://www.youtube.com/watch?v=' + result['id'])
        save(engine, p); thumbnail(engine, p, token)
    except Exception:
        p.update(status='unknown', error='Resume interrupted; inspect the same session again, never start a duplicate upload')
    return save(engine, p)
