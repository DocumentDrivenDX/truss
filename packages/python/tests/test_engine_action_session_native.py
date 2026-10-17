"""Owned SCRAM RC completion with real public groups; no action admission claim."""
from pathlib import Path
import secrets
import time
import psycopg
from psycopg import sql
import test_group_create_native as base
from truss import Ok,ObjectFound,CatalogRuntimeConfiguration,create_reference_assembly
from truss._scram_preparation_login import ScramPreparationLogin
from truss._engine_action_session import _EngineActionSession
from truss.groups import GroupSuccess

class EngineActionSessionNativeTests(base.PublicCreateGroupTests):
    for name in tuple(n for n in dir(base.PublicCreateGroupTests) if n.startswith('test_')):
        locals()[name]=None

    def test_public_group_commit_read_rollback_and_deferred_rejection(self):
        connection,host,assembly,tx=self.ready(document_ids=('adoc',))
        host.detach();connection.rollback();connection.close()
        password=secrets.token_urlsafe(32)
        self.admin.execute("SET password_encryption='scram-sha-256'")
        self.admin.execute(sql.SQL('ALTER ROLE consumer PASSWORD {}').format(sql.Literal(password)))
        self.admin.execute('CREATE TABLE public.action_commit_parent(id int PRIMARY KEY)')
        self.admin.execute('CREATE TABLE public.action_commit_child(id int REFERENCES public.action_commit_parent(id) DEFERRABLE INITIALLY DEFERRED)')
        self.addCleanup(self.admin.execute,'DROP TABLE IF EXISTS public.action_commit_child,public.action_commit_parent')
        self.admin.execute('GRANT INSERT ON public.action_commit_child TO consumer')
        params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri)
        login=ScramPreparationLogin(params['host'],int(params.get('port','5432')),
            params.get('dbname',params.get('user','postgres')),'consumer',password)
        hba=Path(self.admin.execute('SHOW hba_file').fetchone()[0]);original=hba.read_bytes()
        try:
            hba.write_bytes(b'local all consumer scram-sha-256\n'+original)
            before=self.admin.execute('SELECT pg_catalog.pg_conf_load_time()').fetchone()[0]
            self.admin.execute('SELECT pg_catalog.pg_reload_conf()')
            deadline=time.monotonic()+5
            while self.admin.execute('SELECT pg_catalog.pg_conf_load_time()').fetchone()[0]==before:
                if time.monotonic()>=deadline:self.fail('SCRAM HBA reload not observed')
                time.sleep(.01)
            identity=None
            for phase in ('commit','rollback','rejected'):
                session=_EngineActionSession(login,statement_timeout_ms=2000 if phase=='rollback' else 10000)
                try:
                    host,tx=session.begin();native=session.connection
                    assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value
                    def authenticated(cursor,observed):
                        cursor.execute('SELECT system_user,session_user::text,current_user::text')
                        return cursor.fetchone()
                    self.assertEqual(session.run_operation(authenticated).value,
                        ('scram-sha-256:consumer','consumer','consumer'))
                    if identity is not None:
                        read=assembly.get_object_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',object_id=int(identity.id))
                        self.assertIsInstance(read,Ok);self.assertIsInstance(read.value,ObjectFound)
                        self.assertEqual(dict(read.value.object.values)['A-label'],'commit')
                    input,_=self.input(assembly,tx,(self.create(label=phase),))
                    request=assembly.group_context_in_transaction(tx).value.request('owned-action-'+phase)
                    result=self.apply(assembly,tx,input,request)
                    self.assertIsInstance(result,GroupSuccess,repr(result))
                    if phase=='commit':identity=result.response.semantic.results[0].identity
                    if phase=='rejected':
                        def fail_at_commit(cursor,observed):
                            cursor.execute('INSERT INTO public.action_commit_child VALUES(1)')
                        self.assertIsInstance(session.run_operation(fail_at_commit),Ok)
                    committed,rolled=object(),object()
                    observed,error=session.complete(commit=phase!='rollback',committed=committed,rolled_back=rolled)
                    self.assertIs(observed,committed if phase=='commit' else rolled)
                    self.assertEqual(session.completion_observation().disposition,
                        'committed' if phase=='commit' else 'rolled_back')
                    if phase=='rejected':self.assertEqual(error.sql_state,'23503')
                    else:self.assertIsNone(error)
                    self.assertEqual(native.execute("SELECT setting FROM pg_catalog.pg_settings WHERE name='statement_timeout'").fetchone(),
                        ('2000' if phase=='rollback' else '10000',))
                    with self.assertRaises(ValueError):session.begin()
                    with self.assertRaises(ValueError):session.complete(commit=True,committed=committed,rolled_back=rolled)
                finally:
                    session.close()
                self.assertTrue(native.closed)
                self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(1,))
                self.assertEqual(self.admin.execute('SELECT count(*) FROM public.action_commit_child').fetchone(),(0,))
        finally:
            hba.write_bytes(original);self.admin.execute('SELECT pg_catalog.pg_reload_conf()')
            self.admin.execute('DROP TABLE IF EXISTS public.action_commit_child,public.action_commit_parent')
