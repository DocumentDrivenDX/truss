# SPDX-License-Identifier: MIT OR Apache-2.0
"""Public-artifact observations for HF-01; executed probes are not defect fixes.

The result file records desired-outcome satisfaction separately from test health.
Original baseline observations stay archived after fixes change later results.
"""
import base64
import dataclasses
import hashlib
import json
import os
from pathlib import Path

import psycopg
from truss import CatalogDocument, Error, Ok
from truss.batched_import import ObjectImportDraft
from truss.contracts import ABSENT, MapValue
from truss.groups import GroupFailed, GroupSuccess
import test_batched_import_native as fixtures


def original(value):
    if value is ABSENT:
        return {'carrier': 'Absent'}
    if dataclasses.is_dataclass(value):
        return {'carrier': type(value).__name__, **{
            f.name: original(getattr(value, f.name)) for f in dataclasses.fields(value)}}
    if isinstance(value, bytes):
        return {'bytesBase64': base64.b64encode(value).decode(),
                'sha256': hashlib.sha256(value).hexdigest()}
    if isinstance(value, (tuple, list)):
        return [original(v) for v in value]
    if isinstance(value, dict):
        return {str(k): original(v) for k, v in value.items()}
    if value is None or isinstance(value, (str, int, bool, float)):
        return value
    raise TypeError(f'Unrepresented original carrier {type(value).__name__}')


class HohfeldDisputesNativeTests(fixtures.BatchedImportTests):
    for _name in tuple(n for n in dir(fixtures.BatchedImportTests) if n.startswith('test_')):
        locals()[_name] = None

    def observe(self, identity, result, *, desired, facts=None):
        directory = os.environ.get('TRUSS_HF_OBSERVATIONS')
        if not directory:
            return
        path = Path(directory) / (identity + '.json')
        path.parent.mkdir(parents=True, exist_ok=True)
        value = {'case': identity, 'actual': original(result),
                 'desiredOutcomeSatisfied': bool(desired), 'facts': original(facts),
                 'documents': [{'id': d.document_id,
                     'sha256': hashlib.sha256(d.content).hexdigest(),
                     'originalBytesBase64': base64.b64encode(d.content).decode()}
                     for d in getattr(self, 'documents', ())]}
        path.write_text(json.dumps(value, indent=2) + '\n')

    @staticmethod
    def typed_denial(value):
        return not isinstance(value, Error) and any(
            word in json.dumps(original(value)).lower()
            for word in ('unauthorized', 'authorization'))

    def test_capture_nonmember_context_references_reads_groups_and_imports(self):
        c, h, a, t = self.ready(document_ids=('adoc',))
        context = a.group_context_in_transaction(t).value
        group = context.input((self.create(label='known', value='known'),), MapValue(entries=()))
        request = context.request('nonmember-original-request')
        created = a.apply_in_transaction(t, group, request, documents=self.documents)
        self.assertIsInstance(created.value, GroupSuccess, repr(created))
        identity = created.value.response.semantic.results[0].identity
        legacy_context = a.import_context_in_transaction(t).value
        record = self.record(a, t, label='imported')
        legacy = legacy_context.input((record,), load_id='nonmember-legacy', asserted_origin=MapValue(entries=()))
        built = self.build(a, t, 1)
        batch = built.context.input(built.records, load_id='nonmember-batch', asserted_origin=MapValue(entries=()))
        h.detach(); c.commit()
        self.admin.execute('REVOKE group_writer FROM consumer')
        c, h, a, t = self.consumer()
        before = self.group_effect_counts()
        calls = {
            'group-context': lambda: a.group_context_in_transaction(t),
            'group-preparation': lambda: a.prepare_group_in_transaction(t, records=(('adoc','m','A'),)),
            'type-reference': lambda: a.get_type_reference_in_transaction(t, document_id='adoc',module_id='m',record_id='A'),
            'relationship-reference': lambda: a.get_relationship_reference_in_transaction(t,document_id='adoc',module_id='m',relationship_id='A-B'),
            'key-lookup': lambda: a.lookup_key_in_transaction(t,document_id='adoc',module_id='m',record_id='A',key_id='a-primary',values=('known','known')),
            'object-read': lambda: a.get_object_in_transaction(t,document_id='adoc',module_id='m',record_id='A',object_id=int(identity.id)),
            'object-page': lambda: a.page_objects_in_transaction(t,document_id='adoc',module_id='m',record_id='A'),
            'edge-page': lambda: a.page_edges_in_transaction(t,document_id='adoc',module_id='m',relationship_id='A-B',anchor=identity),
            'group-apply': lambda: a.apply_in_transaction(t,group,request,documents=self.documents),
            'import-context': lambda: a.import_context_in_transaction(t),
            'import-build': lambda: a.build_import_records_in_transaction(t,(ObjectImportDraft(document_id='adoc',module_id='m',record_id='A',values=self.create(label='new',value='new').values),)),
            'legacy-import': lambda: a.import_in_transaction(t,legacy,documents=self.documents),
            'batch-import': lambda: a.import_batched_in_transaction(t,batch,documents=self.documents),
        }
        for name, operation in calls.items():
            with self.subTest(surface=name):
                result = operation()
                self.observe('nonmember.'+name, result, desired=self.typed_denial(result),
                    facts={'actor':'consumer','moduleMembership':False})
                self.assertEqual(c.execute('SELECT 42').fetchone(), (42,))
        h.detach(); c.rollback()
        self.assertEqual(self.group_effect_counts(), before)

    def test_capture_damaged_function_grant_separate_from_enrollment(self):
        c, h, a, t = self.ready(document_ids=('adoc',))
        self.assertIsInstance(a.group_context_in_transaction(t), Ok)
        self.assertTrue(self.admin.execute("SELECT pg_has_role('consumer','group_writer','MEMBER')").fetchone()[0])
        self.admin.execute('REVOKE EXECUTE ON FUNCTION truss.group_context(text,text) FROM group_reader,group_writer')
        self.assertFalse(self.admin.execute("SELECT has_function_privilege('consumer','truss.group_context(text,text)','EXECUTE')").fetchone()[0])
        result = a.group_context_in_transaction(t)
        self.observe('damaged-grant.group-context', result,
            desired=isinstance(result, Error), facts={'actor':'consumer','moduleMembership':True,'entrypointExecute':False})
        self.assertTrue(self.admin.execute("SELECT pg_has_role('consumer','group_writer','MEMBER')").fetchone()[0])
        self.assertEqual(c.execute('SELECT 42').fetchone(), (42,))

    @staticmethod
    def ddd(source):
        source['vocabularies']={'umf.ddd':{'version':'0.1.0'},'x-retained':{'version':'1.0.0'}}
        module=source['modules'][0]
        module['extensions']['umf.ddd']={'kind':'bounded-context','terms':[]}
        record=next(e for e in module['elements'] if e['id']=='A')
        record['extensions']={'umf.ddd':{'kind':'entity','fields':{
            'A-label':{'type':{'kind':'scalar','name':'string'},'cardinality':'one'},
            'A-value':{'type':{'kind':'scalar','name':'string'},'cardinality':'one'}},
            'identity':{'fields':['A-label'],'scope':'context'}},
            'x-retained':{'future':[None,{'meaning':'opaque'}]}}

    def required_addition(self, populated):
        c,h,a,t=self.ready(self.ddd,document_ids=('adoc',))
        if populated:
            result=a.apply_in_transaction(t,*self.input(a,t),documents=self.documents)
            self.assertIsInstance(result.value,GroupSuccess,repr(result))
            h.detach();c.commit();c,h,a,t=self.consumer()
        self.admin.execute(psycopg.sql.SQL('GRANT {} TO consumer WITH SET FALSE').format(psycopg.sql.Identifier(self.installation.registrar_role)))
        source=json.loads(self.documents[0].content)
        module=source['modules'][0];record=next(e for e in module['elements'] if e['id']=='A')
        record['members'].append({'module':'m','element':'A-required'})
        record['extensions']['umf.ddd']['fields']['A-required']={'type':{'kind':'scalar','name':'string'},'cardinality':'one'}
        module['elements'].append({'id':'A-required','name':'A-required','kind':'field','scalarType':'string','nullability':'required','cardinality':'one','extensions':{}})
        changed=CatalogDocument('adoc','required-r2',json.dumps(source).encode())
        prepared=a.prepare_catalog((changed,))
        before=self.group_effect_counts()
        result=a.accept_in_transaction(t,prepared,request_key='required-r2')
        accepted=isinstance(result,Ok) and getattr(result.value,'revision',None)==2
        self.observe('required-ddd.'+('populated' if populated else 'empty'),result,
            desired=(not accepted if populated else accepted),
            facts={'populated':populated,'targetSourceSha256':hashlib.sha256(changed.content).hexdigest(),
                   'targetSourceBytesBase64':base64.b64encode(changed.content).decode()})
        if not accepted:
            self.assertEqual(self.admin.execute('SELECT rev FROM truss.schema_head').fetchone(),(1,))
            self.assertEqual(self.group_effect_counts(),before)
        h.detach();c.rollback()

    def test_capture_required_paired_ddd_addition_on_empty_record(self):
        self.required_addition(False)

    def test_capture_required_paired_ddd_addition_on_populated_record(self):
        self.required_addition(True)

    def test_single_field_key_first_middle_last_conflicts_name_actual_ordinal(self):
        def single_key(source):
            for record in (e for e in source['modules'][0]['elements'] if e['kind']=='record'):
                record['keys']=[{'id':'identity','name':'identity','primary':True,
                    'fields':[{'module':'m','element':record['id']+'-label'}]}]
            source['modules'][0]['relationships'][0]['target'][0]['key']='identity'
        c,h,a,t=self.ready(single_key,document_ids=('adoc',))
        context=a.group_context_in_transaction(t).value
        seeded=a.apply_in_transaction(t,context.input((self.create(label='zz-b',value='held'),),MapValue(entries=())),context.request('hold-zz-b'),documents=self.documents)
        self.assertIsInstance(seeded.value,GroupSuccess,repr(seeded));h.detach();c.commit()
        c,h,a,t=self.consumer();before=self.group_effect_counts()
        for position in range(3):
            context=a.group_context_in_transaction(t).value
            labels=['zz-a','zz-c'];labels.insert(position,'zz-b')
            commands=tuple(self.create(label=label,value='new',alias='item-'+str(i)) for i,label in enumerate(labels))
            result=a.apply_in_transaction(t,context.input(commands,MapValue(entries=())),context.request('conflict-'+str(position)),documents=self.documents)
            self.assertIsInstance(result.value,GroupFailed,repr(result))
            failure=result.value.failure
            correct=(failure.operation_code,failure.operation_index)==('key_conflict',str(position))
            self.observe('single-key-collision.'+str(position),result,desired=correct,facts={'labels':labels,'expectedOriginalOperationIndex':position})
            self.assertTrue(correct,repr(result));self.assertEqual(self.group_effect_counts(),before)

    def test_capture_apply_legacy_and_batched_unknown_value_retention_and_facets(self):
        from dataclasses import replace
        from truss.contracts import TextValue
        from truss.groups import AuthoredValue
        from truss.imports import ImportCreated, ImportReported, ImportRejected
        def bounded(source):
            field=next(e for e in source['modules'][0]['elements'] if e['id']=='A-value')
            field['facets']={'length':{'max':4,'unit':'unicode-scalar'}}
        c,h,a,t=self.ready(bounded,document_ids=('adoc',))
        unknown=AuthoredValue(name='future',value=TextValue(kind='string',text='kept-opaque'))
        good=self.create(label='apply',value='ok');good=replace(good,values=good.values+(unknown,))
        applied,_,_=self.run_group(a,t,(good,))
        self.assertIsInstance(applied,GroupSuccess,repr(applied))
        identities={'apply':applied.response.semantic.results[0].identity}
        invalid,_,_=self.run_group(a,t,(self.create(label='bad-apply',value='too-long'),))
        self.observe('facets.apply',invalid,desired=isinstance(invalid,GroupFailed))
        context=a.import_context_in_transaction(t).value
        legacy_values=self.create(label='legacy',value='ok').values+(unknown,)
        built_legacy=a.object_import_record_in_transaction(t,document_id='adoc',module_id='m',record_id='A',values=legacy_values)
        self.assertIsInstance(built_legacy,Ok,repr(built_legacy))
        legacy=a.import_in_transaction(t,context.input((built_legacy.value,),load_id='legacy-unknown',asserted_origin=MapValue(entries=())),documents=self.documents)
        self.assertIsInstance(legacy,ImportReported,repr(legacy));self.assertIsInstance(legacy.report.outcomes[0],ImportCreated)
        identities['legacy']=legacy.report.outcomes[0].identity
        values=self.create(label='batch',value='ok').values+(unknown,)
        drafts=(ObjectImportDraft(document_id='adoc',module_id='m',record_id='A',values=values),
            ObjectImportDraft(document_id='adoc',module_id='m',record_id='A',values=self.create(label='bad-import',value='too-long').values))
        built=a.build_import_records_in_transaction(t,drafts)
        self.assertIsInstance(built,Ok,repr(built))
        batch=self.run_batch(a,t,built.value)
        self.assertIsInstance(batch.result.report.outcomes[0],ImportCreated,repr(batch))
        identities['batch']=batch.result.report.outcomes[0].identity
        self.observe('facets.batch',batch,desired=isinstance(batch.result.report.outcomes[1],ImportRejected))
        h.detach();c.commit();c,h,a,t=self.consumer()
        for route,identity in identities.items():
            public=a.get_object_in_transaction(t,document_id='adoc',module_id='m',record_id='A',object_id=int(identity.id))
            self.assertIsInstance(public,Ok,repr(public))
            retained=dict(public.value.object.retained)
            native=self.admin.execute('SELECT retained FROM truss.object WHERE id=%s',(int(identity.id),)).fetchone()[0]
            value=retained.get('future')
            self.observe('unknown-value.'+route,public,
                desired='future' in native and getattr(value,'text',value)=='kept-opaque',facts={'nativeRetained':native})

    def test_capture_batched_source_timestamp_refusal(self):
        from truss.contracts import MapEntry,TextValue
        c,h,a,t=self.ready(document_ids=('adoc',))
        source=MapValue(entries=(MapEntry(key='at',value=TextValue(kind='string',text='garbage')),))
        built=a.build_import_records_in_transaction(t,(ObjectImportDraft(document_id='adoc',module_id='m',record_id='A',values=self.create(label='bad-at').values,source=source),))
        result=built
        if isinstance(built,Ok):
            result=a.import_batched_in_transaction(t,built.value.context.input(built.value.records,load_id='bad-at',asserted_origin=MapValue(entries=())),documents=self.documents)
        h.detach();c.commit()
        count=self.admin.execute('SELECT count(*) FROM truss.object').fetchone()[0]
        self.observe('source-timestamp.batch',result,desired=count==0,facts={'committedObjects':count,'sourceAt':'garbage','profile':'new-batched-parseable-time'})

    def test_capture_import_minimum_and_group_finalization(self):
        def minimum(source):source['modules'][0]['relationships'][0]['targetMultiplicity']['min']=1
        c,h,a,t=self.ready(minimum,document_ids=('adoc',))
        before=self.group_effect_counts()
        group,_,_=self.run_group(a,t,(self.create(label='apply-min'),))
        self.assertIsInstance(group,GroupFailed,repr(group))
        self.observe('multiplicity.group-minimum',group,
            desired=getattr(group.failure,'operation_code',None) not in ('dependencies',None),
            facts={'minimum':1,'applyStateUnchanged':self.group_effect_counts()==before})
        built=self.build(a,t,1,prefix='min-')
        result=a.import_batched_in_transaction(t,built.context.input(built.records,load_id='minimum',asserted_origin=MapValue(entries=())),documents=self.documents)
        h.detach();commit={'outcome':'committed','sqlstate':None}
        try:c.commit()
        except psycopg.Error as error:
            commit={'outcome':'failed','sqlstate':error.sqlstate,'transactionStatus':str(c.info.transaction_status)}
            c.rollback()
        count=self.admin.execute('SELECT count(*) FROM truss.object').fetchone()[0]
        self.observe('multiplicity.batch-minimum',result,desired=count==0,
            facts={'minimum':1,'commit':commit,'committedObjects':count})

    def test_capture_import_maximum(self):
        from truss.batched_import import EdgeImportDraft
        from truss.groups import NullOrderKey
        c,h,a,t=self.ready(document_ids=('adoc',))
        result,_,_=self.run_group(a,t,(self.create(label='a',alias='a'),
            *(self.create(record='B',label='b'+str(i),value='b'+str(i),alias='b'+str(i)) for i in range(3))))
        self.assertIsInstance(result,GroupSuccess,repr(result))
        identities=[r.identity for r in result.response.semantic.results]
        h.detach();c.commit();c,h,a,t=self.consumer()
        drafts=tuple(EdgeImportDraft(document_id='adoc',module_id='m',relationship_id='A-B',source_endpoint=identities[0],target_endpoint=b,values=(),order_key=NullOrderKey()) for b in identities[1:])
        built=a.build_import_records_in_transaction(t,drafts);self.assertIsInstance(built,Ok,repr(built))
        result=a.import_batched_in_transaction(t,built.value.context.input(built.value.records,load_id='maximum',asserted_origin=MapValue(entries=())),documents=self.documents)
        h.detach();commit={'outcome':'committed','sqlstate':None}
        try:c.commit()
        except psycopg.Error as error:
            commit={'outcome':'failed','sqlstate':error.sqlstate,'transactionStatus':str(c.info.transaction_status)}
            c.rollback()
        count=self.admin.execute('SELECT count(*) FROM truss.edge').fetchone()[0]
        self.observe('multiplicity.batch-maximum',result,desired=count<=2,
            facts={'maximum':2,'commit':commit,'committedEdges':count})

    def test_nondefault_decimal_catalog_is_already_supported(self):
        def decimal(source):
            field=next(e for e in source['modules'][0]['elements'] if e['id']=='A-value')
            field['scalarType']='decimal';field['facets']={'precision':18,'scale':2}
        c,h,a,t=self.ready(decimal,document_ids=('adoc',))
        result=a.accepted_document_in_transaction(t,document_id='adoc')
        self.observe('registration.decimal18-scale2',result,desired=isinstance(result,Ok),
            facts={'precision':18,'scale':2,'catalogRevision':1})

    def test_selected_recursive_scalar_containers_are_already_supported(self):
        from test_recursive_containers_native import RecursiveContainerTests
        self.source_version='0.10.0'
        c,h,a,t=self.ready(lambda source:RecursiveContainerTests.fields(self,source),document_ids=('adoc',))
        result=a.accepted_document_in_transaction(t,document_id='adoc')
        self.observe('registration.nested-scalar-container',result,desired=isinstance(result,Ok),
            facts={'subset':'map of arrays of exact decimals; no arbitrary record-valued support claimed'})

    def test_capture_valid_owner_uuid_source_native_profile_refusal(self):
        from truss import PreparationRejected
        from test_catalog_relational_support import relational_document
        self.install();c,h,a,t=self.consumer()
        source=relational_document();source['id']='uuid'
        field=next(e for e in source['modules'][0]['elements'] if e['id']=='A-value');field['scalarType']='uuid'
        self.documents=(CatalogDocument('uuid','r1',json.dumps(source).encode()),)
        try:
            prepared=a.prepare_catalog(self.documents)
        except PreparationRejected as error:
            result={'stage':'preparation','reason':error.reason,'diagnostics':error.diagnostics}
        else:
            result=a.accept_in_transaction(t,prepared,request_key='unsupported-uuid')
        self.observe('registration.uuid-profile-refusal',result,
            desired='unsupported_profile' in json.dumps(original(result)),facts={'sourceFamily':'uuid'})
        self.assertEqual(self.admin.execute('SELECT rev FROM truss.schema_head').fetchone(),(0,))
