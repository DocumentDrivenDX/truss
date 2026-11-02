# SPDX-License-Identifier: MIT OR Apache-2.0
"""F7 native scalar component; does not qualify temporal sources or enrollment."""
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

import psycopg
from truss import LocalPostgres

ROOT = Path(__file__).resolve().parents[3]


class TemporalCanonicalTextNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.worker_fixture = None
        cls.runtime = None
        cls.root = None
        worker = os.environ.get('TRUSS_NATIVE_WORKER')
        if worker:
            from native_fixture import DatabaseFixture
            cls.worker_fixture = DatabaseFixture(Path(worker))
            cls.addClassCleanup(cls.worker_fixture.cleanup)
            uri = cls.worker_fixture.get_uri()
        else:
            cls.root = Path(tempfile.mkdtemp(prefix='truss-temporal-canonical-'))
            cls.runtime = LocalPostgres(cls.root / 'data')
            cls.addClassCleanup(cls.cleanup_owned_runtime)
            cls.runtime.__enter__()
            cls.original_pid = int((cls.runtime.directory / 'postmaster.pid').read_text().splitlines()[0])
            if cls.original_pid <= 0:
                raise RuntimeError('Original running postmaster PID required')
            uri = cls.runtime.info.connection_uri
        cls.connection = psycopg.connect(uri, autocommit=True, options='-c statement_timeout=10000')
        cls.addClassCleanup(cls.connection.close)
        cls.connection.execute('CREATE SCHEMA truss')
        cls.connection.execute((ROOT / 'packages/python/src/truss/_catalog_runtime/query-temporal.sql').read_text(), prepare=False)

    @classmethod
    def cleanup_owned_runtime(cls):
        proof = {'confirmed': False, 'dataDeleted': False, 'directory': str(cls.root)}
        try:
            cls.runtime.close()
            pid = getattr(cls, 'original_pid', None)
            if type(pid) is not int or pid <= 0:
                raise RuntimeError('Original native PID unavailable; retain owned data')
            status = subprocess.run([str(cls.runtime.psql_path.with_name('pg_ctl')), '-D',
                                     str(cls.runtime.directory), 'status'],
                                    capture_output=True, text=True, timeout=15, check=False)
            absent = False
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                absent = True
            proof.update(originalPostmasterPid=pid, originalPostmasterPidAbsent=absent,
                         pgCtlStatus=status.returncode, pgCtlStdout=status.stdout, pgCtlStderr=status.stderr)
            if status.returncode != 3 or not absent:
                raise RuntimeError('Native cleanup uncertain; retain owned data')
            proof['confirmed'] = True
            shutil.rmtree(cls.root)
            proof['dataDeleted'] = not cls.root.exists()
        finally:
            print('temporal-canonical-cleanup ' + json.dumps(proof, sort_keys=True))

    def canonical(self, kind, token):
        return self.connection.execute('SELECT truss.query_temporal_canonical_text(%s,%s)', (kind, token)).fetchone()[0]

    def test_contract075_canonical_vectors_and_original_text(self):
        vectors = (
            ('date', '0001-01-01', '0001-01-01'),
            ('date', '2000-02-29', '2000-02-29'),
            ('date', '9999-12-31', '9999-12-31'),
            ('local', '2024-02-29T12:34:56.1', '2024-02-29T12:34:56.100000'),
            ('local', '0001-01-01T00:00:00', '0001-01-01T00:00:00.000000'),
            ('local', '9999-12-31T23:59:59.999999', '9999-12-31T23:59:59.999999'),
            ('instant', '2024-01-01T01:30:00.123456+01:30', '2024-01-01T00:00:00.123456Z'),
            ('instant', '1969-12-31T23:59:59.5Z', '1969-12-31T23:59:59.500000Z'),
            ('instant', '1970-01-01T00:00:00+00:01', '1969-12-31T23:59:00.000000Z'),
            ('instant', '2024-01-01T23:59:59.123456+23:59', '2024-01-01T00:00:59.123456Z'),
        )
        self.connection.execute('CREATE TEMP TABLE temporal_original(kind text, token text, original bytea)')
        for kind, token, expected in vectors:
            with self.subTest(kind=kind, token=token):
                self.assertEqual(self.canonical(kind, token), expected)
            self.connection.execute('INSERT INTO temporal_original VALUES(%s,%s,%s)', (kind, token, token.encode()))
        rows = self.connection.execute('SELECT token,original,truss.query_temporal_canonical_text(kind,token) FROM temporal_original').fetchall()
        self.assertEqual([(token, bytes(original)) for token, original, _ in rows],
                         [(token, token.encode()) for _, token, _ in vectors])
        self.assertEqual([canonical for _, _, canonical in rows], [expected for _, _, expected in vectors])

    def test_exact_integer_offset_normalization_against_fixed_offset_carriers(self):
        for year, month, day in ((1969, 12, 31), (1970, 1, 1), (2000, 2, 29), (2024, 3, 1)):
            for offset in (-1439, -60, -1, 0, 1, 60, 1439):
                value = datetime(year, month, day, 0, 0, 9, 123456,
                                 tzinfo=timezone(timedelta(minutes=offset)))
                suffix = ('-' if offset < 0 else '+') + f'{abs(offset)//60:02}:{abs(offset)%60:02}'
                token = f'{year:04}-{month:02}-{day:02}T00:00:09.123456{suffix}'
                utc = value.astimezone(timezone.utc)
                expected = f'{utc.year:04}-{utc.month:02}-{utc.day:02}T{utc.hour:02}:{utc.minute:02}:{utc.second:02}.{utc.microsecond:06}Z'
                with self.subTest(token=token):
                    self.assertEqual(self.canonical('instant', token), expected)

    def test_strict_grammar_calendar_kind_and_normalized_range_refusals(self):
        invalid = (
            (None, '2024-01-01'), ('date', None), ('unknown', '2024-01-01'),
            ('date', '0000-01-01'), ('date', '1900-02-29'), ('date', '2024-02-30'),
            ('date', '2024-13-01'), ('date', '2024-01-00'), ('date', '２０２４-01-01'),
            ('date', '2024-01-01\n'), ('date', '2024-01-01 '), ('date', '2024-01-01T00:00:00'),
            ('local', '2024-01-01T24:00:00'), ('local', '2024-01-01T00:60:00'),
            ('local', '2024-01-01T00:00:60'), ('local', '2024-01-01t00:00:00'),
            ('local', '2024-01-01T00:00:00.1234560'), ('local', '2024-01-01T00:00:00.'),
            ('local', '2024-01-01T00:00:00Z'), ('local', '2024-01-01T00:00:00.000000\r'),
            ('instant', '2024-01-01T00:00:00'), ('instant', '2024-01-01T00:00:00z'),
            ('instant', '2024-01-01T00:00:00-00:00'), ('instant', '2024-01-01T00:00:00+24:00'),
            ('instant', '2024-01-01T00:00:00+00:60'), ('instant', '2024-01-01T00:00:00+00:00:01'),
            ('instant', '2024-01-01T00:00:00.1234560Z'), ('instant', '2024-01-01T00:00:00Z\n'),
            ('instant', '0001-01-01T00:00:00+00:01'), ('instant', '9999-12-31T23:59:59-00:01'),
            ('instant', '0' * 33),
        )
        for kind, token in invalid:
            with self.subTest(kind=kind, token=token), self.assertRaises(psycopg.Error) as caught:
                self.canonical(kind, token)
            self.assertEqual(caught.exception.sqlstate, '22023')

    def test_host_timezone_datestyle_and_collation_do_not_change_tokens(self):
        try:
            for timezone_name, date_style in (('Pacific/Apia', 'SQL, DMY'), ('America/New_York', 'German, DMY')):
                self.connection.execute('SELECT set_config(\'TimeZone\',%s,false),set_config(\'DateStyle\',%s,false)',
                                        (timezone_name, date_style))
                self.assertEqual(self.canonical('instant', '0001-01-01T00:01:00+00:01'), '0001-01-01T00:00:00.000000Z')
                self.assertEqual(self.canonical('local', '2024-11-03T01:30:00.1'), '2024-11-03T01:30:00.100000')
            tokens = ['1970-01-01T00:00:10Z', '1969-12-31T23:59:59.999999Z',
                      '1970-01-01T00:00:09Z', '1970-01-01T00:00:00Z']
            actual = self.connection.execute("SELECT c FROM (SELECT truss.query_temporal_canonical_text('instant',t) AS c FROM unnest(%s::text[]) t) q ORDER BY c COLLATE \"C\"", (tokens,)).fetchall()
            self.assertEqual([row[0] for row in actual], [
                '1969-12-31T23:59:59.999999Z', '1970-01-01T00:00:00.000000Z',
                '1970-01-01T00:00:09.000000Z', '1970-01-01T00:00:10.000000Z'])
        finally:
            self.connection.execute("SET TimeZone='UTC';SET DateStyle='ISO, MDY'")

    def test_helper_is_immutable_invoker_and_has_no_public_execute(self):
        metadata = self.connection.execute("SELECT provolatile,prosecdef,EXISTS(SELECT 1 FROM aclexplode(coalesce(proacl,acldefault('f',proowner))) a WHERE a.grantee=0 AND a.privilege_type='EXECUTE') FROM pg_proc WHERE oid='truss.query_temporal_canonical_text(text,text)'::regprocedure").fetchone()
        self.assertEqual(metadata, ('i', False, False))
