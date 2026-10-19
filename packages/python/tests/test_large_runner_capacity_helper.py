# SPDX-License-Identifier: MIT OR Apache-2.0
"""Safety controls for the large stress runner's narrowly scoped cleanup."""

import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
HELPER_PATH = ROOT / 'scripts' / 'prepare-large-stress-runner.py'
SPEC = importlib.util.spec_from_file_location('prepare_large_stress_runner', HELPER_PATH)
helper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helper)


class LargeRunnerCapacityHelperTests(unittest.TestCase):
    def test_refuses_local_or_self_hosted_before_cleanup(self):
        with mock.patch.dict(os.environ, {'GITHUB_ACTIONS': 'true', 'RUNNER_ENVIRONMENT': 'self-hosted'}):
            with mock.patch.object(helper, 'reclaim_linux') as reclaim:
                with self.assertRaisesRegex(RuntimeError, 'GitHub-hosted'):
                    helper.require_github_hosted_runner()
                reclaim.assert_not_called()

        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch.object(helper, 'reclaim_linux') as reclaim:
                with self.assertRaisesRegex(RuntimeError, 'GitHub Actions'):
                    helper.require_github_hosted_runner()
                reclaim.assert_not_called()

    def test_linux_allowlist_uses_sudo_and_leaves_python_toolcache_out(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sdk_paths = (root / 'android', root / 'dotnet', root / 'ghc')
            for sdk in sdk_paths:
                sdk.mkdir()
            protected = root / 'hostedtoolcache' / 'Python'
            protected.mkdir(parents=True)
            selected_python = root / 'selected-python'
            selected_python.mkdir()
            calls = []

            def record(command, **kwargs):
                calls.append(command)

            with mock.patch.object(helper, 'LINUX_UNUSED_SDKS', sdk_paths):
                outcomes = helper.reclaim_linux(command=record)

            self.assertEqual(len(outcomes), 3)
            self.assertEqual(calls, [[
                'sudo', 'rm', '-rf', '--', str(sdk)
            ] for sdk in sdk_paths])
            self.assertTrue(protected.is_dir())
            self.assertTrue(selected_python.is_dir())
            self.assertEqual(helper.LINUX_UNUSED_SDKS, (
                Path('/usr/local/lib/android'), Path('/usr/share/dotnet'), Path('/opt/ghc')
            ))
            self.assertTrue(all(path != protected for path in helper.LINUX_UNUSED_SDKS))

    def test_exact_path_guard_rejects_outside_parent_without_command(self):
        command = mock.Mock()
        with self.assertRaisesRegex(RuntimeError, 'unexpected SDK path'):
            helper.remove_exact_sdk(Path('/usr/bin/python3'), Path('/usr/bin/unused'), command)
        command.assert_not_called()

    def test_macos_switches_to_clt_then_skips_symlink_and_sudos_real_bundles(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            applications = root / 'Applications'
            applications.mkdir()
            command_line_tools = root / 'CommandLineTools'
            command_line_tools.mkdir()
            real_xcode = applications / 'Xcode_16.app'
            real_xcode.mkdir()
            symlink_xcode = applications / 'Xcode.app'
            symlink_xcode.symlink_to(real_xcode, target_is_directory=True)
            calls = []

            def record(command, **kwargs):
                calls.append(command)
                if command[-1] == '--print-path':
                    return mock.Mock(stdout=str(command_line_tools))
                return mock.Mock(stdout='')

            outcomes = helper.reclaim_macos(
                command=record,
                applications=applications,
                command_line_tools=command_line_tools,
            )

            self.assertEqual(calls[0], [
                'sudo', '/usr/bin/xcode-select', '--switch', str(command_line_tools)
            ])
            self.assertEqual(calls[1], ['/usr/bin/xcode-select', '--print-path'])
            self.assertEqual(calls[2], ['sudo', 'rm', '-rf', '--', str(real_xcode)])
            self.assertIn(f'skipped symlink: {symlink_xcode}', outcomes)
            self.assertTrue(real_xcode.is_dir())  # mock proves no real deletion was attempted
            self.assertTrue(symlink_xcode.is_symlink())
            self.assertIn(f'selected: {command_line_tools.resolve()}', outcomes)

    def test_insufficient_df_space_writes_explicit_capacity_refusal(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root / 'workspace'
            workspace.mkdir()
            runner_temp = root / 'runner-temp'
            runner_temp.mkdir()
            snapshots = iter((
                {'availableBytes': 80 * 1024**3, 'availableGiB': 80.0},
                {'availableBytes': 63 * 1024**3, 'availableGiB': 63.0},
            ))
            with mock.patch.object(helper, 'require_github_hosted_runner', return_value=('Linux', workspace, runner_temp)), \
                 mock.patch.object(helper, 'df_snapshot', side_effect=lambda _path: next(snapshots)), \
                 mock.patch.object(helper, 'reclaim_linux', return_value=['removed: test SDK']), \
                 contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                status = helper.main()

            report = json.loads((runner_temp / 'public-stress' / 'runner-capacity.json').read_text())
            self.assertEqual(status, 2)
            self.assertEqual(report['status'], 'capacity-refusal')
            self.assertEqual(report['after']['availableBytes'], 63 * 1024**3)
            self.assertEqual(report['reason'], 'available filesystem space remains below the 64 GiB large-workload target')


if __name__ == '__main__':
    unittest.main()
