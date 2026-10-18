import unittest
import psycopg
import test_catalog_runtime_native as catalog_tests


class StringKeyBucketNativeTests(catalog_tests.PublicCatalogRuntimeTests):
    def setUp(self):
        super().setUp();self.install()
        # Exercise the installed protected helper, not the predecessor fixture SQL.
        self.namespace=b'private-test-namespace'
        self.key=b'umf-key-tuple-v1:hex:554d464b3101040178'

    def lock(self,connection=None):
        return (self.admin if connection is None else connection).execute(
            'SELECT * FROM truss.lock_string_key_bucket(%s,%s)',(self.namespace,self.key)).fetchone()

    def test_exact_reservation_facts_and_caller_rollback(self):
        self.admin.execute('BEGIN')
        self.assertEqual(self.lock(),(0,[],[]))
        identity=self.admin.execute('''INSERT INTO truss.object_key_reservation_bucket(namespace_bytes,key_bytes,original_reservation_bytes)
          VALUES(%s,%s,convert_to(jsonb_build_object('xid',pg_current_xact_id()::text,'fixture',%s)::text,'UTF8')) RETURNING storage_row_id''',(self.namespace,self.key,b'private fixture reservation')).fetchone()[0]
        self.assertEqual(self.lock(),(0,[],[identity]))
        self.admin.rollback()
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.key_bucket_guard').fetchone(),(0,))
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object_key_reservation_bucket').fetchone(),(0,))

    def test_first_creator_contention_refuses_and_committed_facts_are_visible(self):
        params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri)
        with psycopg.connect(**params,autocommit=True,options='-c statement_timeout=10000') as contender:
            self.admin.execute('BEGIN');self.assertEqual(self.lock(),(0,[],[]))
            contender.execute('BEGIN')
            with self.assertRaises(psycopg.errors.LockNotAvailable):self.lock(contender)
            contender.rollback()
            identity=self.admin.execute('''INSERT INTO truss.object_key_reservation_bucket(namespace_bytes,key_bytes,original_reservation_bytes)
              VALUES(%s,%s,convert_to(jsonb_build_object('xid',pg_current_xact_id()::text,'fixture',%s)::text,'UTF8')) RETURNING storage_row_id''',(self.namespace,self.key,b'private fixture reservation')).fetchone()[0]
            self.admin.commit()
            contender.execute('BEGIN')
            self.assertEqual(self.lock(contender),(0,[],[identity]))
            contender.rollback()

    def test_fixed_snapshot_refuses(self):
        self.admin.execute('BEGIN ISOLATION LEVEL REPEATABLE READ')
        with self.assertRaises(psycopg.errors.FeatureNotSupported):self.lock()
        self.admin.rollback()

    def test_existing_native_guard_contention_refuses(self):
        self.lock()
        params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri)
        with psycopg.connect(**params,autocommit=True,options='-c statement_timeout=10000') as holder:
            holder.execute('BEGIN')
            holder.execute('SELECT * FROM truss.key_bucket_guard FOR UPDATE')
            self.admin.execute('BEGIN')
            with self.assertRaises(psycopg.errors.LockNotAvailable):self.lock()
            self.admin.rollback();holder.rollback()
        self.assertEqual(self.lock(),(0,[],[]))

    def test_same_active_read_committed_transaction_observes_new_claim(self):
        params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri)
        with psycopg.connect(**params,autocommit=True) as reader:
            reader.execute('BEGIN')
            xid=reader.execute('SELECT pg_current_xact_id()::text').fetchone()[0]
            self.assertEqual(reader.execute('SELECT count(*) FROM truss.key_bucket_guard').fetchone(),(0,))
            self.admin.execute('BEGIN');self.lock()
            identity=self.admin.execute('''INSERT INTO truss.object_key_reservation_bucket(namespace_bytes,key_bytes,original_reservation_bytes)
              VALUES(%s,%s,convert_to(jsonb_build_object('xid',pg_current_xact_id()::text,'fixture',%s)::text,'UTF8')) RETURNING storage_row_id''',(self.namespace,self.key,b'fixture')).fetchone()[0]
            self.admin.commit()
            self.assertEqual(self.lock(reader),(0,[],[identity]))
            self.assertEqual(reader.execute('SELECT pg_current_xact_id()::text').fetchone()[0],xid)
            reader.rollback()

    def test_bucket_overflow_is_not_an_empty_observation(self):
        self.lock()
        self.admin.execute('''INSERT INTO truss.object_key_reservation_bucket(namespace_bytes,key_bytes,original_reservation_bytes)
          SELECT %s,%s,convert_to(jsonb_build_object('xid',pg_current_xact_id()::text,'fixture',%s)::text,'UTF8') FROM generate_series(1,10001)''',(self.namespace,self.key,b'private fixture reservation'))
        self.admin.execute('BEGIN')
        with self.assertRaises(psycopg.errors.ProgramLimitExceeded):self.lock()
        self.admin.rollback()

    def test_suppressed_guard_creation_and_private_execution_refuse(self):
        self.admin.execute("""CREATE FUNCTION truss.fixture_suppress_guard() RETURNS trigger LANGUAGE plpgsql AS $$
          BEGIN RETURN NULL; END $$;
          CREATE TRIGGER fixture_suppress_guard BEFORE INSERT ON truss.key_bucket_guard
          FOR EACH ROW EXECUTE FUNCTION truss.fixture_suppress_guard()""")
        self.admin.execute('BEGIN')
        with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState):self.lock()
        self.admin.rollback()
        self.admin.execute('DROP TRIGGER fixture_suppress_guard ON truss.key_bucket_guard')
        self.admin.execute('DROP FUNCTION truss.fixture_suppress_guard()')
        params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);params['user']='consumer'
        with psycopg.connect(**params,autocommit=True) as consumer:
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):self.lock(consumer)

    def test_rewritten_guard_creation_refuses_without_resetting_existing_generation(self):
        self.admin.execute("""CREATE FUNCTION truss.fixture_rewrite_guard() RETURNS trigger LANGUAGE plpgsql AS $$
          BEGIN NEW.generation:=7; RETURN NEW; END $$;
          CREATE TRIGGER fixture_rewrite_guard BEFORE INSERT ON truss.key_bucket_guard
          FOR EACH ROW EXECUTE FUNCTION truss.fixture_rewrite_guard()""")
        self.admin.execute('BEGIN')
        with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState):self.lock()
        self.admin.rollback()
        self.admin.execute('DROP TRIGGER fixture_rewrite_guard ON truss.key_bucket_guard')
        self.admin.execute('DROP FUNCTION truss.fixture_rewrite_guard()')
        self.lock();self.admin.execute('UPDATE truss.key_bucket_guard SET generation=7')
        self.assertEqual(self.lock(),(7,[],[]))

    def test_complete_candidate_byte_budget_refuses(self):
        self.namespace=b'n'*65536;self.key=b'umf-key-tuple-v1:hex:'+b'00'*500000
        self.lock()
        self.admin.execute('''INSERT INTO truss.object_key_reservation_bucket(namespace_bytes,key_bytes,original_reservation_bytes)
          SELECT %s,%s,convert_to(jsonb_build_object('xid',pg_current_xact_id()::text,'fixture',%s)::text,'UTF8') FROM generate_series(1,16)''',(self.namespace,self.key,b'fixture'))
        self.admin.execute('BEGIN')
        with self.assertRaises(psycopg.errors.ProgramLimitExceeded):self.lock()
        self.admin.rollback()

    def test_rls_cannot_turn_hidden_reservation_into_empty_bucket(self):
        self.lock()
        self.admin.execute('''INSERT INTO truss.object_key_reservation_bucket(namespace_bytes,key_bytes,original_reservation_bytes)
          VALUES(%s,%s,convert_to(jsonb_build_object('xid',pg_current_xact_id()::text,'fixture',%s)::text,'UTF8'))''',(self.namespace,self.key,b'fixture'))
        self.admin.execute("""ALTER TABLE truss.object_key_reservation_bucket ENABLE ROW LEVEL SECURITY;
          CREATE POLICY fixture_hidden ON truss.object_key_reservation_bucket USING(false);
          GRANT SELECT ON truss.object_key_bucket,truss.object_key_reservation_bucket TO consumer;
          GRANT SELECT,UPDATE ON truss.key_bucket_guard TO consumer;
          GRANT EXECUTE ON FUNCTION truss.lock_string_key_bucket(bytea,bytea) TO consumer""")
        params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);params['user']='consumer'
        with psycopg.connect(**params,autocommit=True) as consumer:
            self.assertEqual(consumer.execute('SELECT count(*) FROM truss.object_key_reservation_bucket').fetchone(),(0,))
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):self.lock(consumer)


for _name in tuple(vars(catalog_tests.PublicCatalogRuntimeTests)):
    if _name.startswith('test_'):setattr(StringKeyBucketNativeTests,_name,None)

if __name__=='__main__':unittest.main()
