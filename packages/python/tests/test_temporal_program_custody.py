# SPDX-License-Identifier: MIT OR Apache-2.0
"""Host dispatch and response custody controls; no Rust qualification claim."""
import json
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from truss._temporal_program_custody import (
    TemporalProgramRefused,
    TemporalProgramUnavailable,
    check_current,
    check_shape,
)


class FakeCompiler:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def _record(self, operation, *arguments):
        self.calls.append((operation, arguments))
        return self.response

    def check_engine_temporal_read_shape_json(self, program, request):
        return self._record('check_engine_temporal_read_shape_json', program, request)

    def check_engine_temporal_page_shape_json(self, program, request):
        return self._record('check_engine_temporal_page_shape_json', program, request)

    def check_engine_temporal_read_json(self, program, request):
        return self._record('check_engine_temporal_read_json', program, request)

    def check_engine_temporal_page_json(self, program, request, after):
        return self._record('check_engine_temporal_page_json', program, request, after)


class TemporalProgramCustodyTests(unittest.TestCase):
    def setUp(self):
        self.program = {
            'status': 'compiled',
            'artifact': {'sql': 'SELECT original_sql', 'parameters': ['exact']},
            'request': {'bindingJson': ' { "original": true }\n'},
            'futureOwnerMember': {'nested': [None, {'retained': 'all members'}]},
        }
        self.response = json.dumps({'status': 'checked', 'program': self.program})
        self.original_program = '  {"program": "unchanged original"}\n'
        self.request = '\n { "request": "exact original spelling" } '
        self.after = ' { "continuation": "unchanged" }\n'

    def _routes(self):
        return (
            (check_shape, False, 'check_engine_temporal_read_shape_json'),
            (check_shape, True, 'check_engine_temporal_page_shape_json'),
            (check_current, False, 'check_engine_temporal_read_json'),
            (check_current, True, 'check_engine_temporal_page_json'),
        )

    def test_all_four_routes_pass_original_strings_and_return_whole_program(self):
        for helper, page, operation in self._routes():
            with self.subTest(operation=operation):
                compiler = FakeCompiler(self.response)
                kwargs = {'page': page}
                arguments = (self.original_program, self.request)
                if helper is check_current and page:
                    kwargs['after_json'] = self.after
                    arguments += (self.after,)
                result = helper(compiler, self.original_program, self.request, **kwargs)
                self.assertEqual(result, self.program)
                self.assertEqual(compiler.calls, [(operation, arguments)])
                for actual, original in zip(compiler.calls[0][1], arguments):
                    self.assertIs(actual, original)

    def test_current_page_default_after_is_json_null(self):
        compiler = FakeCompiler(self.response)
        check_current(compiler, self.original_program, self.request, page=True)
        self.assertEqual(compiler.calls[0][1], (self.original_program, self.request, 'null'))
        compiler.calls.clear()
        explicit_null = ' \nnull '
        check_current(compiler, self.original_program, self.request, page=True, after_json=explicit_null)
        self.assertIs(compiler.calls[0][1][2], explicit_null)

    def test_current_read_does_not_forward_after_or_call_page_checker(self):
        compiler = FakeCompiler(self.response)
        check_current(compiler, self.original_program, self.request,
                      page=False, after_json=self.after)
        self.assertEqual(compiler.calls, [
            ('check_engine_temporal_read_json', (self.original_program, self.request)),
        ])

    def test_missing_or_noncallable_checker_reports_exact_operation_without_fallback(self):
        for helper, page, operation in self._routes():
            for present in (False, True):
                with self.subTest(operation=operation, noncallable=present):
                    ordinary = Mock(side_effect=AssertionError('Ordinary fallback invoked'))
                    compiler = SimpleNamespace(check_engine_read_json=ordinary,
                        check_engine_page_json=ordinary)
                    if present:
                        setattr(compiler, operation, 'not callable')
                    with self.assertRaises(TemporalProgramUnavailable) as caught:
                        helper(compiler, self.original_program, self.request, page=page)
                    self.assertEqual(caught.exception.operation, operation)
                    ordinary.assert_not_called()

    def test_blocked_response_retains_full_original_and_parsed_response(self):
        blocked = {'status': 'blocked', 'diagnostics': [
            {'code': 'WFT-ENGINE-READ', 'details': ['first', 'second']},
        ], 'original': {'status': 'blocked', 'diagnostics': [{'owner': 'unchanged'}]},
            'futureEvidence': {'retain': True}}
        original = ' \n' + json.dumps(blocked) + '\n '
        for helper, page, operation in self._routes():
            with self.subTest(operation=operation):
                with self.assertRaises(TemporalProgramRefused) as caught:
                    helper(FakeCompiler(original), self.original_program, self.request, page=page)
                self.assertIs(caught.exception.original, original)
                self.assertEqual(caught.exception.parsed, blocked)

    def test_malformed_response_is_refused_with_original_retained(self):
        cases = ('not JSON', 'null', '[]', '{}',
            '{"status":"compiled","program":{}}',
            '{"status":true,"program":{}}', '{"status":"checked"}',
            '{"status":"checked","program":null}',
            '{"status":"checked","program":[]}',
            '{"status":"checked","program":"sql"}',
            '{"status":"checked","program":{},"extra":"not F6"}',
            '{"status":"checked","status":"blocked","program":{}}',
            '{"status":"checked","program":{"number":NaN}}')
        for original in cases:
            with self.subTest(original=original):
                with self.assertRaises(TemporalProgramRefused) as caught:
                    check_shape(FakeCompiler(original), self.original_program, self.request, page=False)
                self.assertIs(caught.exception.original, original)

    def test_nonstring_response_is_not_accepted_as_f6(self):
        original = {'status': 'checked', 'program': self.program}
        with self.assertRaises(TemporalProgramRefused) as caught:
            check_shape(FakeCompiler(original), self.original_program, self.request, page=False)
        self.assertEqual(caught.exception.original, original)

    def test_success_and_refusal_parsing_do_not_share_mutable_results(self):
        compiler = FakeCompiler(self.response)
        first = check_shape(compiler, self.original_program, self.request, page=False)
        first['futureOwnerMember']['nested'].clear()
        second = check_shape(compiler, self.original_program, self.request, page=False)
        self.assertEqual(second, self.program)
        self.assertIs(compiler.response, self.response)
        blocked = '{"status":"blocked","diagnostics":[{"retain":["original"]}]}'
        compiler.response = blocked
        for index in range(2):
            with self.assertRaises(TemporalProgramRefused) as caught:
                check_shape(compiler, self.original_program, self.request, page=False)
            self.assertEqual(caught.exception.parsed['diagnostics'][0]['retain'], ['original'])
            caught.exception.parsed['diagnostics'][0]['retain'].clear()
            self.assertIs(caught.exception.original, blocked)

    def test_checker_exception_propagates_without_retry_or_fallback(self):
        error = RuntimeError('original checker error')
        checker = Mock(side_effect=error)
        compiler = SimpleNamespace(check_engine_temporal_read_json=checker)
        with self.assertRaises(RuntimeError) as caught:
            check_current(compiler, self.original_program, self.request, page=False)
        self.assertIs(caught.exception, error)
        checker.assert_called_once_with(self.original_program, self.request)

    def test_invalid_route_or_nonstring_arguments_never_call_compiler(self):
        compiler = FakeCompiler(self.response)
        for page in ('page', 1, None):
            with self.subTest(page=page), self.assertRaises(ValueError):
                check_shape(compiler, self.original_program, self.request, page=page)
        for program, request in (({}, self.request), (self.original_program, [])):
            with self.subTest(program=program, request=request), self.assertRaises(ValueError):
                check_current(compiler, program, request, page=False)
        with self.assertRaises(ValueError):
            check_current(compiler, self.original_program, self.request, page=True, after_json=None)
        self.assertEqual(compiler.calls, [])


if __name__ == '__main__':
    unittest.main()
