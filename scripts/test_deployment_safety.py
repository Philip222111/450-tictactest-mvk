"""Regression tests: no network, AWS, real systemd, release publication or deployment."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import MagicMock, patch
import zipfile

import deploy_cloud as cloud
import release_assets as assets
import release_metadata as metadata

spec = importlib.util.spec_from_file_location(
    'runtime_installer', Path(__file__).resolve().parents[1] / 'infrastructure/runtime/deploy_release.py')
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)


class ReleaseMetadataTest(unittest.TestCase):
    def test_only_published_matching_release_allowed(self):
        valid = {'tagName': 'v1.4.0', 'isDraft': False, 'publishedAt': '2026-11-04T12:00:00Z'}
        with patch.object(metadata.subprocess, 'run', return_value=MagicMock(stdout=json.dumps(valid))):
            self.assertEqual(metadata.published_release('v1.4.0'), valid)
        for override in ({'isDraft': True}, {'publishedAt': None}, {'tagName': 'v1.3.0'}):
            with self.subTest(override=override), patch.object(metadata.subprocess, 'run',
                    return_value=MagicMock(stdout=json.dumps({**valid, **override}))):
                with self.assertRaises(ValueError): metadata.published_release('v1.4.0')

    def test_invalid_tag_and_missing_release_fail_closed(self):
        with patch.object(metadata.subprocess, 'run') as run:
            for tag in ('v01.2.3', 'main', 'v1.2', 'v1.2.3;echo injected'):
                with self.assertRaises(ValueError): metadata.published_release(tag)
            run.assert_not_called()
        with patch.object(metadata.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, 'gh')):
            with self.assertRaises(subprocess.CalledProcessError): metadata.published_release('v1.4.0')

    def test_workflow_gates_before_upload_and_has_release_token(self):
        root = Path(__file__).resolve().parents[1]
        workflow = (root / '.github/workflows/deploy.yml').read_text()
        self.assertLess(workflow.index('scripts/release_metadata.py'), workflow.index('gh release download'))
        self.assertIn('GH_TOKEN: ${{ github.token }}', workflow)
        self.assertIn('actions/upload-artifact@v4', workflow)
        bootstrap = (root / 'infrastructure/web.tf').read_text()
        self.assertLess(bootstrap.index('flock -x 9'), bootstrap.index('python3 - bundle'))


class CloudVerificationTest(unittest.TestCase):
    def setUp(self):
        self.manifest = {'changed': {'backend': True, 'frontend': False}}
        self.report = {'tag': 'v1.4.0', 'changed': {'backend': True, 'frontend': False},
                       'versions': {'backend': '1.4.0', 'frontend': '1.3.2'}}
        self.baseline = {'frontend': '1.3.2'}

    def test_selective_and_manual_and_drift_expected_versions(self):
        expected = cloud.expected_versions('v1.4.0', self.manifest, self.report, self.baseline, False)
        self.assertEqual(expected, self.report['versions'])
        both = {'tag': 'v1.4.0', 'changed': {'backend': True, 'frontend': True},
                'versions': {'backend': '1.4.0', 'frontend': '1.4.0'}}
        for force in (True, False):
            self.assertEqual(cloud.expected_versions('v1.4.0', self.manifest, both, self.baseline, force), both['versions'])

    def test_false_report_cannot_define_expected_version(self):
        for override in ({'versions': {'backend': '0.0.0', 'frontend': '1.3.2'}},
                         {'versions': {'backend': '1.4.0', 'frontend': '0.0.0'}},
                         {'tag': 'v0.0.0'}, {'changed': {'backend': False, 'frontend': False}},
                         {'changed': {'backend': 1, 'frontend': False}}):
            with self.subTest(override=override), self.assertRaises(ValueError):
                cloud.expected_versions('v1.4.0', self.manifest, {**self.report, **override}, self.baseline, False)
        with self.assertRaises(ValueError):
            cloud.expected_versions('v1.4.0', self.manifest, self.report, self.baseline, True)

    def test_documentation_only_preserves_independent_baseline(self):
        manifest = {'changed': {'backend': False, 'frontend': False}}
        baseline = {'backend': '1.3.1', 'frontend': '1.3.2'}
        report = {'tag': 'v1.4.0', 'changed': manifest['changed'], 'versions': baseline}
        self.assertEqual(cloud.expected_versions('v1.4.0', manifest, report, baseline, False), baseline)

    def test_invalid_release_blocks_all_uploads(self):
        with patch.dict(cloud.os.environ, TAG='v1.4.0'), patch.object(cloud, 'published_release', side_effect=ValueError('draft')), patch.object(cloud.subprocess, 'run') as run:
            with self.assertRaises(ValueError): cloud.main()
            run.assert_not_called()

    def test_verified_manifest_checks_identity_and_artifact_hashes(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(cloud, 'published_release'):
            root = Path(folder)
            files = {'tictactest-1.4.0.jar': b'jar', 'tictactest-frontend-1.4.0.zip': b'zip'}
            for name, data in files.items(): (root / name).write_bytes(data)
            manifest = {'tag': 'v1.4.0', 'version': '1.4.0', 'changed': {'backend': True, 'frontend': True},
                        'files': {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}}
            def write_manifest():
                data = json.dumps(manifest).encode()
                (root / 'deployment.json').write_bytes(data)
                (root / 'deployment.json.sha256').write_text(hashlib.sha256(data).hexdigest() + '  deployment.json\n')
            write_manifest()
            self.assertEqual(cloud.verified_manifest('v1.4.0', root), manifest)
            (root / 'tictactest-1.4.0.jar').write_bytes(b'tampered')
            with self.assertRaises(ValueError): cloud.verified_manifest('v1.4.0', root)
            manifest['tag'] = 'v0.0.0'
            write_manifest()
            with self.assertRaises(ValueError): cloud.verified_manifest('v1.4.0', root)

    def test_false_report_and_matching_false_http_fail_end_to_end(self):
        both = {'changed': {'backend': True, 'frontend': True}}
        report = {'tag': 'v1.4.0', 'changed': both['changed'],
                  'versions': {'backend': '0.0.0', 'frontend': '0.0.0'}}
        responses = [{'Command': {'CommandId': 'mock'}},
                     {'Status': 'Success', 'StandardOutputContent': json.dumps(report)}]
        with patch.dict(cloud.os.environ, TAG='v1.4.0', FORCE='true', ARTIFACT_BUCKET='mock', INSTANCE_ID='mock', APP_URL='http://mock.invalid'), patch.object(cloud, 'verified_manifest', return_value=both), patch.object(cloud.subprocess, 'run'), patch.object(cloud, 'aws', side_effect=responses), patch.object(cloud, 'public_version', return_value='0.0.0') as http:
            with self.assertRaisesRegex(ValueError, 'independently expected'):
                cloud.main()
            http.assert_not_called()

    def test_wrong_public_version_exhausts_bounded_retries(self):
        both = {'changed': {'backend': True, 'frontend': True}}
        report = {'tag': 'v1.4.0', 'changed': both['changed'],
                  'versions': {'backend': '1.4.0', 'frontend': '1.4.0'}}
        responses = [{'Command': {'CommandId': 'mock'}},
                     {'Status': 'Success', 'StandardOutputContent': json.dumps(report)}]
        with patch.dict(cloud.os.environ, TAG='v1.4.0', FORCE='true', ARTIFACT_BUCKET='mock', INSTANCE_ID='mock', APP_URL='http://mock.invalid'), patch.object(cloud, 'verified_manifest', return_value=both), patch.object(cloud.subprocess, 'run'), patch.object(cloud, 'aws', side_effect=responses), patch.object(cloud, 'public_version', return_value='0.0.0') as http, patch.object(cloud.time, 'sleep'):
            with self.assertRaisesRegex(RuntimeError, 'public version did not become 1.4.0'):
                cloud.main()
            self.assertEqual(http.call_count, 20)


class PreviousReleaseTest(unittest.TestCase):
    def release(self, tag, date='2026-11-01T00:00:00Z', draft=False):
        return {'tag_name': tag, 'published_at': date, 'draft': draft}

    def run_for(self, pages, ancestry=None):
        def run(args, **kwargs):
            if args[0] == 'gh': return MagicMock(stdout=json.dumps(pages))
            if args[1] == 'merge-base': return MagicMock(returncode=(ancestry or {}).get(args[-2], 0))
            return MagicMock(returncode=0)
        return run

    def test_published_only_pagination_and_publication_order(self):
        pages = [[self.release('v1.0.0'), self.release('v1.3.0', draft=True)],
                 [self.release('devcontainer-v1.0.0'), self.release('v1.2.0', '2026-11-02T00:00:00Z')]]
        with patch.object(assets.subprocess, 'run', side_effect=self.run_for(pages)) as run, patch.object(assets.subprocess, 'check_output', return_value='old\nnew\n'):
            self.assertEqual(assets.previous_release('v1.4.0'), 'v1.2.0')
            self.assertFalse(any('v1.3.0' in call.args[0] for call in run.call_args_list if call.args[0][0] == 'git'))

    def test_first_release_and_unrelated_history(self):
        for pages, ancestry in (([[]], {}), ([[self.release('v1.0.0')]], {'v1.0.0': 1})):
            with patch.object(assets.subprocess, 'run', side_effect=self.run_for(pages, ancestry)), patch.object(assets.subprocess, 'check_output', return_value='old\nnew\n'):
                self.assertIsNone(assets.previous_release('v1.4.0'))

    def test_api_and_git_failures_are_not_first_release(self):
        with patch.object(assets.subprocess, 'run', side_effect=[MagicMock(returncode=0), subprocess.CalledProcessError(1, 'gh')]):
            with self.assertRaises(subprocess.CalledProcessError): assets.previous_release('v1.4.0')
        with patch.object(assets.subprocess, 'run', side_effect=subprocess.CalledProcessError(128, 'git')):
            with self.assertRaises(subprocess.CalledProcessError): assets.previous_release('v1.4.0')
        with patch.object(assets.subprocess, 'run', side_effect=self.run_for([[self.release('v1.0.0')]], {'v1.0.0': 128})):
            with self.assertRaises(RuntimeError): assets.previous_release('v1.4.0')

    def test_rerun_ignores_releases_published_after_current(self):
        pages = [[self.release('v1.0.0'), self.release('v1.4.0', '2026-11-02T00:00:00Z'),
                  self.release('v1.5.0', '2026-11-03T00:00:00Z')]]
        with patch.object(assets.subprocess, 'run', side_effect=self.run_for(pages)), patch.object(assets.subprocess, 'check_output', return_value='old\nnew\n'):
            self.assertEqual(assets.previous_release('v1.4.0'), 'v1.0.0')

    def test_wrapper_changes_are_backend_changes(self):
        for path in ('gradlew', 'gradlew.bat'):
            self.assertEqual(assets.changes([path]), {'backend': True, 'frontend': False})


class RuntimeSafetyTest(unittest.TestCase):
    def setUp(self):
        kill_signal = patch.object(runtime.signal, 'SIGKILL', 9, create=True)
        kill_signal.start()
        self.addCleanup(kill_signal.stop)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.root_patch = patch.object(runtime, 'ROOT', self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)
        (self.root / 'releases').mkdir()

    def make_jar(self):
        jar = self.root / 'test.jar'
        with zipfile.ZipFile(jar, 'w') as archive:
            archive.writestr('META-INF/MANIFEST.MF', 'Implementation-Version: 1.4.0\n')
        return jar

    def test_preflight_uses_service_identity_and_enters_game(self):
        process = MagicMock()
        process.poll.return_value = None
        selector = MagicMock()
        selector.__enter__.return_value = selector
        selector.select.return_value = [(MagicMock(fd=123), None)]
        with patch.object(runtime.subprocess, 'Popen', return_value=process) as popen, patch.object(runtime.selectors, 'DefaultSelector', return_value=selector), patch.object(runtime.os, 'read', side_effect=[b'Gegner (1=Greedy, 2=Perfect):', b'(0-8)']), patch.object(runtime.os, 'killpg', create=True) as killpg:
            runtime.preflight(self.make_jar(), '1.4.0', identity=('tictactest', 'tictactest'))
            self.assertEqual(popen.call_args.args[0][:3], ['java', '-Xmx48m', '-jar'])
            self.assertEqual(popen.call_args.kwargs['user'], 'tictactest')
            self.assertEqual(popen.call_args.kwargs['group'], 'tictactest')
            self.assertEqual(popen.call_args.kwargs['extra_groups'], [])
            process.stdin.write.assert_called_once_with(b'1\n')
            self.assertTrue(popen.call_args.kwargs['start_new_session'])
            killpg.assert_called_once_with(process.pid, runtime.signal.SIGKILL)

    def test_preflight_rejects_exit_before_game(self):
        process = MagicMock()
        process.poll.return_value = None
        selector = MagicMock()
        selector.__enter__.return_value = selector
        selector.select.return_value = [(MagicMock(fd=123), None)]
        with patch.object(runtime.subprocess, 'Popen', return_value=process), patch.object(runtime.selectors, 'DefaultSelector', return_value=selector), patch.object(runtime.os, 'read', return_value=b''), patch.object(runtime.os, 'killpg', create=True) as killpg:
            with self.assertRaises(RuntimeError): runtime.preflight(self.make_jar(), '1.4.0', ('tictactest', 'tictactest'))
            killpg.assert_called_once()

    def test_legacy_jar_needs_no_opponent_selection(self):
        process = MagicMock()
        process.poll.return_value = None
        selector = MagicMock()
        selector.__enter__.return_value = selector
        selector.select.return_value = [(MagicMock(fd=123), None)]
        with patch.object(runtime.subprocess, 'Popen', return_value=process), patch.object(runtime.selectors, 'DefaultSelector', return_value=selector), patch.object(runtime.os, 'read', return_value=b'Where to put the next CROSS? (0-8):'), patch.object(runtime.os, 'killpg', create=True):
            runtime.preflight(self.make_jar(), '1.4.0', ('tictactest', 'tictactest'))
            process.stdin.write.assert_not_called()

    def test_game_prompt_timeout_is_bounded(self):
        process = MagicMock()
        process.poll.return_value = None
        with patch.object(runtime.subprocess, 'Popen', return_value=process), patch.object(runtime.selectors, 'DefaultSelector'), patch.object(runtime.time, 'monotonic', side_effect=[0, 21]), patch.object(runtime.os, 'killpg', create=True) as killpg:
            with self.assertRaisesRegex(RuntimeError, 'within 20 seconds'):
                runtime.preflight(self.make_jar(), '1.4.0', ('tictactest', 'tictactest'))
            killpg.assert_called_once()

    def test_root_or_unspecified_service_identity_rejected(self):
        for value in ('root', '', '0'):
            with patch.object(runtime.subprocess, 'check_output', return_value=value):
                with self.assertRaises(RuntimeError): runtime.service_identity()

    def test_failed_service_user_game_restores_previous_jar_and_metadata(self):
        (self.root / 'app.jar').write_bytes(b'healthy old jar')
        old_metadata = b'{"version":"1.3.0"}\n'
        (self.root / 'backend-version.json').write_bytes(old_metadata)
        state = {'tag': 'v1.3.0', 'backend': '1.3.0', 'frontend': '1.3.0'}
        (self.root / 'deployment-state.json').write_text(json.dumps(state))
        manifest = {'tag': 'v1.4.0', 'version': '1.4.0', 'previous_tag': 'v1.3.0',
                    'changed': {'backend': True, 'frontend': False},
                    'files': {'tictactest-1.4.0.jar': hashlib.sha256(b'new jar').hexdigest()}}
        data = json.dumps(manifest).encode()
        fixtures = {'deployment.json': data, 'deployment.json.sha256': (hashlib.sha256(data).hexdigest() + '  deployment.json').encode(), 'tictactest-1.4.0.jar': b'new jar'}
        calls = []
        def fake_run(args, **kwargs):
            calls.append(args)
            if args[0] == 'aws': Path(args[4]).write_bytes(fixtures[args[3].rsplit('/', 1)[-1]])
            return MagicMock(returncode=0)
        def game_probe(jar, version, identity=None):
            if identity and version == '1.4.0': raise RuntimeError('service-user game failed')
        with patch.object(runtime.subprocess, 'run', side_effect=fake_run), patch.object(runtime, 'service_identity', return_value=('tictactest', 'tictactest')), patch.object(runtime, 'preflight', side_effect=game_probe) as probe, patch.object(runtime, 'urlopen') as http:
            http.return_value.__enter__.return_value.status = 200
            with self.assertRaisesRegex(RuntimeError, 'service-user game failed'):
                runtime.deploy('s3://mock/', 'v1.4.0')
        self.assertEqual((self.root / 'app.jar').read_bytes(), b'healthy old jar')
        self.assertEqual((self.root / 'backend-version.json').read_bytes(), old_metadata)
        self.assertEqual(json.loads((self.root / 'deployment-state.json').read_text()), state)
        self.assertEqual(sum(call == ['systemctl', 'restart', 'tictactest'] for call in calls), 2)
        self.assertEqual(probe.call_args_list[-1].kwargs['identity'], ('tictactest', 'tictactest'))
        self.assertEqual(probe.call_args_list[-1].args[1], '1.3.0')

    def test_same_version_frontend_is_fresh_and_failure_preserves_active_tree(self):
        source = self.root / 'source'
        source.mkdir()
        (source / 'index.html').write_text('first')
        try:
            runtime.activate_frontend(source, '1.4.0')
        except OSError as error:
            if getattr(error, 'winerror', None) == 1314:
                self.skipTest('Windows account cannot create symlinks; run on Linux/CI')
            raise
        old = (self.root / 'frontend').resolve()
        (source / 'index.html').write_text('second')
        runtime.activate_frontend(source, '1.4.0')
        active = (self.root / 'frontend').resolve()
        self.assertNotEqual(old, active)
        self.assertEqual((old / 'index.html').read_text(), 'first')
        self.assertEqual((active / 'index.html').read_text(), 'second')
        with patch.object(runtime.shutil, 'copytree', side_effect=OSError('disk full')):
            with self.assertRaises(OSError): runtime.activate_frontend(source, '1.4.0')
        self.assertEqual((self.root / 'frontend').resolve(), active)
        self.assertEqual((active / 'index.html').read_text(), 'second')

    def test_failed_frontend_switch_removes_only_new_staging_tree(self):
        source = self.root / 'source'
        source.mkdir()
        (source / 'index.html').write_text('new')
        old = self.root / 'releases/frontend-1.4.0-old'
        old.mkdir()
        (old / 'index.html').write_text('healthy')
        active = self.root / 'frontend'
        active.write_text('stand-in for active link')
        with patch.object(Path, 'symlink_to'), patch.object(runtime.os, 'replace', side_effect=OSError('switch failed')):
            with self.assertRaises(OSError): runtime.activate_frontend(source, '1.4.0')
        self.assertEqual(active.read_text(), 'stand-in for active link')
        self.assertEqual((old / 'index.html').read_text(), 'healthy')
        self.assertEqual(list((self.root / 'releases').iterdir()), [old])


if __name__ == '__main__':
    unittest.main()
