# SPDX-License-Identifier: MIT OR Apache-2.0
"""TN01/TN05 authentic enrolled source/owner/ACL/capability controls."""
import copy
import json
from uuid import uuid4
import psycopg
from truss.catalog_runtime import _release
import temporal_native_fixture as fixture


class TemporalSourceSecurityNativeTests(fixture.TemporalNativeFixture):
    def test_native_temporal_cached_and_uncached_source_keep_exact_descriptor_basis(self):
        """TN08 cache present/miss on actual public acceptance, not mock rows."""
        c,h,a,tx=self.ready_temporal();binding,requirements=self.capture(c)
        parsed=json.loads(binding);revision=parsed['catalogRevision']
        cached=self.admin.execute('SELECT metadata::text FROM truss.runtime_document_schema WHERE rev=%s AND doc_id=%s',
                                  (revision,'adoc')).fetchone()
        self.assertIsNotNone(cached)
        metadata=json.loads(cached[0]);pin=next(p for p in parsed['documents'] if p['documentId']=='adoc')
        self.assertEqual(metadata['pin'],pin)
        family,descriptor,definition_pin,property_id=self.admin.execute(
            "SELECT p.scalar_type,p.native_temporal,d.definition_pin,p.prop_id FROM truss.prop_def p "
            "JOIN truss.runtime_definition_source d ON d.rev=p.definition_rev AND d.ord=p.definition_doc_ord "
            "AND d.doc_id=p.definition_document_id AND d.module_id=p.declaration_module AND d.element_id=p.element "
            "AND d.kind='element' AND d.key_id='' WHERE p.type_id=%s AND p.element='A-local'",
            (self.selected_type,)).fetchone()
        self.assertEqual(family,'localTimestamp');self.assertEqual(descriptor['source']['sha256'],pin['sha256'])
        type_metadata,valid=self.admin.execute('SELECT metadata,valid_properties FROM truss.runtime_type_schema WHERE rev=%s AND type_id=%s',
                                             (revision,self.selected_type)).fetchone()
        self.assertIs(valid,True);self.assertEqual(type_metadata['propertyPins'][str(property_id)],definition_pin)
        original=c.execute('SELECT id,props FROM '+self.source()+' ORDER BY id',self.source_arguments(binding,requirements)).fetchall()
        self.assertEqual(len(original),6)
        # Named administrative cache-miss control. Actual native data/owner
        # inputs stay unchanged; immutable triggers are restored BEFORE calls.
        self.admin.execute('ALTER TABLE truss.runtime_document_schema DISABLE TRIGGER USER')
        try:self.admin.execute('DELETE FROM truss.runtime_document_schema WHERE rev=%s AND doc_id=%s',(revision,'adoc'))
        finally:self.admin.execute('ALTER TABLE truss.runtime_document_schema ENABLE TRIGGER USER')
        try:
            self.assertIsNone(self.admin.execute('SELECT metadata FROM truss.runtime_document_schema WHERE rev=%s AND doc_id=%s',
                                               (revision,'adoc')).fetchone())
            missing=c.execute('SELECT id,props FROM '+self.source()+' ORDER BY id',self.source_arguments(binding,requirements)).fetchall()
            self.assertEqual(missing,original)
        finally:
            self.admin.execute('INSERT INTO truss.runtime_document_schema(rev,doc_id,metadata) VALUES(%s,%s,%s::jsonb)',
                               (revision,'adoc',cached[0]))
        self.assertEqual(self.admin.execute('SELECT metadata::text FROM truss.runtime_document_schema WHERE rev=%s AND doc_id=%s',
                                           (revision,'adoc')).fetchone(),cached)
        self.assertEqual(c.execute('SELECT id,props FROM '+self.source()+' ORDER BY id',self.source_arguments(binding,requirements)).fetchall(),original)
        self.assertEqual(self.admin.execute("SELECT native_temporal FROM truss.prop_def WHERE type_id=%s AND element='A-local'",
                                           (self.selected_type,)).fetchone()[0],descriptor)
        print('temporal-native-cache-source-custody '+json.dumps({'catalogRevision':revision,'sourcePin':pin,
            'family':family,'nativeDescriptor':descriptor,'definitionPin':definition_pin,'cachedAndUncachedRows':len(original)},sort_keys=True))

    def denied_source(self, connection, binding, requirements, state):
        with self.assertRaises(psycopg.Error) as caught:
            with connection.transaction():
                with connection.cursor(name='temporal_security_' + uuid4().hex[:8]) as cursor:
                    cursor.execute('SELECT id FROM '+self.source()+' LIMIT 1',self.source_arguments(binding,requirements))
                    self.fail('Denied source released first fetch: '+repr(cursor.fetchone()))
        self.assertEqual(caught.exception.sqlstate,state)

    def test_installed_temporal_abi13_shims_have_exact_owner_acl_and_stability(self):
        connection,host,assembly,transaction=self.ready_temporal()
        binding,requirements=self.capture(connection)
        manifest,digest,_=_release()
        installed=self.admin.execute('SELECT release_id,release_sha256,owner_oid FROM truss.catalog_runtime_installation').fetchone()
        self.assertEqual(installed[:2],(manifest['releaseId'],digest))
        self.assertEqual(self.admin.execute('SELECT truss.query_abi()->>\'version\',truss.query_temporal_abi()->>\'version\'').fetchone(),('1.2','1.3'))
        captured=assembly.query_temporal_catalog_sources_in_transaction(transaction,
            sql='SELECT "A-instant" FROM "m"."A"',document_ids=('adoc',),
            temporal_parameters={'token':{'kind':'instant','value':'2024-01-01T01:00:00+01:00'}})
        from truss import Ok
        from truss.query import QueryCatalogSources
        self.assertIsInstance(captured,Ok,repr(captured))
        self.assertIsInstance(captured.value,QueryCatalogSources,repr(captured))
        request=json.loads(captured.value.request_json)
        self.assertEqual(request['interfaceVersion'],'weft-compile/0.2.10')
        self.assertEqual(request['temporalProfile'],'umf.weft-binding-temporal/0.2')
        self.assertEqual(request['temporalParameters']['token']['value'],'2024-01-01T01:00:00+01:00')
        from hashlib import sha256
        self.assertEqual(request['target']['bindingSha256'],sha256(request['target']['bindingJson'].encode()).hexdigest())
        self.assertEqual(json.loads(request['target']['bindingJson'])['queryAbi']['version'],'1.3')
        inventory=[]
        for signature,volatility in (
            ('truss.person_query_temporal_objects(jsonb,int,jsonb)','s'),('truss.query_temporal_objects(jsonb,int,jsonb)','s'),
            ('truss.person_query_temporal_page_objects(jsonb,int,text,jsonb)','s'),('truss.query_temporal_page_objects(jsonb,int,text,jsonb)','s'),
            ('truss.query_temporal_canonical_text(text,text)','i')):
            row=self.admin.execute('SELECT proowner,provolatile,prosecdef,pg_get_functiondef(oid) FROM pg_proc WHERE oid=%s::regprocedure',(signature,)).fetchone()
            self.assertEqual(row[0],installed[2]);self.assertEqual(row[1],volatility)
            self.assertEqual(row[2],signature!='truss.query_temporal_canonical_text(text,text)')
            inventory.append({'signature':signature,'owner':row[0],'volatility':row[1],'securityDefiner':row[2],'definition':row[3]})
        for page in (False,True):
            self.assertEqual(len(connection.execute('SELECT id FROM '+self.source(page),self.source_arguments(binding,requirements,page)).fetchall()),6)
        outsider='temporal_outsider_'+uuid4().hex[:8]
        self.admin.execute(psycopg.sql.SQL('CREATE ROLE {} LOGIN').format(psycopg.sql.Identifier(outsider)))
        try:
            params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);params['user']=outsider
            with psycopg.connect(**params,autocommit=True) as unauthorized:
                with self.assertRaises(psycopg.errors.InsufficientPrivilege) as caught:
                    unauthorized.execute("SELECT truss.query_temporal_canonical_text('date','2000-02-29')")
                self.assertEqual(caught.exception.sqlstate,'42501')
        finally:
            self.admin.execute(psycopg.sql.SQL('DROP ROLE {}').format(psycopg.sql.Identifier(outsider)))
        print('temporal-native-source-inventory '+json.dumps({'release':installed[0],'digest':installed[1],'functions':inventory},sort_keys=True))

    def test_temporal_shim_refuses_abi_owner_acl_source_and_context_drift(self):
        connection,host,assembly,transaction=self.ready_temporal()
        original,requirements=self.capture(connection)
        self.assertEqual(len(connection.execute('SELECT id FROM '+self.source(),self.source_arguments(original,requirements)).fetchall()),6)
        for mutation,state in (('abi','0A000'),('source','55P03'),('release','0A000')):
            changed=json.loads(original)
            if mutation=='abi':changed['queryAbi']['sha256']='0'*64
            elif mutation=='source':changed['documents'][0]['sha256']='0'*64
            else:changed['releaseSha256']='0'*64
            with self.subTest(mutation=mutation):self.denied_source(connection,json.dumps(changed),requirements,state)
        self.admin.execute('REVOKE EXECUTE ON FUNCTION truss.query_temporal_objects(jsonb,int,jsonb) FROM group_writer')
        try:self.denied_source(connection,original,requirements,'42501')
        finally:self.admin.execute('GRANT EXECUTE ON FUNCTION truss.query_temporal_objects(jsonb,int,jsonb) TO group_writer')
        self.admin.execute('CREATE ROLE temporal_wrong_owner NOLOGIN')
        try:
            self.admin.execute('ALTER FUNCTION truss.query_temporal_objects(jsonb,int,jsonb) OWNER TO temporal_wrong_owner')
            try:self.denied_source(connection,original,requirements,'55000')
            finally:self.admin.execute(psycopg.sql.SQL('ALTER FUNCTION truss.query_temporal_objects(jsonb,int,jsonb) OWNER TO {}').format(psycopg.sql.Identifier(self.installation.owner_role)))
        finally:self.admin.execute('DROP ROLE temporal_wrong_owner')
        self.assertEqual(len(connection.execute('SELECT id FROM '+self.source(),self.source_arguments(original,requirements)).fetchall()),6)

    def test_temporal_person_admission_needs_module_role_even_for_registrar(self):
        connection,host,assembly,transaction=self.ready_temporal()
        binding,requirements=self.capture(connection)
        self.admin.execute(psycopg.sql.SQL('GRANT {} TO consumer WITH SET FALSE').format(psycopg.sql.Identifier(self.installation.registrar_role)))
        try:
            self.admin.execute('REVOKE group_writer FROM consumer')
            try:self.denied_source(connection,binding,requirements,'P1403')
            finally:self.admin.execute('GRANT group_writer TO consumer WITH SET FALSE')
        finally:self.admin.execute(psycopg.sql.SQL('REVOKE {} FROM consumer').format(psycopg.sql.Identifier(self.installation.registrar_role)))
        self.assertEqual(len(connection.execute('SELECT id FROM '+self.source(),self.source_arguments(binding,requirements)).fetchall()),6)
