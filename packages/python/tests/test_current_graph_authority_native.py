"""Actual SCRAM public Graph reads under trusted administrative quiescence.

No diagnostic source substitution; not concurrent privileged-DDL qualification.
"""
import hashlib,json,os,unittest
import psycopg
import truss._current_query_runtime as runtime
from pathlib import Path
from truss import (Ok,Error,CurrentDisclosureExecutor,CurrentDisclosureRows,adopt_psycopg_host,
    prepare_current_disclosure_originals,register_current_disclosure_sources_in_transaction,
    activate_current_query_protection_in_transaction,ModuleAccessGrant)
from truss._current_query_subjects import register_current_query_subjects_in_transaction
from truss._current_query_protection import _GRAPH_PROFILE
import test_current_disclosure_scram_native as scram
import test_current_disclosure_graphs_native as graph
from test_group_create_native import PublicCreateGroupTests
wire=graph.wire
ROOT=Path(__file__).resolve().parents[3]/'docs/helix/04-build/evidence/actual-graph-requirements-20261016'


@unittest.skipUnless(os.environ.get('TRUSS_GRAPH_AUTHORITY_NATIVE_QUALIFICATION')=='1',
                     'explicit serialized quiescent-admin Graph qualification required')
class CurrentGraphAuthorityNativeTests(scram.CurrentDisclosureScramNativeTests):
    for name in tuple(n for n in dir(scram.CurrentDisclosureScramNativeTests) if n.startswith('test_')):
        locals()[name]=None
    ready=PublicCreateGroupTests.ready
    apply=PublicCreateGroupTests.apply
    _create_public_population=graph.NativeGraphCaptureTests._create_public_population

    def prepare_graph(self,staff,parallel=False):
        initial,accepted,_,_,_,_,_,_=self._create_public_population(parallel)
        request=json.loads((ROOT/'original-request.json').read_bytes());request['modules']=json.loads(accepted)['modules']
        for m in request['modules']:m['selectedModuleIds']=['m']
        for row in request['opaqueSources']:
            role=row['role']
            if role in ('policy','ontology','catalog','owner'):
                source=initial['owner'] if role=='owner' else initial['sources'][role]
                row['utf8']=wire(source).decode();row['sha256']=hashlib.sha256(row['utf8'].encode()).hexdigest()
                row['identity']={'documentId':source.get('id',source.get('documentId')),'revision':source['revision']}
        designation=next(r for r in request['opaqueSources'] if r['role']=='presence-designation');profile=json.loads(designation['utf8'])
        profile['modelPins']=[m['pin'] for m in request['modules']]
        profile['sources']=[{k:r[k] for k in ('role','identity','sha256')} for r in request['opaqueSources'] if r['role'] in ('policy','ontology','catalog','owner')]
        designation['utf8']=wire(profile).decode();designation['sha256']=hashlib.sha256(designation['utf8'].encode()).hexdigest()
        registered=wire({'kind':'initialize','requestId':'registered','sources':{**initial['sources'],'extensionSelection':None}})
        originals=prepare_current_disclosure_originals(wire(request['opaqueSources']))
        for c,h in self.consumer_connections:
            if not c.closed:h.detach();c.rollback();c.close()
        self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin,operation_timeout_ms=30000);self.tx=self.host.adopt_transaction().value
        source=register_current_disclosure_sources_in_transaction(self.host,self.tx,initialize_bytes=registered,accepted_request_bytes=accepted,disclosure_originals=originals)
        self.assertIsInstance(source,Ok,str(self.host._custody.last_attempt.error))
        enrolled=register_current_query_subjects_in_transaction(self.host,self.tx,bindings=(('consumer',staff),))
        self.assertIsInstance(enrolled,Ok,str(self.host._custody.last_attempt.error));self.registration=enrolled.value
        self.host.detach();self.admin.commit()
        self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin,operation_timeout_ms=30000);self.tx=self.host.adopt_transaction().value
        activated=activate_current_query_protection_in_transaction(self.host,self.tx,subject_registration=self.registration)
        self.assertIsInstance(activated,Ok,str(self.host._custody.last_attempt.error));self.host.detach();self.admin.commit()
        marker=json.loads(self.admin.execute('SELECT truss.current_query_protection_marker()').fetchone()[0])
        self.assertEqual(marker['profile'],_GRAPH_PROFILE)
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(14,))
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.edge').fetchone(),(13 if parallel else 12,))

    def public_graph(self,staff,expected,*,parallel=False):
        self.prepare_graph(staff,parallel)
        self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin,operation_timeout_ms=30000);self.tx=self.host.adopt_transaction().value
        executor=CurrentDisclosureExecutor(self.host,self.tx,self.registration,bun_executable=os.environ['TRUSS_BUN_EXECUTABLE'])
        caller,host,assembly,transaction=self.consumer()
        result=assembly.query_current_disclosure_in_transaction(transaction,executor=executor,
            sql='SELECT r.salary FROM Resource r',document_ids=('adoc',))
        self.assertIsInstance(result,Ok,str(self.host._custody.last_attempt.error))
        self.assertIsInstance(result.value,CurrentDisclosureRows,str(self.host._custody.last_attempt.error))
        batch=json.loads(result.value.batch_json)
        self.assertEqual(batch['rows'],[[{'disposition':'original','value':{'integerToken':str(v)}}] for v in expected])
        self.assertEqual(self.admin.execute("SELECT count(*) FROM pg_catalog.pg_class WHERE relnamespace=pg_catalog.pg_my_temp_schema() AND relname LIKE 'truss_presence_%'").fetchone(),(0,))
        # Successful private operation released only its savepoint. Both actual
        # transactions still hold their source/role cuts until the host settles.
        self.assertEqual(self.admin.info.transaction_status.name,'INTRANS')
        return caller,host,assembly,transaction

    def test_scram_alice_parallel_occurrences_do_not_duplicate_authorized_object(self):
        caller,host,assembly,transaction=self.public_graph('Alice',[100],parallel=True)
        actual=caller.execute("SELECT pg_catalog.pg_backend_pid()::text,l.virtualtransaction::text FROM pg_catalog.pg_locks l WHERE l.pid=pg_catalog.pg_backend_pid() AND l.locktype='virtualxid' AND l.granted AND l.mode='ExclusiveLock'").fetchone()
        self.assertIsInstance(host._run_operation(transaction,lambda cursor,observed:runtime._verify_graph_caller_cut(cursor,actual)),Ok)
        other,other_host,_,other_tx=self.consumer()
        rejected=other_host._run_operation(other_tx,lambda cursor,observed:runtime._verify_graph_caller_cut(cursor,actual))
        self.assertIsInstance(rejected,Error)
        self.assertIn('same-backend caller transaction',str(other_host._custody.last_attempt.error))
        other_host.detach();other.rollback();other.close()
        statements=('ALTER ROLE consumer NOLOGIN','REVOKE group_writer FROM consumer')
        with psycopg.connect(self.info.connection_uri,autocommit=True) as writer:
            for statement in statements:
                writer.execute('BEGIN');writer.execute("SET LOCAL lock_timeout='100ms'")
                try:
                    with self.assertRaises(psycopg.errors.LockNotAvailable) as blocked:writer.execute(statement)
                    self.assertEqual(blocked.exception.sqlstate,'55P03')
                finally:writer.rollback()
            # Successful operation completion above did not settle either outer
            # transaction. Settle them now and prove the same writes can run.
            host.detach();caller.rollback();self.host.detach();self.admin.rollback()
            for statement in statements:
                writer.execute('BEGIN')
                try:writer.execute(statement)
                finally:writer.rollback()
        self.assertEqual(self.admin.execute("SELECT rolcanlogin FROM pg_catalog.pg_roles WHERE rolname='consumer'").fetchone(),(True,))
        self.assertEqual(self.admin.execute("SELECT pg_catalog.pg_has_role('consumer','group_writer','MEMBER')").fetchone(),(True,))

    def test_scram_bob_has_only_own_project_resource(self):
        self.public_graph('Bob',[200])

    def test_scram_outsider_has_no_resource(self):
        self.public_graph('Outsider',[])
