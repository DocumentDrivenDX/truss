# SPDX-License-Identifier: MIT OR Apache-2.0
"""Fresh0.76 installer component, independent of held compiler/owner adoption.

This observes actual installed definitions. No temporal catalog acceptance,
query execution, dependency-cohort adoption or release claim follows from it.
"""
from hashlib import sha256
import json
import psycopg

from truss.catalog_runtime import _release
from truss._runtime_admission import person_entrypoints
from truss._temporal_profiles import abi,profiles
import temporal_native_fixture as fixture


class TemporalEnrollmentNativeTests(fixture.TemporalNativeFixture):
    def test_fresh_installer_enrolls_original_sources_and_additive_abi(self):
        self.install()
        manifest,digest,_=_release()
        installation=self.admin.execute('SELECT release_id,release_sha256,owner_oid FROM truss.catalog_runtime_installation').fetchone()
        self.assertEqual(installation[:2],('truss-catalog-runtime/0.76-temporal-candidate',digest))
        original,selected=self.admin.execute('SELECT truss.query_abi(),truss.query_temporal_abi()').fetchone()
        self.assertEqual(original,{'identity':'truss-postgresql-logical-query','version':'1.2',
                                 'sha256':'8266c19d6f1bc4e816d5981cd594b224f09bafd4975e1c851610fa94d1f75f96'})
        self.assertEqual(selected,abi())
        self.assertEqual(self.admin.execute('SELECT truss.runtime_temporal_profiles()').fetchone()[0],profiles())
        declarations=[entry for entry in person_entrypoints() if entry['name'] in (
            'query_temporal_binding','query_temporal_objects','query_temporal_page_objects',
            'temporal_group_context','apply_temporal_group','apply_temporal_group_prepared',
            'get_temporal_object','lookup_temporal_key','page_temporal_objects',
            'temporal_import_context','temporal_import_key_selection','temporal_import_object_identity',
            'recover_temporal_group_request','temporal_writer_schema_basis','temporal_scope')]
        self.assertEqual(len(declarations),15)
        observed=[]
        for entry in declarations:
            for name in (entry['name'],'person_'+entry['name']):
                # The declaration's original argument types select the actual
                # overload; no guessed regprocedure or package-only identity.
                rows=self.admin.execute("SELECT p.oid::regprocedure::text,p.proowner,p.provolatile,p.prosecdef,"
                    "pg_get_function_identity_arguments(p.oid),pg_get_functiondef(p.oid),"
                    "has_function_privilege('consumer',p.oid,'EXECUTE') FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace "
                    "WHERE n.nspname='truss' AND p.proname=%s",(name,)).fetchall()
                self.assertEqual(len(rows),1,(name,rows))
                signature,owner,volatility,security,arguments,definition,consumer_execute=rows[0]
                self.assertEqual(owner,installation[2],signature)
                self.assertEqual(volatility,entry['volatility'],signature)
                self.assertTrue(security,signature)
                self.assertEqual(consumer_execute,name.startswith('person_'),signature)
                observed.append({'signature':signature,'ownerOid':owner,'volatility':volatility,
                                 'securityDefiner':security,'consumerExecute':consumer_execute,
                                 'definitionSha256':sha256(definition.encode()).hexdigest(),'definition':definition})
        helper=self.admin.execute("SELECT proowner,provolatile,prosecdef,has_function_privilege('consumer',oid,'EXECUTE'),pg_get_functiondef(oid) "
            "FROM pg_proc WHERE oid='truss.query_temporal_canonical_text(text,text)'::regprocedure").fetchone()
        self.assertEqual(helper[:4],(installation[2],'i',False,False))
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.schema_doc').fetchone(),(0,))
        # Prepared optimization is unavailable even if a caller supplies all
        # expected labels; refusal must precede original group parsing/effects.
        with self.assertRaises(psycopg.Error) as caught:
            with self.admin.transaction():
                self.admin.execute('SELECT truss.apply_temporal_group_prepared(%s,%s,%s,%s,%s,%s::jsonb)',
                    (b'{}',b'[]',b'{}',manifest['releaseId'],digest,json.dumps({
                        'profile':'truss-python-temporal-record-patch/0.1','valueProfile':profiles()['valueProfile'],'queryAbi':abi()})))
        self.assertEqual(getattr(caught.exception,'sqlstate',None),'0A000')
        print('temporal-fresh-native-enrollment '+json.dumps({'release':installation[0],'manifestSha256':digest,
            'sourceFiles':manifest['files'],'ordinaryAbi':original,'temporalAbi':selected,
            'functions':observed,'helperDefinition':helper[4]},sort_keys=True))
