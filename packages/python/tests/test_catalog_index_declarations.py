# SPDX-License-Identifier: MIT OR Apache-2.0
"""Original selected declaration policy integrated with actual native reports."""
import dataclasses
import hashlib
import json
import unittest
from unittest.mock import patch
from pg8000.exceptions import DatabaseError
from test_catalog_staging import CatalogNativeFixture, ROOT, native_document
from test_preparation import prepare
from truss import CatalogDocument
from truss._catalog_staging import stage_catalog_report_basis
from truss._catalog_report import require_current_catalog_report_basis
from truss import _catalog_index_declarations as declarations


class CatalogIndexDeclarationTests(CatalogNativeFixture, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        c=cls.Connection(**cls.kwargs)
        try: c.run((ROOT/'packages/postgresql/native/catalog-report/empty-graph.sql').read_text())
        finally: c.close()

    def report(self):
        return stage_catalog_report_basis(self.connection,self.prepared,origin_bytes=b'{}')

    def cut(self):
        return tuple(self.connection.run('SELECT original_writer_xid::text,operation_ordinal::text,effect_generation::text FROM truss.row_home_operation')[0])

    def collect(self,basis):
        payload=json.loads(basis.basis_bytes)
        return declarations.collect_catalog_index_declarations(
            self.connection,self.prepared,payload['fields']['rev'],self.cut())

    def test_real_unkeyed_report_field_and_baseline_indexes(self):
        before=self.connection.run("SELECT count(*) FROM pg_catalog.pg_indexes WHERE schemaname='truss'")[0][0]
        self.assertGreater(before,0)
        basis=self.report();payload=json.loads(basis.basis_bytes)
        self.assertEqual(payload['fields']['pending_indexes'],[])
        self.assertNotIn('pending_indexes',basis.missing_fields)
        self.assertIn('assertions',basis.missing_fields)
        self.assertFalse(payload['acceptedReportQualified'])
        evidence=json.loads(bytes.fromhex(payload['indexDeclarationEvidenceHex']))
        policy=bytes.fromhex(evidence['policyHex'])
        self.assertEqual(hashlib.sha256(policy).hexdigest(),declarations.POLICY_SHA256)
        self.assertEqual(policy,(ROOT/'packages/python/src/truss/_profiles/absent-binding-index-declarations.json').read_bytes())
        self.assertNotEqual(json.loads(policy)['identity'],self.prepared.input()['layoutProfile']['identity'])
        self.assertFalse(evidence['installedProfileQualified']);self.assertFalse(evidence['readinessQualified'])
        self.assertEqual(evidence['inputHex'],self.prepared.input_bytes.hex())
        self.assertEqual(self.connection.run("SELECT count(*) FROM pg_catalog.pg_indexes WHERE schemaname='truss'")[0][0],before)
        require_current_catalog_report_basis(basis,self.connection,self.prepared)

    def test_keyed_multiple_documents_still_declare_no_optimization_jobs(self):
        documents=[]
        for identity in ('first','second'):
            source=native_document(identity);value=json.loads(source.content)
            value['modules'][0]['elements'][0]['keys']=[{
                'id':'label-key','name':'label-key','primary':True,
                'fields':[{'module':'m','element':'label'}]}]
            documents.append(CatalogDocument(identity,'r1',json.dumps(value).encode()))
        self.connection.run('ROLLBACK');self.connection.run('BEGIN')
        self.prepared=prepare(tuple(documents));self.admit(self.prepared)
        basis=self.report();payload=json.loads(basis.basis_bytes)
        self.assertEqual(payload['fields']['counts']['keysAdded'],'2')
        self.assertEqual(payload['fields']['pending_indexes'],[])
        evidence=json.loads(bytes.fromhex(payload['indexDeclarationEvidenceHex']))
        self.assertEqual([d['doc_id'] for d in evidence['documents']],['first','second'])

    def test_changed_policy_refuses_entire_basis_and_rolls_back(self):
        original=declarations._policy_bytes()
        with patch.object(declarations,'_policy_bytes',return_value=original+b' '):
            with self.assertRaises(DatabaseError) as raised:self.report()
        self.assertEqual(raised.exception.args[0]['C'],'55000')
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.type_def'),[[0]])
        self.assertEqual(self.connection.run('SELECT rev FROM truss.schema_head'),[[0]])

    def test_unknown_extension_is_retained_without_job_or_semantic_claim(self):
        source=native_document('future');value=json.loads(source.content)
        value['vocabularies']={'future.vendor':{'version':'99.0.0'}}
        value['extensions']={'future.vendor':{'indexIntent':'retain this unknown meaning'}}
        original=json.dumps(value).encode()
        self.connection.run('ROLLBACK');self.connection.run('BEGIN')
        self.prepared=prepare((CatalogDocument('future','r1',original),));self.admit(self.prepared)
        basis=self.report();payload=json.loads(basis.basis_bytes)
        self.assertEqual(payload['fields']['pending_indexes'],[])
        self.assertEqual(self.connection.run('SELECT document FROM truss.schema_doc'),[[original.decode()]])
        self.assertEqual(payload['fieldQualification']['extensions'],'partial_retention_only')
        self.assertIn('extensions',basis.missing_fields)
        self.assertFalse(payload['acceptedReportQualified'])

    def test_policy_resource_digest_corruption_refuses(self):
        class Resource:
            def joinpath(self,name):return self
            def read_bytes(self):return b'{}'
        with patch.object(declarations,'files',return_value=Resource()):
            with self.assertRaisesRegex(ValueError,'Original selected index'):self.report()
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.type_def'),[[0]])

    def test_missing_policy_resource_never_falls_back_to_empty_inventory(self):
        class Resource:
            def joinpath(self,name):return self
            def read_bytes(self):raise FileNotFoundError('missing original policy')
        with patch.object(declarations,'files',return_value=Resource()):
            with self.assertRaises(FileNotFoundError):self.report()
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.schema_doc'),[[0]])
        self.assertEqual(self.connection.run('SELECT effect_generation FROM truss.row_home_operation'),[[0]])

    def test_original_evidence_copies_foreign_preparation_and_stale_cut_refuse(self):
        basis=self.report();result=self.collect(basis)
        for carrier,prepared in ((dataclasses.replace(result),self.prepared),
                                 (result,prepare((native_document('foreign'),)))):
            with self.assertRaises(ValueError):
                declarations.require_current_catalog_index_declarations(carrier,self.connection,prepared)
        declarations.require_current_catalog_index_declarations(result,self.connection,self.prepared)
        self.connection.run('UPDATE truss.prop_def SET name=name')
        with self.assertRaises(DatabaseError) as raised:
            declarations.require_current_catalog_index_declarations(result,self.connection,self.prepared)
        self.assertEqual(raised.exception.args[0]['C'],'55000')

    def test_copied_preparation_refuses_before_sql(self):
        class NoCalls:
            def run(self,*args,**kwargs):raise AssertionError('No SQL permitted')
        with self.assertRaises(ValueError):
            declarations.collect_catalog_index_declarations(
                NoCalls(),dataclasses.replace(self.prepared),'1',('1','0','0'))

    def test_recheck_result_substitution_refuses(self):
        basis=self.report();original_run=self.connection.run
        for key,replacement in (('readinessQualified',True),('inputHex','00'),
                                ('policyHex','00'),('documents',[])):
            def substituted(sql,**parameters):
                result=original_run(sql,**parameters)
                if 'runtime_collect_absent_binding_index_declarations' in sql:
                    value=json.loads(result[0][0]);value[key]=replacement
                    return [[json.dumps(value)]]
                return result
            with self.subTest(key=key),patch.object(self.connection,'run',side_effect=substituted):
                with self.assertRaisesRegex(ValueError,'policy/input/source correspondence'):
                    require_current_catalog_report_basis(basis,self.connection,self.prepared)
        require_current_catalog_report_basis(basis,self.connection,self.prepared)

    def test_native_unsupported_source_selections_refuse(self):
        original=self.prepared.input()
        variants=[]
        bound=json.loads(json.dumps(original));bound['binding']={'state':'present'};variants.append(bound)
        transformed=json.loads(json.dumps(original));transformed['transforms']=[{}];variants.append(transformed)
        converted=json.loads(json.dumps(original));converted['documents'][0]['ingress']={'kind':'converted'};variants.append(converted)
        for value in variants:
            with self.subTest(value=value['binding']['state'],transforms=bool(value['transforms']),ingress=value['documents'][0]['ingress']['kind']):
                self.connection.run('ROLLBACK');self.connection.run('BEGIN')
                # Administrative original-byte fixture, not prepared/accepted authority.
                self.admit(dataclasses.replace(self.prepared,input_bytes=json.dumps(value).encode()))
                self.connection.run('LOCK TABLE truss.schema_head IN EXCLUSIVE MODE')
                w,o,g=self.cut()
                with self.assertRaises(DatabaseError) as raised:
                    self.connection.run("SELECT truss.runtime_collect_absent_binding_index_declarations(:w,:o,:g,1,decode(:policy,'hex'))",
                        w=w,o=o,g=g,policy=declarations._policy_bytes().hex())
                self.assertEqual(raised.exception.args[0]['C'],'0A000')

    def test_commit_remains_refused_and_host_savepoint_rollback_preserves_work(self):
        self.connection.run('CREATE TEMP TABLE declaration_host_work(value text)')
        self.connection.run("INSERT INTO declaration_host_work VALUES('preserve')")
        self.connection.run('SAVEPOINT acceptance')
        basis=self.report()
        self.assertEqual(json.loads(basis.basis_bytes)['fields']['pending_indexes'],[])
        self.connection.run('ROLLBACK TO SAVEPOINT acceptance')
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.schema_doc'),[[0]])
        self.assertEqual(self.connection.run('SELECT value FROM declaration_host_work'),[['preserve']])
        self.report()
        with self.assertRaises(DatabaseError) as raised:self.connection.run('COMMIT')
        self.assertEqual(raised.exception.args[0]['C'],'55000')
