"""Actual EL multiset body under administrative test custody, not public admission."""
import json
from pathlib import Path
import unittest
from test_native_pg8000 import NativeBoundaryFixture
ROOT=Path(__file__).resolve().parents[3]
SQL=ROOT/'packages/postgresql/native/edge-limit/verify-current-scope.sql'

class NativeEdgeLimitTests(NativeBoundaryFixture,unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        connection=cls.Connection(**cls.kwargs)
        try:
            connection.run((ROOT/'docs/helix/04-build/evidence/qualified-property-layout-0.15.owner-export.sql').read_text())
            connection.run(SQL.read_text())
            connection.run('CREATE ROLE truss_el_ordinary')
            connection.run('GRANT USAGE ON SCHEMA truss TO truss_el_ordinary')
        finally:connection.close()
    def setUp(self):
        self.connection=self.Connection(**self.kwargs)
        self.connection.run('BEGIN')
        self.connection.run('LOCK TABLE truss.schema_head IN EXCLUSIVE MODE')
        self.admit()
        self.connection.run("INSERT INTO truss.schema_doc VALUES(0,0,'synthetic','fixture','0.7.0','fixture-only','{}','{}')")
    def tearDown(self):
        self.connection.run('ROLLBACK');self.connection.close()
    def admit(self,ordinal=0,kind='catalog-acceptance'):
        self.connection.run("""INSERT INTO truss.row_home_operation
          (original_writer_xid,operation_ordinal,operation_kind,phase,effect_generation,
           original_context_bytes,original_definition_bytes,original_input_bytes,
           original_prestate_bytes,admitted_candidate_bytes,effect_obligation_bytes,original_group_custody_bytes)
          VALUES(pg_current_xact_id(),:ordinal,:kind,'admitted',0,
           'native-test','native-test','native-test','native-test','native-test','native-test','native-test')""",ordinal=ordinal,kind=kind)
    def verify(self):self.connection.run('SELECT truss.edge_limit_verify_current_scope()')
    def seed(self,definitions,edges,markers):
        # Administrative corruption/fixture setup only: no protected/accepted IDs
        # or owner authority is inferred from these synthetic native rows.
        self.connection.run("SET LOCAL session_replication_role='replica'")
        for d in definitions:
            self.connection.run("""INSERT INTO truss.rel_def(document_id,rel_type_id,module,rel_id,name,
              source_min,source_max,target_min,target_max,lifecycle,directed,since_rev,doc_ord,
              definition_source_kind,definition_rev,definition_doc_ord,definition_document_id)
              VALUES('synthetic',:id,'m',:name,:name,0,:s,0,:t,'independent',true,0,0,'accepted_document',0,0,'synthetic')""",
              id=int(d['relationshipId']),name='r'+d['relationshipId'],
              s=None if d['sourceMax'] in ('*',None) else int(d['sourceMax']),
              t=None if d['targetMax'] in ('*',None) else int(d['targetMax']))
        for e in edges:
            self.connection.run("""INSERT INTO truss.edge(id,rel_type_id,source_id,source_type,target_id,target_type,rev)
              VALUES(:id,:r,:s,1,:t,1,0)""",id=int(e['id']),r=int(e['relationshipId']),s=int(e['sourceId']),t=int(e['targetId']))
        for m in markers:
            self.connection.run('INSERT INTO truss.edge_limit VALUES(:r,:side,:endpoint,:edge)',r=int(m['relationshipId']),side=m['side'],endpoint=int(m['endpointId']),edge=int(m['edgeId']))
        self.connection.run("SET LOCAL session_replication_role='origin'")
    def refused(self,code):
        from pg8000.exceptions import DatabaseError
        self.connection.run('SAVEPOINT expected_refusal')
        with self.assertRaises(DatabaseError) as raised:self.verify()
        self.assertEqual(raised.exception.args[0]['C'],code)
        self.connection.run('ROLLBACK TO expected_refusal')
    def test_eleven_original_vectors(self):
        vectors=json.loads((ROOT/'docs/helix/02-design/contracts/bindings/edge-limit-correspondence-v0.1.vectors.json').read_text())['vectors']
        self.assertEqual(len(vectors),11)
        for vector in vectors:
            with self.subTest(vector=vector['name']):
                self.connection.run('SAVEPOINT vector')
                if vector['name']=='duplicated raw marker occurrence is not deduplicated':
                    # Explicit administrative corruption probe: isolate multiset
                    # validation after removing the PK that normally prevents it.
                    self.connection.run('ALTER TABLE truss.edge_limit DROP CONSTRAINT edge_limit_pkey')
                self.seed(vector['definitions'],vector['edges'],vector['actualMarkers'])
                outcome=vector['expectedOutcome']
                if outcome=='correspondence':self.verify()
                else:self.refused('23505' if outcome=='required_key_conflict' else '55000')
                self.connection.run('ROLLBACK TO vector')
    def test_actual_installed_body_and_selected_attributes(self):
        row=self.connection.run("""SELECT p.prosrc,p.provolatile,p.proparallel,p.prosecdef,
          p.pronargs,p.prorettype='void'::regtype,l.lanname,p.proconfig,p.proowner::regrole::text,
          has_function_privilege('truss_el_ordinary',p.oid,'EXECUTE')
          FROM pg_proc p JOIN pg_language l ON l.oid=p.prolang
          WHERE p.oid='truss.edge_limit_verify_current_scope()'::regprocedure""")[0]
        self.assertEqual(row[0],SQL.read_text().split('AS $$',1)[1].split('$$;',1)[0])
        self.assertEqual(tuple(row[1:7]),('v','u',True,0,True,'plpgsql'))
        self.assertEqual(row[7],['search_path=pg_catalog, pg_temp','row_security=off'])
        self.assertEqual(row[8],'postgres');self.assertFalse(row[9])

    def test_empty_scope_no_mutation(self):
        before=self.connection.run('SELECT to_jsonb(o)::text FROM truss.row_home_operation o')
        self.verify();self.verify()
        self.assertEqual(before,self.connection.run('SELECT to_jsonb(o)::text FROM truss.row_home_operation o'))
    def test_retired_definition_is_not_filtered(self):
        self.seed([{'relationshipId':'1','sourceMax':'*','targetMax':'1'}],[{'id':'10','relationshipId':'1','sourceId':'100','targetId':'200'}],[])
        self.connection.run('UPDATE truss.rel_def SET retired_rev=0');self.refused('55000')
    def test_catalog_tightening_without_property_touches(self):
        self.seed([{'relationshipId':'1','sourceMax':'*','targetMax':'*'}],[{'id':'10','relationshipId':'1','sourceId':'100','targetId':'200'}],[])
        self.verify();self.connection.run('SAVEPOINT tightening')
        self.connection.run('UPDATE truss.rel_def SET target_max=1');self.refused('55000')
        self.connection.run('ROLLBACK TO tightening');self.verify()
    def test_wrong_or_orphan_relationship_marker(self):
        self.seed([{'relationshipId':'1','sourceMax':'*','targetMax':'1'}],[{'id':'10','relationshipId':'1','sourceId':'100','targetId':'200'}],[{'relationshipId':'99','side':'s','endpointId':'100','edgeId':'10'}])
        self.refused('55000')
    def test_signed_relationship_ids(self):
        self.seed([{'relationshipId':'-1','sourceMax':'*','targetMax':'1'},
                   {'relationshipId':'0','sourceMax':'*','targetMax':'*'}],
                  [{'id':'10','relationshipId':'-1','sourceId':'100','targetId':'200'}],
                  [{'relationshipId':'-1','side':'s','endpointId':'100','edgeId':'10'}])
        self.verify()
    def test_column_type_and_nullability_drift_refuses(self):
        self.connection.run('SAVEPOINT drift')
        self.connection.run('ALTER TABLE truss.edge_limit ALTER COLUMN side TYPE char(2)')
        self.refused('0A000');self.connection.run('ROLLBACK TO drift')
        self.connection.run('ALTER TABLE truss.rel_def ALTER COLUMN source_max TYPE bigint')
        self.refused('0A000');self.connection.run('ROLLBACK TO drift')
        self.connection.run('ALTER TABLE truss.edge_limit DROP CONSTRAINT edge_limit_pkey')
        self.connection.run('ALTER TABLE truss.edge_limit ALTER COLUMN endpoint_id DROP NOT NULL')
        self.refused('0A000')

    def test_numeric_marker_relationship_cannot_round_into_identity(self):
        self.seed([{'relationshipId':'1','sourceMax':'*','targetMax':'1'}],
                  [{'id':'10','relationshipId':'1','sourceId':'100','targetId':'200'}],
                  [{'relationshipId':'1','side':'s','endpointId':'100','edgeId':'10'}])
        self.verify()
        self.connection.run('ALTER TABLE truss.edge_limit ALTER COLUMN rel_type_id TYPE numeric')
        self.connection.run('UPDATE truss.edge_limit SET rel_type_id=1.4')
        self.refused('0A000')

    def test_invalid_bounds(self):
        self.seed([{'relationshipId':'1','sourceMax':'*','targetMax':'-1'}],[],[]);self.refused('0A000')
    def test_ambiguous_operation_refuses(self):
        # Explicit index-corruption probe, not an admitted installed profile.
        self.connection.run('DROP INDEX truss.row_home_operation_unfinished_xid')
        self.admit(ordinal=1);self.refused('P0003')
    def test_unknown_phase_refuses(self):
        self.connection.run('ALTER TABLE truss.row_home_operation DROP CONSTRAINT row_home_operation_phase')
        self.connection.run("UPDATE truss.row_home_operation SET phase='unknown'")
        self.refused('55000')
    def test_duplicate_native_definition_identity_refuses(self):
        # Drop referential dependents only in an isolated corruption probe.
        self.connection.run('ALTER TABLE truss.rel_def DROP CONSTRAINT rel_def_pkey CASCADE')
        definitions=[{'relationshipId':'1','sourceMax':'*','targetMax':'*'}]
        self.seed(definitions,[],[])
        self.connection.run("SET LOCAL session_replication_role='replica'")
        self.connection.run('INSERT INTO truss.rel_def SELECT * FROM truss.rel_def')
        self.connection.run("SET LOCAL session_replication_role='origin'")
        self.refused('0A000')

    def test_wrong_operation_refuses(self):
        self.connection.run("UPDATE truss.row_home_operation SET operation_kind='mutation'");self.refused('55000')
    def test_missing_exclusion_refuses(self):
        self.connection.run('ROLLBACK');self.connection.run('BEGIN');self.admit();self.refused('55000')
    def test_scope_boundary(self):
        self.connection.run("SET LOCAL session_replication_role='replica'")
        self.connection.run("""INSERT INTO truss.rel_def(document_id,rel_type_id,module,rel_id,name,source_min,target_min,lifecycle,directed,since_rev,doc_ord,definition_source_kind,definition_rev,definition_doc_ord,definition_document_id)
          SELECT 'synthetic',n,'m',n::text,n::text,0,0,'independent',true,0,0,'accepted_document',0,0,'synthetic' FROM generate_series(1,256) n""")
        self.connection.run("SET LOCAL session_replication_role='origin'");self.verify()
        self.connection.run("SET LOCAL session_replication_role='replica'")
        self.connection.run("INSERT INTO truss.rel_def(document_id,rel_type_id,module,rel_id,name,source_min,target_min,lifecycle,directed,since_rev,doc_ord,definition_source_kind,definition_rev,definition_doc_ord,definition_document_id) VALUES('synthetic',257,'m','257','257',0,0,'independent',true,0,0,'accepted_document',0,0,'synthetic')")
        self.connection.run("SET LOCAL session_replication_role='origin'");self.refused('54000')
    def test_edge_and_marker_row_boundaries(self):
        self.seed([{'relationshipId':'1','sourceMax':'1','targetMax':'1'}],[],[])
        self.connection.run("SET LOCAL session_replication_role='replica'")
        self.connection.run("""INSERT INTO truss.edge(id,rel_type_id,source_id,source_type,target_id,target_type,rev)
          SELECT n,1,n,1,n,1,0 FROM generate_series(1,16384) n""")
        self.connection.run("INSERT INTO truss.edge_limit SELECT 1,'s',id,id FROM truss.edge UNION ALL SELECT 1,'t',id,id FROM truss.edge")
        self.connection.run("SET LOCAL session_replication_role='origin'");self.verify()
        self.connection.run('SAVEPOINT excess_marker')
        self.connection.run("INSERT INTO truss.edge_limit VALUES(1,'s',999999,1)");self.refused('54000')
        self.connection.run('ROLLBACK TO excess_marker')
        self.connection.run("SET LOCAL session_replication_role='replica'")
        self.connection.run("INSERT INTO truss.edge(id,rel_type_id,source_id,source_type,target_id,target_type,rev) VALUES(16385,1,16385,1,16385,1,0)")
        self.connection.run("SET LOCAL session_replication_role='origin'");self.refused('54000')

    def test_ordinary_direct_call_denied(self):
        self.connection.run('SET LOCAL ROLE truss_el_ordinary');self.refused('42501')
        self.connection.run('RESET ROLE')
    def test_concurrent_shared_head_writer_excluded(self):
        from pg8000.exceptions import DatabaseError
        other=self.Connection(**self.kwargs)
        try:
            other.run('BEGIN');other.run("SET LOCAL lock_timeout='100ms'")
            with self.assertRaises(DatabaseError) as raised:other.run('SELECT * FROM truss.schema_head WHERE id=1 FOR SHARE')
            self.assertEqual(raised.exception.args[0]['C'],'55P03')
        finally:other.run('ROLLBACK');other.close()
    def test_nondeterministic_side_collation_does_not_fold_marker(self):
        from pg8000.exceptions import DatabaseError
        self.connection.run('SAVEPOINT optional_icu')
        try:self.connection.run("CREATE COLLATION truss.el_nocase(provider=icu,locale='und-u-ks-level1',deterministic=false)")
        except DatabaseError as error:
            self.connection.run('ROLLBACK TO optional_icu')
            if error.args[0]['C']=='0A000':self.skipTest('Selected local PostgreSQL build lacks ICU')
            raise
        self.connection.run('ALTER TABLE truss.edge_limit ALTER COLUMN side TYPE char(1) COLLATE truss.el_nocase')
        self.seed([{'relationshipId':'1','sourceMax':'*','targetMax':'1'}],
                  [{'id':'10','relationshipId':'1','sourceId':'100','targetId':'200'}],
                  [{'relationshipId':'1','side':'S','endpointId':'100','edgeId':'10'}])
        self.refused('55000')

    def test_concurrent_catalog_writer_excluded(self):
        from pg8000.exceptions import DatabaseError
        other=self.Connection(**self.kwargs)
        try:
            other.run('BEGIN');other.run("SET LOCAL lock_timeout='100ms'")
            with self.assertRaises(DatabaseError) as raised:other.run('LOCK TABLE truss.schema_head IN EXCLUSIVE MODE')
            self.assertEqual(raised.exception.args[0]['C'],'55P03')
        finally:other.run('ROLLBACK');other.close()
