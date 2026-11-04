# SPDX-License-Identifier: MIT OR Apache-2.0
"""JH parameter-derivation controls, NOT simulated future-install qualification.

Expected endpoints/bounds below are authored literals. PostgreSQL is the calendar
and timezone authority; no Python datetime/calendar codec or server clock override
is used. Execution requires the already-owned campaign worker, never a new cluster.
"""
from contextlib import contextmanager
import os
from pathlib import Path
import re
import unittest
from unittest.mock import patch

import psycopg
from psycopg.pq import TransactionStatus
from native_fixture import DatabaseFixture
from truss import _initialization_custody as custody


class _TransactionOnlyConnection:
    """Expose savepoint contexts, never direct connection SQL/cursor access."""
    __slots__ = ('__transaction',)

    def __init__(self, connection):
        self.__transaction = connection.transaction

    @contextmanager
    def transaction(self, *args, **kwargs):
        # Do not expose the native Transaction through the context's as-value;
        # its connection would otherwise provide an unobserved SQL route.
        with self.__transaction(*args, **kwargs):
            yield None


class _NoClockCursor:
    """Record SQL and refuse native time observations before forwarding them."""
    forbidden = re.compile(
        r'\b(clock_timestamp|statement_timestamp|transaction_timestamp|timeofday|now|'
        r'current_timestamp|current_date|current_time|localtimestamp|localtime)\b', re.I)

    __slots__ = ('__cursor', '__connection', 'statements')

    def __init__(self, cursor):
        self.__cursor = cursor
        self.__connection = _TransactionOnlyConnection(cursor.connection)
        self.statements = []

    @property
    def connection(self):
        return self.__connection

    def execute(self, query, *args, **kwargs):
        if not isinstance(query, str) or self.forbidden.search(query):
            raise AssertionError('Parameter derivation attempted a current-clock observation')
        self.statements.append(query)
        self.__cursor.execute(query, *args, **kwargs)
        return self

    def fetchone(self):
        return self.__cursor.fetchone()

    def fetchall(self):
        return self.__cursor.fetchall()


class InitializationCustodyDerivationNativeTests(unittest.TestCase):
    def setUp(self):
        worker = os.environ.get('TRUSS_NATIVE_WORKER')
        if not worker:
            raise RuntimeError('JH derivation requires campaign-owned TRUSS_NATIVE_WORKER')
        self.fixture = DatabaseFixture(Path(worker))
        self.addCleanup(self.fixture.cleanup)
        self.connection = psycopg.connect(
            self.fixture.get_uri(), autocommit=False, options='-c statement_timeout=10000')
        self.addCleanup(self.connection.close)
        self.addCleanup(self.connection.rollback)
        self.connection.execute("SELECT set_config('DateStyle','ISO, YMD',true)")
        self.connection.execute('CREATE TEMP TABLE jh_derivation_caller_work(token text) ON COMMIT DROP')
        self.connection.execute("INSERT INTO jh_derivation_caller_work VALUES ('preserve caller work')")
        self.outer_xid = self.connection.execute('SELECT pg_current_xact_id()::text').fetchone()[0]

    def _zone(self):
        return self.connection.execute('SHOW TimeZone').fetchone()[0]

    def _retain_zone(self, zone):
        self.assertEqual(self.connection.execute(
            "SELECT set_config('TimeZone',%s,true)", (zone,)).fetchone(), (zone,))

    def _outer_usable(self):
        self.assertEqual(self.connection.info.transaction_status, TransactionStatus.INTRANS)
        self.assertEqual(self.connection.execute('SELECT token FROM jh_derivation_caller_work').fetchall(),
                         [('preserve caller work',)])
        self.assertEqual(self.connection.execute('SELECT pg_current_xact_id()::text').fetchone(),
                         (self.outer_xid,))

    def _assert_result(self, actual, expected_pairs, expected_bounds):
        self.assertIs(type(actual), tuple)
        self.assertEqual(len(actual), 2)
        pairs, bounds = actual
        self.assertIs(type(pairs), list)
        self.assertIs(type(bounds), list)
        self.assertEqual(pairs, expected_pairs)
        self.assertEqual(bounds, expected_bounds)
        for pair in pairs:
            self.assertIs(type(pair), dict)
            self.assertEqual(set(pair), {'lowerUtc', 'upperUtc'})
            for value in pair.values():
                self.assertIs(type(value), str)
                self.assertRegex(value, r'^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z$')
        for bound in bounds:
            self.assertIs(type(bound), str)

    def _one(self, before, after, zone, lower, upper, bound):
        retained = self._zone()
        with self.connection.transaction(), self.connection.cursor() as cursor:
            actual = custody.derive(cursor, before, after, zone)
            self._assert_result(actual, [{'lowerUtc': lower, 'upperUtc': upper}], [bound])
            self.assertEqual(self._zone(), retained)  # before savepoint exit, not rollback repair
        self._outer_usable()

    def _refuse(self, before, after, zone):
        retained = self._zone()
        # Nested psycopg transaction is an actual savepoint in caller transaction.
        with self.assertRaises((ValueError, psycopg.Error)) as caught:
            with self.connection.transaction(), self.connection.cursor() as cursor:
                custody.derive(cursor, before, after, zone)
        if isinstance(caught.exception, psycopg.Error):
            # InFailedSqlTransaction (25P02) would mask the original native error.
            self.assertIn(caught.exception.sqlstate, ('22007', '22008', '22023'))
        self.assertEqual(self._zone(), retained)
        self._outer_usable()

    def test_authored_month_year_leap_and_dst_endpoint_vectors(self):
        vectors = [
            ('UTC', '2026-11-15T12:00:00.000000Z', '2026-11-15T12:00:00.000001Z',
             '2026-10-01T00:00:00.000000Z', '2027-12-01T00:00:00.000000Z',
             "FOR VALUES FROM ('2026-10-01 00:00:00+00') TO ('2027-12-01 00:00:00+00')"),
            ('UTC', '2026-12-31T12:00:00.000000Z', '2026-12-31T12:00:00.000000Z',
             '2026-11-01T00:00:00.000000Z', '2028-01-01T00:00:00.000000Z',
             "FOR VALUES FROM ('2026-11-01 00:00:00+00') TO ('2028-01-01 00:00:00+00')"),
            ('UTC', '2024-02-29T23:59:59.000000Z', '2024-02-29T23:59:59.999999Z',
             '2024-01-01T00:00:00.000000Z', '2025-03-01T00:00:00.000000Z',
             "FOR VALUES FROM ('2024-01-01 00:00:00+00') TO ('2025-03-01 00:00:00+00')"),
            ('UTC', '2024-03-15T12:00:00.000000Z', '2024-03-15T12:05:00.000000Z',
             '2024-02-01T00:00:00.000000Z', '2025-04-01T00:00:00.000000Z',
             "FOR VALUES FROM ('2024-02-01 00:00:00+00') TO ('2025-04-01 00:00:00+00')"),
            # Spring transition: February lower is EST, April upper is EDT.
            ('America/New_York', '2024-03-10T06:59:59.000000Z', '2024-03-10T07:00:01.000000Z',
             '2024-02-01T05:00:00.000000Z', '2025-04-01T04:00:00.000000Z',
             "FOR VALUES FROM ('2024-02-01 05:00:00+00') TO ('2025-04-01 04:00:00+00')"),
            # Fall transition: October lower is EDT, December upper is EST.
            ('America/New_York', '2024-11-03T05:59:59.000000Z', '2024-11-03T06:00:01.000000Z',
             '2024-10-01T04:00:00.000000Z', '2025-12-01T05:00:00.000000Z',
             "FOR VALUES FROM ('2024-10-01 04:00:00+00') TO ('2025-12-01 05:00:00+00')"),
        ]
        for zone, before, after, lower, upper, bound in vectors:
            with self.subTest(zone=zone, before=before):
                self._one(before, after, zone, lower, upper, bound)

    def test_rollover_exact_three_pairs_and_forbidden_new_old(self):
        vectors = [
            ('UTC', '2026-11-30T23:59:59.999999Z', '2026-12-01T00:00:00.000000Z', [
                {'lowerUtc': '2026-10-01T00:00:00.000000Z', 'upperUtc': '2027-12-01T00:00:00.000000Z'},
                {'lowerUtc': '2026-10-01T00:00:00.000000Z', 'upperUtc': '2028-01-01T00:00:00.000000Z'},
                {'lowerUtc': '2026-11-01T00:00:00.000000Z', 'upperUtc': '2028-01-01T00:00:00.000000Z'}], [
                "FOR VALUES FROM ('2026-10-01 00:00:00+00') TO ('2027-12-01 00:00:00+00')",
                "FOR VALUES FROM ('2026-10-01 00:00:00+00') TO ('2028-01-01 00:00:00+00')",
                "FOR VALUES FROM ('2026-11-01 00:00:00+00') TO ('2028-01-01 00:00:00+00')"],
                {'lowerUtc': '2026-11-01T00:00:00.000000Z', 'upperUtc': '2027-12-01T00:00:00.000000Z'}),
            ('America/New_York', '2025-01-01T04:59:59.999999Z', '2025-01-01T05:00:00.000000Z', [
                {'lowerUtc': '2024-11-01T04:00:00.000000Z', 'upperUtc': '2026-01-01T05:00:00.000000Z'},
                {'lowerUtc': '2024-11-01T04:00:00.000000Z', 'upperUtc': '2026-02-01T05:00:00.000000Z'},
                {'lowerUtc': '2024-12-01T05:00:00.000000Z', 'upperUtc': '2026-02-01T05:00:00.000000Z'}], [
                "FOR VALUES FROM ('2024-11-01 04:00:00+00') TO ('2026-01-01 05:00:00+00')",
                "FOR VALUES FROM ('2024-11-01 04:00:00+00') TO ('2026-02-01 05:00:00+00')",
                "FOR VALUES FROM ('2024-12-01 05:00:00+00') TO ('2026-02-01 05:00:00+00')"],
                {'lowerUtc': '2024-12-01T05:00:00.000000Z', 'upperUtc': '2026-01-01T05:00:00.000000Z'}),
        ]
        for zone, before, after, expected, bounds, forbidden in vectors:
            with self.subTest(zone=zone):
                with self.connection.transaction(), self.connection.cursor() as cursor:
                    actual = custody.derive(cursor, before, after, zone)
                self._assert_result(actual, expected, bounds)  # exact order/completeness, not membership
                self.assertEqual(len(actual[0]), 3)
                self.assertNotIn(forbidden, actual[0])
                self._outer_usable()

    def test_invalid_noncanonical_nonfinite_reversed_and_oversized_windows_refuse(self):
        valid = '2026-11-15T12:00:00.000000Z'
        invalid = [None, True, 2026, 1.5, '', 'infinity', '-infinity', 'NaN',
                   '2026-11-15T12:00:00Z', '2026-11-15T12:00:00.00000Z',
                   '2026-11-15T12:00:00.0000000Z', '2026-11-15T12:00:00.000000+00:00',
                   '2026-11-15 12:00:00.000000Z', '2026-11-15T12:00:00.000000z',
                   ' 2026-11-15T12:00:00.000000Z', '2026-11-15T12:00:00.000000Z\n',
                   '0000-11-15T12:00:00.000000Z', '10000-11-15T12:00:00.000000Z',
                   '2023-02-29T12:00:00.000000Z', '2026-13-15T12:00:00.000000Z',
                   '2026-11-00T12:00:00.000000Z']
        for value in invalid:
            for before, after in ((value, valid), (valid, value)):
                with self.subTest(before=before, after=after):
                    self._refuse(before, after, 'UTC')
        for before, after in [
            ('2026-11-15T12:00:00.000001Z', valid),
            (valid, '2026-11-15T12:05:00.000001Z'),  # max + exactly one microsecond
            ('2026-11-30T23:57:30.000000Z', '2026-12-01T00:02:30.000001Z'),
            ('2026-11-01T00:00:00.000000Z', '2027-01-01T00:00:00.000000Z'),
        ]:
            with self.subTest(before=before, after=after):
                self._refuse(before, after, 'UTC')

    def test_unsupported_zone_and_endpoint_overflow_refuse(self):
        before = '2026-11-15T12:00:00.000000Z'
        for zone in ('Europe/London', 'US/Eastern', 'Etc/UTC', '+00:00', '', None):
            with self.subTest(zone=zone):
                self._refuse(before, before, zone)
        # Finite accepted input range still cannot produce BC or >9999 endpoints.
        for instant in ('0001-01-15T12:00:00.000000Z', '9999-12-15T12:00:00.000000Z'):
            with self.subTest(endpoint_overflow=instant):
                self._refuse(instant, instant, 'UTC')

    def test_retained_zone_restored_on_success_and_native_refusal(self):
        for retained in ('Pacific/Auckland', 'Asia/Kathmandu'):
            with self.subTest(retained=retained):
                self._retain_zone(retained)
                self._one('2026-11-15T12:00:00.000000Z', '2026-11-15T12:00:00.000001Z', 'UTC',
                          '2026-10-01T00:00:00.000000Z', '2027-12-01T00:00:00.000000Z',
                          "FOR VALUES FROM ('2026-10-01 00:00:00+00') TO ('2027-12-01 00:00:00+00')")
                # A no-row refusal must restore zone while transaction is usable,
                # without relying on savepoint rollback to repair the setting.
                with self.connection.transaction(), self.connection.cursor() as cursor:
                    with self.assertRaises(ValueError):
                        custody.derive(cursor, '2026-11-15T12:00:00.000001Z',
                                       '2026-11-15T12:00:00.000000Z', 'UTC')
                    self.assertEqual(self._zone(), retained)
                # Actual native invalid date. Original SQLSTATE22008 must survive
                # cleanup; 25P02 from a restore in an aborted transaction is wrong.
                with self.connection.transaction(), self.connection.cursor() as cursor:
                    with self.assertRaises(psycopg.errors.DatetimeFieldOverflow) as caught:
                        custody.derive(cursor, '2024-02-30T12:00:00.000000Z',
                                       '2024-02-30T12:00:00.000000Z', 'UTC')
                    # All assertions precede enclosing savepoint exit: derive
                    # must recover itself, not leave rollback repair to caller.
                    self.assertEqual(caught.exception.sqlstate, '22008')
                    self.assertEqual(self._zone(), retained)
                    self._outer_usable()  # same outer xid and preserved caller work

    def test_parameter_derivation_never_observes_current_clock(self):
        with self.connection.transaction(), self.connection.cursor() as cursor:
            guard = _NoClockCursor(cursor)
            # The only connection surface is transaction(); neither direct SQL
            # nor a raw cursor can bypass the clock detector.
            for target, attribute in [(guard.connection, 'execute'),
                                      (guard.connection, 'cursor'),
                                      (guard.connection, 'connection'), (guard, 'cursor')]:
                with self.subTest(blocked_attribute=attribute):
                    with self.assertRaises(AttributeError):
                        getattr(target, attribute)
            with guard.connection.transaction() as transaction_value:
                self.assertIsNone(transaction_value)
            # Sensitivity: guard blocks this statement before it reaches PostgreSQL.
            with self.assertRaises(AssertionError):
                guard.execute('SELECT pg_catalog.clock_timestamp()')
            self.assertEqual(guard.statements, [])
            with patch.object(custody, 'observe', side_effect=AssertionError('No current observer allowed')):
                for before, lower, upper, bound in [
                    ('1900-02-28T12:00:00.000000Z', '1900-01-01T00:00:00.000000Z',
                     '1901-03-01T00:00:00.000000Z',
                     "FOR VALUES FROM ('1900-01-01 00:00:00+00') TO ('1901-03-01 00:00:00+00')"),
                    ('2000-02-29T12:00:00.000000Z', '2000-01-01T00:00:00.000000Z',
                     '2001-03-01T00:00:00.000000Z',
                     "FOR VALUES FROM ('2000-01-01 00:00:00+00') TO ('2001-03-01 00:00:00+00')"),
                    ('2099-12-15T12:00:00.000000Z', '2099-11-01T00:00:00.000000Z',
                     '2101-01-01T00:00:00.000000Z',
                     "FOR VALUES FROM ('2099-11-01 00:00:00+00') TO ('2101-01-01 00:00:00+00')"),
                ]:
                    with self.subTest(retained_parameter=before):
                        self._assert_result(custody.derive(guard, before, before, 'UTC'),
                                            [{'lowerUtc': lower, 'upperUtc': upper}], [bound])
            self.assertTrue(guard.statements)
            self.assertFalse(any(guard.forbidden.search(sql) for sql in guard.statements))
        self._outer_usable()
