# SPDX-License-Identifier: MIT OR Apache-2.0
"""Current PG18.6 profile and timeout behavior on the ordinary native fixture."""
from truss import PsycopgProfile, adopt_psycopg_host, Ok, Error
import test_psycopg_host_native as base

class CurrentPsycopgProfileTests(base.PsycopgHostNativeTests):
    selected_profile = PsycopgProfile(server=180006)
    for name in tuple(n for n in dir(base.PsycopgHostNativeTests) if n.startswith('test_')):
        locals()[name] = None

    def test_selected_profile_retained(self):
        self.assertIs(self.host.profile,self.selected_profile)
        self.assertEqual(self.connection.info.server_version,180006)

    def test_wrong_profile_refuses_before_attachment(self):
        self.host.detach()
        for profile in (PsycopgProfile(server=160015),PsycopgProfile(server=180005),PsycopgProfile(libpq=170011,server=180006),None):
            with self.subTest(profile=profile),self.assertRaises(ValueError):adopt_psycopg_host(self.connection,profile=profile)
        self.host=adopt_psycopg_host(self.connection,profile=self.selected_profile)

    def test_transaction_timeout_terminates_and_quarantines(self):
        self.host.detach()
        self.host=adopt_psycopg_host(self.connection,profile=self.selected_profile,statement_timeout_ms=3000)
        self.connection.execute("SET transaction_timeout='1000ms'")
        transaction=self.begin()
        self.assertEqual(self.scalar(transaction,'SHOW transaction_timeout'),Ok('1s'))
        result=self.scalar(transaction,'SELECT pg_sleep(2)')
        self.assertIsInstance(result,Error)
        self.assertEqual(result.error.code,'transaction_unusable')
        self.assertEqual(result.error.sql_state,'25P04')
        self.assertEqual(self.host._custody.last_attempt.error.sqlstate,'25P04')
        self.assertTrue(self.connection.closed or self.connection.broken)
        self.assertTrue(self.host._custody.quarantined)
        self.assertIsNotNone(self.host._custody.last_attempt.error)
        self.assertIsInstance(self.host._run_operation(transaction,lambda cursor,observed:self.fail('Quarantined callback ran')),Error)
        with self.assertRaises(ValueError):adopt_psycopg_host(self.connection,profile=self.selected_profile)

