"""Native protected enrollment component; no invocation authentication claim."""
import psycopg
import test_group_create_native as base
from truss import Ok, Error, adopt_psycopg_host
from truss._action_subject_installation import bootstrap_action_subjects_in_transaction


class ActionSubjectInstallationNativeTests(base.PublicCreateGroupTests):
    for name in tuple(n for n in dir(base.PublicCreateGroupTests) if n.startswith('test_')):
        locals()[name] = None

    def test_private_explicit_subject_kind_and_original_commit(self):
        data, old_host, assembly, old_tx = self.ready(document_ids=('adoc',))
        old_host.detach(); data.commit()
        self.admin.execute('CREATE ROLE action_service LOGIN')
        self.addCleanup(self.admin.execute, 'DROP ROLE action_service')
        self.admin.execute('BEGIN')
        host = adopt_psycopg_host(self.admin); tx = host.adopt_transaction().value
        result = bootstrap_action_subjects_in_transaction(host, tx,
            bindings=(('consumer', b'original-human-identity', 'human'),
                      ('action_service', b'original-service-identity', 'service')))
        self.assertIsInstance(result, Ok, str(host._custody.last_attempt.error))
        self.assertFalse(result.value.security_ready)
        host.detach(); self.admin.commit()
        self.assertEqual(self.admin.execute('SELECT subject_kind,principal_identity FROM truss.action_subject_binding ORDER BY subject_kind').fetchall(),
            [('human', b'original-human-identity'), ('service', b'original-service-identity')])
        for statement in ('SELECT * FROM truss.action_subject_binding',
                          "UPDATE truss.action_subject_binding SET subject_kind='human'",
                          'DELETE FROM truss.action_subject_binding',
                          "INSERT INTO truss.action_subject_binding SELECT * FROM truss.action_subject_binding"):
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                data.execute(statement)
        self.admin.execute('BEGIN')
        host = adopt_psycopg_host(self.admin); tx = host.adopt_transaction().value
        duplicate = bootstrap_action_subjects_in_transaction(host, tx,
            bindings=(('consumer', b'rebound-without-migration', 'human'),))
        self.assertIsInstance(duplicate, Error)
        host.detach(); self.admin.rollback()
        self.assertEqual(self.admin.execute("SELECT principal_identity FROM truss.action_subject_binding WHERE subject_kind='human'").fetchone(), (b'original-human-identity',))
