# SPDX-License-Identifier: MIT OR Apache-2.0
"""Changed-document validation uses real committed data and current authority."""
import json
from truss import CatalogDocument,CatalogAcceptanceRefused,Ok,Error
from truss.groups import GroupSuccess
import test_group_create_native as group_tests
from test_catalog_relational_support import relational_document

class CatalogEvolutionTests(group_tests.PublicCreateGroupTests):
    for _name in tuple(n for n in dir(group_tests.PublicCreateGroupTests) if n.startswith('test_')):
        locals()[_name]=None

    def prepare_changed(self,assembly,*,change_scalar=True,add_new_required=True):
        source=relational_document();source['id']='adoc'
        module=source['modules'][0]
        for element in module['elements']:
            if change_scalar and element['id']=='A-label':element['scalarType']='integer'
            if add_new_required and element['id']=='A':element['members'].append({'module':'m','element':'new-required'})
        if add_new_required:
            module['elements'].append({'id':'new-required','name':'new-required','kind':'field',
                'scalarType':'boolean','nullability':'required','cardinality':'one','extensions':{}})
        return assembly.prepare_catalog((CatalogDocument('adoc','r2',json.dumps(source).encode()),),bun_executable='/opt/homebrew/bin/bun')

    def test_exact_rule_counts_and_no_acceptance_or_cache_effects(self):
        connection,host,assembly,tx=self.ready()
        input,request=self.input(assembly,tx,operations=(self.create('one','v1','first'),self.create('two','v2','second')))
        self.assertIsInstance(self.apply(assembly,tx,input,request),GroupSuccess)
        host.detach();connection.commit()
        self.admin.execute('GRANT '+self.installation.registrar_role+' TO consumer WITH SET FALSE')
        connection,host,assembly,tx=self.consumer()
        prepared=self.prepare_changed(assembly,add_new_required=False)
        original_cache=assembly._group_documents
        before=self.admin.execute('SELECT (SELECT rev FROM truss.schema_head),(SELECT count(*) FROM truss.schema_doc),(SELECT count(*) FROM truss.catalog_registration_request),(SELECT count(*) FROM truss.journal)').fetchone()
        result=assembly.accept_in_transaction(tx,prepared,request_key='changed')
        self.assertIsInstance(result,Ok);self.assertIsInstance(result.value,CatalogAcceptanceRefused)
        self.assertEqual(result.value.revision,1)
        self.assertEqual({(v.field_id,v.rule,v.affected_object_count) for v in result.value.violations},
            {('A-label','property.scalar_type',2)})
        self.assertTrue(all((v.document_id,v.module_id,v.record_id,v.field_module_id)==('adoc','m','A','m') for v in result.value.violations))
        self.assertEqual(assembly._group_documents,original_cache)
        self.assertEqual(connection.execute('SELECT 42').fetchone(),(42,))
        host.detach();connection.commit()
        self.assertEqual(self.admin.execute('SELECT (SELECT rev FROM truss.schema_head),(SELECT count(*) FROM truss.schema_doc),(SELECT count(*) FROM truss.catalog_registration_request),(SELECT count(*) FROM truss.journal)').fetchone(),before)


    def test_new_required_member_reports_exact_missing_count_without_acceptance(self):
        connection,host,assembly,tx=self.ready()
        input,request=self.input(assembly,tx,operations=(self.create('one','v1','first'),self.create('two','v2','second')))
        self.assertIsInstance(self.apply(assembly,tx,input,request),GroupSuccess)
        host.detach();connection.commit()
        self.admin.execute('GRANT '+self.installation.registrar_role+' TO consumer WITH SET FALSE')
        connection,host,assembly,tx=self.consumer()
        prepared=self.prepare_changed(assembly,change_scalar=False,add_new_required=True)
        original_cache=assembly._group_documents
        before=self.admin.execute('SELECT (SELECT rev FROM truss.schema_head),(SELECT count(*) FROM truss.schema_doc),(SELECT count(*) FROM truss.catalog_registration_request),(SELECT count(*) FROM truss.journal)').fetchone()
        result=assembly.accept_in_transaction(tx,prepared,request_key='new-required')
        self.assertIsInstance(result,Ok);self.assertIsInstance(result.value,CatalogAcceptanceRefused)
        self.assertEqual(result.value.revision,1)
        self.assertEqual({(v.field_id,v.rule,v.affected_object_count) for v in result.value.violations},
            {('new-required','property.required',2)})
        self.assertTrue(all((v.document_id,v.module_id,v.record_id,v.field_module_id)==('adoc','m','A','m') for v in result.value.violations))
        self.assertEqual(assembly._group_documents,original_cache)
        self.assertEqual(connection.execute('SELECT 42').fetchone(),(42,))
        host.detach();connection.commit()
        self.assertEqual(self.admin.execute('SELECT (SELECT rev FROM truss.schema_head),(SELECT count(*) FROM truss.schema_doc),(SELECT count(*) FROM truss.catalog_registration_request),(SELECT count(*) FROM truss.journal)').fetchone(),before)

    def test_registrar_without_module_access_gets_no_population_counts(self):
        connection,host,assembly,tx=self.ready()
        input,request=self.input(assembly,tx)
        self.assertIsInstance(self.apply(assembly,tx,input,request),GroupSuccess)
        host.detach();connection.commit()
        self.admin.execute('GRANT '+self.installation.registrar_role+' TO consumer WITH SET FALSE')
        self.admin.execute('REVOKE group_writer FROM consumer')
        connection,host,assembly,tx=self.consumer()
        result=assembly.accept_in_transaction(tx,self.prepare_changed(assembly),request_key='hidden-count')
        self.assertIsInstance(result,Error);self.assertEqual(result.error.catalog_code,'unauthorized')
        self.assertEqual(result.error.sql_state,'42501')
        self.assertEqual(connection.execute('SELECT 42').fetchone(),(42,))
        host.detach();connection.rollback()
