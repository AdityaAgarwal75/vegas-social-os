"""No-live-provider tests for exclusive Flow tab policy."""
import unittest
from vso.flow_browser_guard import allowed_targets, classify


def tab(ident, url, kind='page'):
    return {'id': ident * 32, 'url': url, 'type': kind}


class FlowBrowserTabTests(unittest.TestCase):
    def test_only_flow_page_survives(self):
        pages = [tab('a', 'https://flow.google.com/'), tab('b', 'https://chatgpt.com/auth/login'),
                 tab('c', 'chrome://newtab/'), tab('d', 'https://getadblock.com/en/installed/')]
        self.assertEqual(set(allowed_targets(pages)), {'b' * 32, 'c' * 32, 'd' * 32})

    def test_keep_existing_project_preferentially(self):
        pages = [tab('a', 'https://flow.google.com/'),
                 tab('b', 'https://flow.google.com/project/123'), tab('c', 'https://flow.google.com/about')]
        self.assertEqual(set(allowed_targets(pages)), {'a' * 32, 'c' * 32})

    def test_google_auth_is_not_interrupted(self):
        pages = [tab('a', 'https://accounts.google.com/v3/signin/challenge'),
                 tab('b', 'https://flow.google.com/'),
                 tab('c', 'https://getadblock.com')]
        self.assertEqual(allowed_targets(pages), ['c' * 32])

    def test_no_flow_page_preserves_one_tab(self):
        pages = [tab('a', 'about:blank'), tab('b', 'chrome://newtab')]
        self.assertEqual(allowed_targets(pages), ['b' * 32])

    def test_unsafe_target_and_host_refused(self):
        pages = [tab('a', 'https://evilflow.google.com/'), tab('b', 'http://flow.google.com/'),
                 tab('c', 'https://flow.google.com/'), {'id': '../../secret', 'url': 'https://chatgpt.com', 'type': 'page'}]
        self.assertEqual(classify('https://evilflow.google.com/'), 'other')
        self.assertEqual(allowed_targets(pages), ['a' * 32, 'b' * 32])


if __name__ == '__main__':
    unittest.main()
