# SPDX-License-Identifier: MIT OR Apache-2.0
"""Cleanup failures cannot replace cancellation or escape credential diagnostics."""
import unittest
from unittest.mock import patch
from truss._scram_preparation_login import ScramPreparationLogin


class BrokenCloseConnection:
    class PGconn:
        used_password = True
    pgconn = PGconn()

    def __init__(self, original):
        self.original = original
        self.close_attempted = False

    def cursor(self):
        raise self.original

    def close(self):
        self.close_attempted = True
        raise RuntimeError('secondary driver error with secret diagnostic')


class ScramCleanupTests(unittest.TestCase):
    def test_secondary_close_failure_is_redacted(self):
        connection = BrokenCloseConnection(RuntimeError('original sensitive diagnostic'))
        login = ScramPreparationLogin('/tmp/original-socket', 5432, 'store', 'person', 'private')
        with patch('truss._scram_preparation_login.psycopg.connect', return_value=connection):
            with self.assertRaises(ValueError) as caught:
                login.open_connection()
        self.assertEqual(str(caught.exception), 'Original SCRAM login refused; connection cleanup unconfirmed')
        self.assertTrue(caught.exception.__suppress_context__)
        self.assertTrue(connection.close_attempted)

    def test_original_cancellation_survives_secondary_close_failure(self):
        original = KeyboardInterrupt()
        connection = BrokenCloseConnection(original)
        login = ScramPreparationLogin('/tmp/original-socket', 5432, 'store', 'person', 'private')
        with patch('truss._scram_preparation_login.psycopg.connect', return_value=connection):
            with self.assertRaises(KeyboardInterrupt) as caught:
                login.open_connection()
        self.assertIs(caught.exception, original)
        self.assertEqual(original.__notes__, ['SCRAM connection cleanup unconfirmed'])
        self.assertTrue(connection.close_attempted)
