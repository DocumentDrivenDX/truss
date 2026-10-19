# SPDX-License-Identifier: MIT OR Apache-2.0
"""Ordinary callers cannot write private journal or settlement tables."""
import psycopg
from psycopg import sql

import test_object_mutations_native as base


class JournalRowGuardTests(base.ObjectMutationTests):
    for _name in tuple(n for n in dir(base.ObjectMutationTests) if n.startswith('test_')):
        locals()[_name] = None

    def test_consumer_cannot_write_journal_partitions_or_owned_control_tables(self):
        connection, host, assembly, tx = self.ready()
        host.detach()

        relations = self.admin.execute("""SELECT n.nspname,c.relname
            FROM pg_class parent JOIN pg_namespace pn ON pn.oid=parent.relnamespace
            JOIN pg_inherits i ON i.inhparent=parent.oid JOIN pg_class c ON c.oid=i.inhrelid
            JOIN pg_namespace n ON n.oid=c.relnamespace
            WHERE pn.nspname='truss' AND parent.relname='journal'
            UNION ALL SELECT 'truss','journal'
            UNION ALL SELECT 'truss',unnest(ARRAY['runtime_object_attempt',
                'runtime_object_transition','runtime_owned_operation','runtime_create_group'])
            ORDER BY 1""").fetchall()
        relation_names = [(row[0], row[1]) for row in relations]
        self.assertGreaterEqual(len(relation_names), 6)
        privileges = [(schema, name, self.admin.execute(
            'SELECT has_table_privilege(\'consumer\',%s,\'INSERT\')',
            (f'{schema}.{name}',)).fetchone()[0]) for schema, name in relation_names]
        self.assertEqual(privileges, [(schema, name, False) for schema, name in relation_names])

        # No per-row journal oracle is installed. Engine procedures own the
        # write path; supported deferred settlement validates completed attempts.
        journal_guards = self.admin.execute("""SELECT count(*) FROM pg_trigger t
            JOIN pg_class c ON c.oid=t.tgrelid JOIN pg_namespace n ON n.oid=c.relnamespace
            WHERE n.nspname='truss' AND c.relname LIKE 'journal%' AND NOT t.tgisinternal
             AND t.tgname='runtime_owned_journal_insert_commit'""").fetchone()[0]
        self.assertEqual(journal_guards, 0)

        for index, relation in enumerate(relation_names):
            with self.subTest(relation='.'.join(relation)):
                savepoint = f'direct_private_insert_{index}'
                connection.execute(sql.SQL('SAVEPOINT {}').format(sql.Identifier(savepoint)))
                with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                    connection.execute(sql.SQL('INSERT INTO {} DEFAULT VALUES').format(sql.Identifier(*relation)))
                connection.execute(sql.SQL('ROLLBACK TO SAVEPOINT {}').format(sql.Identifier(savepoint)))
                connection.execute(sql.SQL('RELEASE SAVEPOINT {}').format(sql.Identifier(savepoint)))
