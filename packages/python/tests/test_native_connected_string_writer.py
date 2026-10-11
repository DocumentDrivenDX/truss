"""Real pending native effects only; no accepted catalog or ordinary authority."""
from pathlib import Path
import json
import unittest
from test_native_pg8000 import NativeBoundaryFixture

class NativeConnectedStringWriterTests(NativeBoundaryFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        root=Path(__file__).resolve().parents[3]
        self.connection.run('BEGIN')
        for path in ('docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql',
          'packages/postgresql/native/row-image/codec.sql',
          'packages/postgresql/native/row-image/prestate.sql',
          'packages/postgresql/native/row-image/state-owner.sql',
          'packages/postgresql/native/row-image/dependent-owner.sql',
          'packages/postgresql/native/row-image/string-candidate.sql',
          'packages/postgresql/native/issued-operation-admission/operation-admission.sql'):
            self.connection.run((root/path).read_text())
        # Native catalog fixture is not accepted UMF evidence. All actual FKs
        # remain enabled; runtime writes are measured with the ALWAYS observer.
        self.connection.run("INSERT INTO truss.schema_doc VALUES(0,0,'native-fixture','0','fixture','fixture','{}','{}')")
        self.connection.run("INSERT INTO truss.type_def(document_id,type_id,module,element,kind,since_rev,doc_ord,lineage_profile,lineage_bytes,definition_source_kind,definition_rev,definition_doc_ord,definition_document_id) VALUES('native-fixture',2,'test','item','entity',0,0,'native-fixture',decode('01','hex'),'accepted_document',0,0,'native-fixture')")
        self.connection.run("INSERT INTO truss.prop_def(prop_id,type_id,element,name,scalar_type,nullability,cardinality,home,since_rev,doc_ord,definition_source_kind,definition_rev,definition_doc_ord,definition_document_id,declaration_module) VALUES(301,2,'note','note','string','nullable','one','row',0,0,'accepted_document',0,0,'native-fixture','test')")
        self.connection.run('INSERT INTO truss.object(id,type_id,rev) VALUES(100,2,0)')
        self.connection.run("INSERT INTO truss.row_home_state VALUES(501,'object',100,2,NULL,NULL,2,301,601,decode('01','hex'),decode('02','hex'),decode('03','hex'),decode('04','hex'))")
        self.connection.run("INSERT INTO truss.row_home_node VALUES(501,601,NULL,'root',NULL,NULL,NULL,'scalar',decode('05','hex'),decode('06','hex'))")
        self.connection.run("INSERT INTO truss.row_home_scalar VALUES(501,601,'string','value',NULL,NULL,NULL,NULL,NULL,NULL,NULL,decode('07','hex'),decode('08','hex'))")
        self.connection.run('SET CONSTRAINTS ALL IMMEDIATE')
        for path in ('packages/postgresql/native/existing-string-writer/pending-effects.sql',
                     'packages/postgresql/native/operation-commit-barrier.sql'):
            self.connection.run((root/path).read_text())
        self.connection.run('SET CONSTRAINTS ALL DEFERRED')

    def _write(self, text='new ☃', token=None, version=1, ordinal=0):
        token=json.dumps(text,ensure_ascii=False).encode() if token is None else token
        return self.connection.run('SELECT * FROM truss.runtime_write_existing_string_pending('
            ':ordinal,501,:version,:text,decode(:token,\'hex\'))',
            ordinal=ordinal,version=version,text=text,token=token.hex())[0]

    def test_real_pending_write_retains_old_new_and_exact_token(self):
        token=b'"new \\u2603"'
        row=self._write(token=token)
        self.assertEqual(row[1],'0')
        self.assertEqual(self.connection.run('SELECT text_value,original_source_bytes FROM truss.row_home_scalar'),[['new ☃',token]])
        self.assertEqual(self.connection.run('SELECT ver::text FROM truss.object'),[['2']])
        self.assertEqual(self.connection.run('SELECT phase,effect_generation::text FROM truss.row_home_operation'),[['admitted','1']])
        before,after=(json.loads(bytes(value)) for value in row[2:])
        self.assertEqual(before['version'],'1');self.assertEqual(after['version'],'2')
        for name in ('stateHex','nodeHex'):self.assertEqual(before[name],after[name])
        self.assertNotEqual(before['scalarHex'],after['scalarHex'])
        # Raw commit is refused. No fixture phase mutation turns this pending
        # effect component into an accepted installation or durable operation.
        from pg8000.exceptions import DatabaseError
        with self.assertRaises(DatabaseError):self.connection.run('COMMIT')

    def test_equal_value_still_records_event_and_version(self):
        self._write('value',b'"value"')
        self.assertEqual(self.connection.run('SELECT ver::text FROM truss.object'),[['2']])
        self.assertEqual(self.connection.run('SELECT effect_generation::text FROM truss.row_home_operation'),[['1']])

    def test_refusals_preserve_prior_host_work(self):
        from pg8000.exceptions import DatabaseError
        self.connection.run('CREATE TABLE public.host_sentinel(value text)')
        self.connection.run("INSERT INTO public.host_sentinel VALUES('prior')")
        for args in ({'version':2},{'token':b'"different"'},{'token':b'123'}, {'version':9223372036854775807}):
            self.connection.run('SAVEPOINT operation')
            with self.assertRaises(DatabaseError):self._write(**args)
            self.connection.run('ROLLBACK TO SAVEPOINT operation');self.connection.run('RELEASE SAVEPOINT operation')
            self.assertEqual(self.connection.run('SELECT value FROM public.host_sentinel'),[['prior']])
            self.assertEqual(self.connection.run('SELECT ver::text FROM truss.object'),[['1']])
            self.assertEqual(self.connection.run('SELECT count(*) FROM truss.row_home_operation'),[[0]])

    def test_late_foreign_scalar_event_refuses_and_rolls_back_writer(self):
        from pg8000.exceptions import DatabaseError
        self.connection.run('SAVEPOINT operation')
        self._write()
        with self.assertRaises(DatabaseError):
            self.connection.run("UPDATE truss.row_home_scalar SET text_value='late'")
        self.connection.run('ROLLBACK TO SAVEPOINT operation')
        self.assertEqual(self.connection.run('SELECT text_value FROM truss.row_home_scalar'),[['value']])
        self.assertEqual(self.connection.run('SELECT ver::text FROM truss.object'),[['1']])
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.row_home_operation'),[[0]])

    def test_missing_observer_refuses_and_restores_attempt(self):
        from pg8000.exceptions import DatabaseError
        self.connection.run('ALTER TABLE truss.row_home_scalar DISABLE TRIGGER runtime_existing_string_pending_scalar')
        self.connection.run('SAVEPOINT operation')
        with self.assertRaises(DatabaseError): self._write()
        self.connection.run('ROLLBACK TO SAVEPOINT operation')
        self.assertEqual(self.connection.run('SELECT ver::text FROM truss.object'), [['1']])
        self.assertEqual(self.connection.run('SELECT text_value FROM truss.row_home_scalar'), [['value']])
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.row_home_operation'), [[0]])

    def test_object_rewrite_refuses_and_restores_attempt(self):
        from pg8000.exceptions import DatabaseError
        self.connection.run("CREATE FUNCTION public.rewrite_object() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN NEW.ver:=NEW.ver+1; RETURN NEW; END $$")
        self.connection.run('CREATE TRIGGER rewrite_object BEFORE UPDATE ON truss.object FOR EACH ROW EXECUTE FUNCTION public.rewrite_object()')
        self.connection.run('SAVEPOINT operation')
        with self.assertRaises(DatabaseError): self._write()
        self.connection.run('ROLLBACK TO SAVEPOINT operation')
        self.assertEqual(self.connection.run('SELECT ver::text FROM truss.object'), [['1']])
        self.assertEqual(self.connection.run('SELECT text_value FROM truss.row_home_scalar'), [['value']])
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.row_home_operation'), [[0]])

    def test_late_parent_rewrite_refuses_and_restores_attempt(self):
        from pg8000.exceptions import DatabaseError
        before=self.connection.run('SELECT truss.row_image_node_original(n) FROM truss.row_home_node n')
        self.connection.run("CREATE FUNCTION public.rewrite_parent() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN UPDATE truss.row_home_node SET source_bytes=decode('99','hex'); RETURN NULL; END $$")
        self.connection.run('CREATE TRIGGER rewrite_parent AFTER UPDATE ON truss.object FOR EACH ROW EXECUTE FUNCTION public.rewrite_parent()')
        self.connection.run('SAVEPOINT operation')
        with self.assertRaises(DatabaseError): self._write()
        self.connection.run('ROLLBACK TO SAVEPOINT operation')
        self.assertEqual(self.connection.run('SELECT truss.row_image_node_original(n) FROM truss.row_home_node n'), before)
        self.assertEqual(self.connection.run('SELECT ver::text FROM truss.object'), [['1']])
        self.assertEqual(self.connection.run('SELECT text_value FROM truss.row_home_scalar'), [['value']])
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.row_home_operation'), [[0]])
