# SPDX-License-Identifier: MIT OR Apache-2.0
"""Pure PostgreSQL profile controls for the installer measurement runner."""

import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / 'scripts/measure-installer-submissions.py'
RUNTIME_PROFILE = ROOT / 'packages/python/src/truss/_profiles/local-postgres-runtime.json'
SPEC = importlib.util.spec_from_file_location('measure_installer_submissions', SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MEASURER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MEASURER)


def numeric_server_version(display_version):
    major, minor = (int(part) for part in display_version.split('.'))
    return major * 10000 + minor


class InstallerMeasurementRuntimeProfileTests(unittest.TestCase):
    def test_public49_profile_pair_and_candidate_profile_are_accepted(self):
        # The public 0.0.49 wheel and current source use the selected 18.6 tuple.
        public49_display = '18.6'
        MEASURER._require_server_version_profile(
            public49_display, numeric_server_version(public49_display))

        candidate = json.loads(RUNTIME_PROFILE.read_bytes())
        MEASURER._require_server_version_profile(
            candidate['serverVersion'], numeric_server_version(candidate['serverVersion']))

    def test_wrong_display_or_numeric_profile_is_refused(self):
        for display, numeric in (('18.06', 180006), ('18.6', 180007)):
            with self.subTest(display=display, numeric=numeric), self.assertRaisesRegex(
                    RuntimeError, 'PostgreSQL 18.6 package profile'):
                MEASURER._require_server_version_profile(display, numeric)


class FakeCursor:
    def __init__(self, *, nextset_result=None, nextset_error=None):
        self.nextset_result = nextset_result
        self.nextset_error = nextset_error
        self.execute_result = object()

    def execute(self, *args, **kwargs):
        return self.execute_result

    def nextset(self, *args, **kwargs):
        if self.nextset_error is not None:
            raise self.nextset_error
        return self.nextset_result


class FakePsycopg:
    Cursor = FakeCursor


def measurement_recorder():
    return {
        'cursorExecuteCount': 0,
        'cursorExecuteElapsedNs': 0,
        'cursorExecuteMaxNs': 0,
        'cursorNextsetCount': 0,
        'cursorNextsetElapsedNs': 0,
        'cursorNextsetMaxNs': 0,
        'cursorNextsetFailureCount': 0,
        'orderedDdlHelperCalls': 0,
        'orderedDdlUnits': 0,
        'orderedDdlExecuteSubmissions': 0,
        'orderedDdlSourceUnitCount': 0,
        'orderedDdlOtherUnitCount': 0,
        'directSourceUnitExecuteSubmissions': 0,
        'sourceUnitHashes': set(),
    }


class InstallerMeasurementObserverTests(unittest.TestCase):
    def setUp(self):
        self.original_execute = FakeCursor.execute
        self.original_nextset = FakeCursor.nextset
        self.recorder = measurement_recorder()
        MEASURER._measure_cursor_execute(FakePsycopg, self.recorder)

    def tearDown(self):
        MEASURER._ACTIVE_MEASUREMENT.set(None)
        MEASURER._restore_instrumentation(FakePsycopg, self.recorder)

    def test_active_execute_and_nextset_are_counted_separately(self):
        cursor = FakeCursor(nextset_result=True)
        token = MEASURER._ACTIVE_MEASUREMENT.set(self.recorder)
        try:
            self.assertIs(cursor.execute('select 1'), cursor.execute_result)
            self.assertIs(cursor.nextset(), True)
        finally:
            MEASURER._ACTIVE_MEASUREMENT.reset(token)
        self.assertEqual(self.recorder['cursorExecuteCount'], 1)
        self.assertEqual(self.recorder['cursorNextsetCount'], 1)
        self.assertEqual(self.recorder['cursorNextsetFailureCount'], 0)
        self.assertGreaterEqual(self.recorder['cursorExecuteElapsedNs'], 0)
        self.assertGreaterEqual(self.recorder['cursorNextsetElapsedNs'], 0)

    def test_nextset_exception_identity_is_preserved_and_counted(self):
        error = RuntimeError('sentinel exception; not report data')
        cursor = FakeCursor(nextset_error=error)
        token = MEASURER._ACTIVE_MEASUREMENT.set(self.recorder)
        try:
            with self.assertRaises(RuntimeError) as raised:
                cursor.nextset()
        finally:
            MEASURER._ACTIVE_MEASUREMENT.reset(token)
        self.assertIs(raised.exception, error)
        self.assertEqual(self.recorder['cursorNextsetCount'], 1)
        self.assertEqual(self.recorder['cursorNextsetFailureCount'], 1)

    def test_inactive_calls_pass_through_and_hooks_restore_exactly(self):
        cursor = FakeCursor(nextset_result='unchanged')
        self.assertIs(cursor.execute('select 1'), cursor.execute_result)
        self.assertEqual(cursor.nextset(), 'unchanged')
        self.assertEqual(self.recorder['cursorExecuteCount'], 0)
        self.assertEqual(self.recorder['cursorNextsetCount'], 0)
        MEASURER._restore_instrumentation(FakePsycopg, self.recorder)
        self.assertIs(FakeCursor.execute, self.original_execute)
        self.assertIs(FakeCursor.nextset, self.original_nextset)

    def test_process_cpu_has_explicit_install_window_scope(self):
        summary = MEASURER._measurement_summary(
            self.recorder, install_elapsed_ns=23, process_cpu_ns=9
        )
        self.assertEqual(summary['installElapsedNs'], 23)
        self.assertEqual(summary['installerProcessCpuElapsedNs'], 9)
        self.assertEqual(summary['cursorExecuteSubmissionCount'], 0)
        self.assertEqual(summary['cursorNextsetCallCount'], 0)
        self.assertIn('whole diagnostic child process CPU', summary['processCpuScope'])
        self.assertNotIn('SQL', summary)

    def test_clocks_start_after_hook_setup_and_stop_at_installer_return(self):
        clock_calls = []
        hook_setup_complete = False

        def wall_clock():
            self.assertTrue(hook_setup_complete)
            clock_calls.append('wall')
            return 100 if clock_calls.count('wall') == 1 else 200

        def process_clock():
            self.assertTrue(hook_setup_complete)
            clock_calls.append('cpu')
            return 10 if clock_calls.count('cpu') == 1 else 30

        hook_setup_complete = True
        with patch.object(MEASURER, 'perf_counter_ns', wall_clock), patch.object(
                MEASURER.time, 'process_time_ns', process_clock):
            result = MEASURER._call_measured_install(
                self.recorder, lambda: 'installed'
            )
        self.assertEqual(result, 'installed')
        self.assertEqual(clock_calls, ['wall', 'cpu', 'wall', 'cpu'])
        self.assertEqual(self.recorder['installElapsedNs'], 100)
        self.assertEqual(self.recorder['installerProcessCpuElapsedNs'], 20)

    def test_summary_failure_does_not_mask_installer_error_or_skip_restore(self):
        self.recorder['installAttempted'] = True
        self.recorder['installElapsedNs'] = 10
        self.recorder['installerProcessCpuElapsedNs'] = 5
        token = MEASURER._ACTIVE_MEASUREMENT.set(self.recorder)
        original = RuntimeError('original installer failure')
        report_error = ValueError('reporting failure')
        result = {}
        try:
            with patch.object(
                    MEASURER, '_measurement_summary', side_effect=report_error):
                with self.assertRaises(RuntimeError) as raised:
                    try:
                        raise original
                    except BaseException as primary:
                        try:
                            raise
                        finally:
                            MEASURER._finish_measurement(
                                FakePsycopg, self.recorder, token, result, primary
                            )
        finally:
            MEASURER._ACTIVE_MEASUREMENT.set(None)
            MEASURER._restore_instrumentation(FakePsycopg, self.recorder)
        self.assertIs(raised.exception, original)
        self.assertEqual(result['measurementSummaryFailureType'], 'ValueError')
        self.assertTrue(result['instrumentationHooksRestored'])
        self.assertIs(FakeCursor.execute, self.original_execute)
        self.assertIs(FakeCursor.nextset, self.original_nextset)


if __name__ == '__main__':
    unittest.main()
