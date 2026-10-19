# SPDX-License-Identifier: MIT OR Apache-2.0
"""Original catalog/issued compiler model correspondence; no native admission."""
import hashlib,json,os,unittest
from pathlib import Path
from truss import Ok,CatalogDocument,adopt_psycopg_host
from truss._native_source_observation import capture_native_source_observation_with_cursor
from truss._owner_evidence_json import decode_owner_evidence_json
import test_catalog_runtime_native as base

@unittest.skipUnless(os.environ.get('TRUSS_MODEL_CORRESPONDENCE_QUALIFICATION')=='1','explicit serialized native correspondence required')
class NativeModelCorrespondenceTests(base.PublicCatalogRuntimeTests):
    for name in tuple(n for n in dir(base.PublicCatalogRuntimeTests) if n.startswith('test_')):locals()[name]=None
    def retain(self,name,raw):
        out=Path(os.environ['TRUSS_MODEL_CORRESPONDENCE_EVIDENCE']);out.mkdir(parents=True,exist_ok=True);(out/name).write_bytes(raw)
    def test_exact_original_model_native_catalog_and_ordered_keys(self):
        import weft,weft.weft as weft_native
        self.__class__.postmaster_pid=int((self.info.data_directory/'postmaster.pid').read_text().splitlines()[0])
        fixture=Path(os.environ['TRUSS_MODEL_CORRESPONDENCE_REQUEST']);original=fixture.read_bytes();request=decode_owner_evidence_json(original)
        self.assertEqual(len(request['modules']),1);module=request['modules'][0];pin=module['pin'];raw=module['documentJson'].encode()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),pin['sha256']);self.assertEqual(pin['documentId'],'domain')
        self.install();connection,host,assembly,transaction=self.consumer()
        prepared=assembly.prepare_catalog((CatalogDocument(pin['documentId'],pin['revision'],raw),),source_version='0.8.0',bun_executable=os.environ['TRUSS_BUN_EXECUTABLE'])
        self.assertEqual(prepared.documents[0].document.content,raw)
        accepted=assembly.accept_in_transaction(transaction,prepared,request_key='exact-weft-model')
        self.assertIsInstance(accepted,Ok,str(host._custody.last_attempt.error));host.detach();connection.commit()
        accepted_request=json.dumps({'modules':[{'pin':pin,'documentJson':module['documentJson']}]},separators=(',',':')).encode()
        self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin,operation_timeout_ms=60000);self.tx=self.host.adopt_transaction().value
        def capture_actual(cursor,actual):
            capture=capture_native_source_observation_with_cursor(cursor,accepted_request)
            parent=weft.prepare_application_lineage(original.decode());context=parent.prepare_current_presence()
            requirements=context.model_requirements_json().encode()
            return capture,requirements
        self.assertEqual(hashlib.sha256(Path(weft_native.__file__).read_bytes()).hexdigest(),'9f1c7bc60f070734f2e935ba53e82a0bd22002e9e738c34f65623ca8bac978dd')
        observed=self.host._run_operation(self.tx,capture_actual)
        self.assertIsInstance(observed,Ok,str(self.host._custody.last_attempt.error));capture,requirements=observed.value
        issued=decode_owner_evidence_json(requirements);self.assertEqual(issued['sourceRequestJson'],original.decode());self.assertEqual(issued['modelPins'],[pin])
        self.assertFalse(issued['complete']);self.assertFalse(issued['authority']);self.assertFalse(issued['securityReady'])
        assessment=decode_owner_evidence_json(capture.accepted_assessment);inventory=assessment['inventory'];self.assertEqual(assessment['modelPins'],[pin])
        # Independently authored golden, not extracted from the input model or
        # generated using native inventory iteration.
        expected={'Staff':(['staffId'],['staffId']),'Project':(['projectId'],['projectId']),'Resource':(['resourceId','salary','token'],['resourceId']),'Ownership':(['ownerId','ownerResource','ownerProject'],['ownerId']),'Assignment':(['assignmentId','assignmentStaff','assignmentProject','active'],['assignmentId'])}
        self.assertEqual(len(issued['records']),len(expected))
        issued_ids=[tuple(r['record'][k] for k in ('documentId','revision','module','element')) for r in issued['records']]
        self.assertEqual(len(set(issued_ids)),len(expected))
        issued_records={r['record']['element']:r for r in issued['records']};self.assertEqual(set(issued_records),set(expected))
        active_types=[t for t in inventory['types'] if t['retired_rev'] is None]
        self.assertEqual(len(active_types),len(expected))
        self.assertEqual(len({(t['document_id'],t['module'],t['element']) for t in active_types}),len(expected))
        self.assertEqual(len({t['type_id'] for t in active_types}),len(expected))
        types={t['element']:t for t in active_types};self.assertEqual(set(types),set(expected));native_mapping={}
        for name,(fields,key_fields) in expected.items():
            issued_record=issued_records[name];self.assertEqual(issued_record['record'],{'documentId':'domain','revision':pin['revision'],'module':'m','element':name})
            self.assertEqual([f['field']['element'] for f in issued_record['fields']],fields)
            self.assertEqual(issued_record['selectedKey'],{'id':'pk','fields':[{'documentId':'domain','revision':pin['revision'],'module':'m','element':field} for field in key_fields]})
            for field in issued_record['fields']:self.assertEqual((field['field']['documentId'],field['field']['revision'],field['field']['module']),('domain',pin['revision'],'m'))
            native=types[name];self.assertEqual((native['document_id'],native['module'],native['kind'],native['provisional']),('domain','m','record',False))
            props=[p for p in inventory['properties'] if p['type_id']==native['type_id'] and p['retired_rev'] is None]
            self.assertEqual({p['element'] for p in props},set(fields));self.assertEqual(len(props),len(fields));self.assertEqual(len({p['prop_id'] for p in props}),len(fields))
            for prop in props:self.assertEqual((prop['definition_document_id'],prop['declaration_module'],prop['home']),('domain','m','json'))
            keys=[k for k in inventory['keys'] if k['type_id']==native['type_id'] and k['retired_rev'] is None];self.assertEqual(len(keys),1);self.assertEqual(keys[0]['key_id'],'pk')
            by_id={p['prop_id']:p['element'] for p in props};self.assertEqual([by_id[k] for k in keys[0]['prop_ids']],key_fields)
            native_mapping[name]={'typeId':native['type_id'],'properties':{p['element']:p['prop_id'] for p in props},'keyNum':keys[0]['key_num'],'orderedKeyFields':[by_id[k] for k in keys[0]['prop_ids']]}
        for name,value in [('issued-requirements.json',requirements),('weft-original-request.json',original),('accepted-request.json',accepted_request),('accepted-assessment.json',capture.accepted_assessment),('native-inventory.json',capture.native_inventory),('runtime-release.json',capture.runtime_release),('observation-report.json',capture.report)]:self.retain(name,value)
        self.retain('native-field-key-mapping.json',json.dumps(native_mapping,indent=2).encode())
        self.retain('scope.json',json.dumps({'complete':False,'authority':False,'securityReady':False,'nativeAdmission':'required','scope':'Actual original host and byte-exact existing Weft model accepted by Truss. Independently expected native identities/order only. Actual candidate borrowed compiler requirements are compared in the original operation; codec/graph correspondence, native binding, authenticated Subject/current authority and guarded release remain required.'},indent=2).encode())
