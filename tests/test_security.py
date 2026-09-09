"""Security regressions: synthetic credentials and local/mock transports only."""
import io
from email.message import Message
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import tempfile
import unittest
import urllib.error
import urllib.request
from urllib.response import addinfourl
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
cu = runpy.run_path(str(ROOT / 'bin/claude-usage'), run_name='security_tests')
g = cu['fetch_usage'].__globals__


class SecurityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        patch = mock.patch.dict(g, CACHE_DIR=self.tmp.name,
                                CACHE_FILE=str(Path(self.tmp.name) / 'cache.json'),
                                CONFIG_FILE=str(Path(self.tmp.name) / 'config.json'))
        patch.start()
        self.addCleanup(patch.stop)

    def test_authenticated_redirects_never_reach_second_host(self):
        """Exercise redirect rejection and a fully offline permissive control."""
        original = urllib.request.build_opener
        redirect = cu['NoRedirect'].redirect_request
        for status in (301, 302, 303, 307, 308):
            for target in ('https://other.invalid/collect', 'http://other.invalid/collect', cu['API_URL'] + '?next'):
                supported = hasattr(urllib.request.HTTPRedirectHandler, 'http_error_%d' % status)
                for protected in (True, False):
                    requests = []

                    class Transport(urllib.request.HTTPHandler, urllib.request.HTTPSHandler):
                        def http_open(self, req):
                            requests.append(req)
                            headers = Message()
                            if len(requests) == 1:
                                headers['Location'] = target
                                response = addinfourl(io.BytesIO(b''), headers, req.full_url, status)
                            else:
                                response = addinfourl(io.BytesIO(b'{"limits": []}'), headers, req.full_url, 200)
                            response.msg = 'synthetic response'
                            return response

                        https_open = http_open

                    def opener(handler):
                        if not protected:
                            handler = urllib.request.HTTPRedirectHandler()
                        return original(handler, Transport(), urllib.request.ProxyHandler({}))

                    with self.subTest(status=status, target=target, protected=protected), \
                            mock.patch.object(urllib.request, 'build_opener', side_effect=opener), \
                            mock.patch.object(cu['NoRedirect'], 'redirect_request',
                                              autospec=True, side_effect=redirect) as guard:
                        if protected or not supported:
                            with self.assertRaises(cu['UsageError']) as caught:
                                cu['fetch_usage']('SYNTHETIC', '0.0.0')
                            self.assertEqual(caught.exception.kind, 'http')
                            if supported:
                                guard.assert_called_once()
                            else:
                                # Python 3.9 rejects 308 in the default error
                                # handler before any redirect hook is reached.
                                guard.assert_not_called()
                            self.assertEqual(len(requests), 1)
                        else:
                            # This control must follow the redirect using only
                            # fake HTTP/HTTPS transports, proving the fixture
                            # would catch removal of the production guard.
                            self.assertEqual(cu['fetch_usage']('SYNTHETIC', '0.0.0'), {'limits': []})
                            guard.assert_not_called()
                            self.assertEqual(len(requests), 2)
                            self.assertEqual(requests[1].full_url, target)
                            self.assertEqual(requests[1].get_header('Authorization'), 'Bearer SYNTHETIC')
                        self.assertEqual(requests[0].full_url, cu['API_URL'])

    def test_errors_do_not_reflect_credentials(self):
        marker = 'SYNTHETIC_CREDENTIAL'
        errors = [urllib.error.HTTPError(cu['API_URL'], 401, marker, {}, io.BytesIO(marker.encode())),
                  urllib.error.URLError(marker)]
        for error in errors:
            with mock.patch.dict(os.environ, {'CLAUDE_USAGE_DEBUG': '1'}), \
                    mock.patch.dict(g, _open_url=mock.Mock(side_effect=error)), \
                    mock.patch('sys.stderr', new_callable=io.StringIO) as stderr:
                with self.assertRaises(cu['UsageError']) as caught:
                    cu['fetch_usage'](marker, '0.0.0')
                self.assertNotIn(marker, stderr.getvalue() + str(caught.exception))

    def test_cache_migrates_and_json_drops_unexpected_fields(self):
        raw = {'limits': [{'kind': 'session', 'percent': 42, 'account_id': 'PRIVATE'}],
               'account_email': 'PRIVATE', 'access_token': 'PRIVATE'}
        path = Path(g['CACHE_FILE'])
        path.write_text(json.dumps({'data': raw, 'fetched_at': 1}))
        cache = cu['load_cache']()
        self.assertNotIn('PRIVATE', path.read_text())
        self.assertEqual(cache['data']['limits'][0]['percent'], 42)
        self.assertNotIn('PRIVATE', cu['fmt_json']([], raw, 1, False, None))
        cu['save_cache']({'data': raw})
        self.assertNotIn('PRIVATE', path.read_text())
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_output_removes_terminal_controls_and_tmux_markup(self):
        raw = {'limits': [{'kind': 'weekly_scoped', 'percent': 42,
                          'scope': {'model': {'display_name': '\x1b]52;c;TEST\x07\x9c#{pane_title}'}}}]}
        buckets = cu['normalize'](raw)
        for formatter in ('fmt_text', 'fmt_tmux'):
            text = cu[formatter](buckets, False, False)
            for control in ('\x1b', '\x07', '\x9c'):
                self.assertNotIn(control, text)
        self.assertIn('##{pane', cu['fmt_tmux'](buckets, False, False))

    def test_ntfy_blocks_enterprise_unknown_missing_and_env_only_plans(self):
        for plan in ('enterprise', ' ENTERPRISE ', None, '', 'new-plan'):
            with self.subTest(plan=plan), mock.patch.dict(g,
                    load_credentials=lambda: ('SYNTHETIC', {'subscriptionType': plan}, 'mock'),
                    _open_url=mock.Mock()) as _:
                self.assertFalse(cu['send_ntfy']('title', 'body', 'topic'))
                g['_open_url'].assert_not_called()
        with mock.patch.dict(os.environ, {'CLAUDE_USAGE_TOKEN': 'SYNTHETIC'}, clear=True), \
                mock.patch.dict(g, _open_url=mock.Mock()):
            self.assertFalse(cu['send_ntfy']('title', 'body', 'topic'))
            g['_open_url'].assert_not_called()

    def test_enterprise_fetch_cannot_publish_after_personal_account_switch(self):
        Path(g['CONFIG_FILE']).write_text(json.dumps({'notify': {'channels': ['ntfy'], 'ntfy_topic': 'topic'}}))
        credentials = mock.Mock(side_effect=[('SYNTHETIC_ENTERPRISE', {'subscriptionType': 'enterprise'}, 'mock'),
                                             ('SYNTHETIC_PERSONAL', {'subscriptionType': 'pro'}, 'mock')])
        with mock.patch.dict(os.environ, {}, clear=True), mock.patch.dict(g,
                load_credentials=credentials, claude_cli_version=lambda _: '0.0.0',
                fetch_usage=lambda *_: {'limits': [{'kind': 'session', 'percent': 90}]},
                _open_url=mock.Mock()):
            cu['get_usage'](0, force=True)
            g['_open_url'].assert_not_called()

    def test_large_and_nonfinite_percentages_cannot_crash_cache_filter(self):
        raw = {'limits': [{'kind': 'session', 'percent': 10**400},
                          {'kind': 'other', 'percent': float('inf')}],
               'seven_day': {'utilization': 10**400}}
        safe = cu['quota_data'](raw)
        self.assertEqual(safe['limits'][0]['percent'], 100)
        self.assertEqual(len(safe['limits']), 1)
        self.assertEqual(safe['seven_day']['utilization'], 100)
        self.assertEqual(len(cu['normalize'](safe)), 1)

    def test_enterprise_notify_test_cannot_override_policy(self):
        Path(g['CONFIG_FILE']).write_text(json.dumps({'notify': {'channels': ['ntfy'], 'ntfy_topic': 'topic'}}))
        with mock.patch.dict(os.environ, {'CLAUDE_USAGE_NOTIFY': 'ntfy'}, clear=True), \
                mock.patch.dict(g, load_credentials=lambda: ('SYNTHETIC', {'subscriptionType': 'enterprise'}, 'mock'),
                                _open_url=mock.Mock()), \
                mock.patch('sys.stdout', new_callable=io.StringIO) as out:
            self.assertEqual(cu['run_notify_test']('ntfy'), 1)
            g['_open_url'].assert_not_called()
            self.assertIn('enterprise', out.getvalue())

    def test_enterprise_keeps_local_channels(self):
        settings = cu['notify_settings']({'notify': {'channels': ['ntfy', 'desktop'], 'ntfy_topic': 'topic'}}, {})
        with mock.patch.dict(g, load_credentials=lambda: ('SYNTHETIC', {'subscriptionType': 'enterprise'}, 'mock'),
                             _open_url=mock.Mock(), send_desktop=mock.Mock(return_value=True)):
            self.assertEqual(cu['send_notification'](settings, 'title', 'body'), {'ntfy': False, 'desktop': True})
            g['_open_url'].assert_not_called()

    def test_ntfy_uses_current_plan_and_requires_https(self):
        response = mock.MagicMock()
        response.__enter__.return_value.status = 200
        credentials = mock.Mock(side_effect=[('SYNTHETIC', {'subscriptionType': 'pro'}, 'mock'),
                                             ('SYNTHETIC', {'subscriptionType': 'enterprise'}, 'mock')])
        opened = mock.Mock(return_value=response)
        with mock.patch.dict(g, load_credentials=credentials, _open_url=opened):
            self.assertTrue(cu['send_ntfy']('title', 'body', 'topic'))
            self.assertFalse(cu['send_ntfy']('title', 'body', 'topic'))
            self.assertEqual(opened.call_count, 1)
            self.assertIsNone(opened.call_args.args[0].get_header('Authorization'))
        for server in ('http://ntfy.invalid', 'file:///tmp/test', 'https://user:pass@ntfy.invalid'):
            with mock.patch.dict(g, load_credentials=lambda: ('SYNTHETIC', {'subscriptionType': 'pro'}, 'mock'),
                                 _open_url=mock.Mock()):
                self.assertFalse(cu['send_ntfy']('title', 'body', 'topic', server))
                g['_open_url'].assert_not_called()


class TmuxPathTests(unittest.TestCase):
    def test_checkout_path_cannot_execute_shell_syntax(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            # Includes shell substitutions, quotes, tmux delimiters and Unicode.
            repo = base / 'repo`touch PWNED`$(touch PWNED2)\'"#(x) café'
            (repo / 'bin').mkdir(parents=True)
            shutil.copy(ROOT / 'claude-usage.tmux', repo / 'claude-usage.tmux')
            cli = repo / 'bin' / 'claude-usage'
            cli.write_text('#!/bin/sh\nprintf "SAFE:%s" "$1"\n')
            cli.chmod(0o700)
            mocks = base / 'mocks'
            mocks.mkdir()
            tmux = mocks / 'tmux'
            tmux.write_text('#!/bin/sh\nif [ "$1" = show-option ]; then printf "#{claude_usage}"; else printf "%s" "$4" > "$CAPTURE"; fi\n')
            tmux.chmod(0o700)
            env = dict(os.environ, HOME=tmp, XDG_CACHE_HOME=tmp, XDG_CONFIG_HOME=tmp,
                       PATH=str(mocks) + os.pathsep + os.environ['PATH'], CAPTURE=str(base / 'job'))
            subprocess.run(['bash', str(repo / 'claude-usage.tmux')], env=env, cwd=tmp, check=True)
            job = (base / 'job').read_text()
            self.assertTrue(job.startswith('#(') and job.endswith(')'))
            result = subprocess.run(['/bin/sh', '-c', job[2:-1]], env=env, cwd=tmp,
                                    capture_output=True, text=True, check=True)
            self.assertEqual(result.stdout, 'SAFE:--format')
            self.assertFalse((base / 'PWNED').exists())
            self.assertFalse((base / 'PWNED2').exists())


class WorkflowTests(unittest.TestCase):
    def test_merge_only_after_required_checks_succeed(self):
        text = (ROOT / '.github/workflows/dependabot-auto-merge.yml').read_text()
        step = text.split('      - name: Merge (patch + minor)', 1)[1]
        body = step.split('        run: |\n', 1)[1].split('        env:', 1)[0]
        script = '\n'.join(line[10:] for line in body.splitlines())
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            gh = path / 'gh'
            gh.write_text('#!/bin/sh\nif [ "$2" = checks ]; then exit "$CHECK_EXIT"; fi\nprintf merged > "$MERGED"\n')
            gh.chmod(0o700)
            for code in ('0', '1', '8', '124'):
                marker = path / ('merged-' + code)
                env = dict(os.environ, PATH=tmp + os.pathsep + os.environ['PATH'],
                           CHECK_EXIT=code, MERGED=str(marker), PR_URL='https://example.invalid/pr/1', HEAD_SHA='abc')
                result = subprocess.run(['bash', '-c', script], env=env, capture_output=True)
                self.assertEqual(marker.exists(), code == '0')
                self.assertEqual(result.returncode == 0, code == '0')


if __name__ == '__main__':
    unittest.main()
