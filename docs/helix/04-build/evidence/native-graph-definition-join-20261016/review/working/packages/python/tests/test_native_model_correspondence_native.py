"""Original catalog/issued compiler model correspondence; no native admission."""
import hashlib,json,os,unittest
from pathlib import Path
from truss import Error,Ok,CatalogDocument,adopt_psycopg_host
from truss._native_model_correspondence import capture_native_model_correspondence_with_cursor
from truss._owner_evidence_json import decode_owner_evidence_json,same_owner_evidence
import test_catalog_runtime_native as base

@unittest.skipUnless(os.environ.get('TRUSS_NATIVE_MODEL_JOIN_QUALIFICATION')=='1','explicit serialized native correspondence required')
class NativeModelCorrespondenceTests(base.PublicCatalogRuntimeTests):
    for name in tuple(n for n in dir(base.PublicCatalogRuntimeTests) if n.startswith('test_')):locals()[name]=None
    def retain(self,name,raw):
        out=Path(os.environ['TRUSS_NATIVE_MODEL_JOIN_EVIDENCE']);out.mkdir(parents=True,exist_ok=True);(out/name).write_bytes(raw)
    def test_exact_original_model_native_catalog_and_ordered_keys(self):
        import weft,weft.weft as weft_native
        self.__class__.postmaster_pid=int((self.info.data_directory/'postmaster.pid').read_text().splitlines()[0])
        fixture=Path(os.environ['TRUSS_NATIVE_MODEL_JOIN_REQUEST']);original=fixture.read_bytes();request=decode_owner_evidence_json(original)
        self.assertEqual(len(request['modules']),1);module=request['modules'][0];pin=module['pin'];raw=module['documentJson'].encode()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),pin['sha256']);self.assertEqual(pin['documentId'],'domain')
        self.install();connection,host,assembly,transaction=self.consumer()
        prepared=assembly.prepare_catalog((CatalogDocument(pin['documentId'],pin['revision'],raw),),source_version='0.8.0',bun_executable=os.environ['TRUSS_BUN_EXECUTABLE'])
        self.assertEqual(prepared.documents[0].document.content,raw)
        accepted=assembly.accept_in_transaction(transaction,prepared,request_key='exact-weft-model')
        self.assertIsInstance(accepted,Ok,str(host._custody.last_attempt.error));host.detach();connection.commit()
        accepted_request=json.dumps({'modules':[{'pin':pin,'documentJson':module['documentJson']}]},separators=(',',':')).encode()
        self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin,operation_timeout_ms=60000);self.tx=self.host.adopt_transaction().value
        parent=weft.prepare_application_lineage(original.decode());context=parent.prepare_current_presence()
        def capture_actual(cursor,actual):
            return capture_native_model_correspondence_with_cursor(cursor,current=context,accepted_request=accepted_request)
        self.assertEqual(hashlib.sha256(Path(weft_native.__file__).read_bytes()).hexdigest(),'9f1c7bc60f070734f2e935ba53e82a0bd22002e9e738c34f65623ca8bac978dd')
        observed=self.host._run_operation(self.tx,capture_actual)
        self.assertIsInstance(observed,Ok,str(self.host._custody.last_attempt.error));joined=observed.value;capture=joined.observation;requirements=joined.requirements
        self.assertIs(joined.current,context);self.assertIs(joined.parent,parent)
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

        mapping=decode_owner_evidence_json(joined.report)
        self.assertEqual(mapping['version'],'truss.native-model.correspondence/0.1-candidate')
        self.assertEqual(mapping['scope'],'actual-context-native-record-member-key-correspondence')
        for flag in ('complete','authority','securityReady'):self.assertIs(mapping[flag],False)
        self.assertEqual(mapping['nativeAdmission'],'required')
        self.assertEqual(mapping['preparationSha256'],hashlib.sha256(context.json().encode()).hexdigest())
        originals=[('accepted-request',capture.accepted_request),('accepted-assessment',capture.accepted_assessment),('runtime-release',capture.runtime_release),('native-inventory',capture.native_inventory),('issued-requirements',requirements)]
        self.assertEqual(mapping['sources'],[{'role':role,'sha256':hashlib.sha256(value).hexdigest(),'bytes':len(value)} for role,value in originals])
        object_oid=self.admin.execute("SELECT 'truss.object'::regclass::oid::text").fetchone()[0]
        physical={name:{'attnum':attnum,'typeOid':oid} for attnum,name,oid in self.admin.execute("SELECT attnum,attname,atttypid::text FROM pg_attribute WHERE attrelid='truss.object'::regclass AND attname IN ('id','type_id','props') AND NOT attisdropped").fetchall()}
        self.assertEqual({n:c['typeOid'] for n,c in physical.items()},{'id':'20','type_id':'23','props':'3802'})
        self.assertEqual(len(mapping['records']),len(expected))
        refs=[tuple(row['record'][k] for k in ('documentId','revision','module','element')) for row in mapping['records']]
        self.assertEqual(len(set(refs)),len(expected))
        self.assertEqual({row['record']['element'] for row in mapping['records']},set(expected))
        self.assertEqual(len({row['typeId'] for row in mapping['records']}),len(expected))
        for row in mapping['records']:
            name=row['record']['element'];gold=native_mapping[name];fields,key_fields=expected[name]
            ref=lambda element:{'documentId':'domain','revision':pin['revision'],'module':'m','element':element}
            self.assertEqual(row['record'],ref(name));self.assertEqual(row['typeId'],gold['typeId'])
            self.assertEqual(row['objectHome'],{'relationOid':object_oid,'columns':physical})
            self.assertEqual(row['fields'],[{'field':ref(field),'propertyId':gold['properties'][field],'jsonKey':str(gold['properties'][field])} for field in fields])
            self.assertEqual(len({f['propertyId'] for f in row['fields']}),len(fields))
            self.assertEqual(row['selectedKey'],{'id':'pk','fields':[ref(field) for field in key_fields],'keyNum':gold['keyNum'],'propertyIds':[gold['properties'][field] for field in key_fields]})
            exact={'record':ref(name),'typeId':gold['typeId'],'objectHome':{'relationOid':object_oid,'columns':physical},'fields':[{'field':ref(field),'propertyId':gold['properties'][field],'jsonKey':str(gold['properties'][field])} for field in fields],'selectedKey':{'id':'pk','fields':[ref(field) for field in key_fields],'keyNum':gold['keyNum'],'propertyIds':[gold['properties'][field] for field in key_fields]}}
            self.assertTrue(same_owner_evidence(row,exact),'Complete type-exact joined mapping required')
        self.retain('joined-report.json',joined.report)
        self.admin.execute("CREATE TEMP TABLE model_join_prior(value text);INSERT INTO model_join_prior VALUES('kept')")
        self.admin.execute('SAVEPOINT before_join_column');self.admin.execute('ALTER TABLE truss.object RENAME COLUMN props TO props_drift')
        refused=self.host._run_operation(self.tx,capture_actual)
        self.assertIsInstance(refused,Error);self.assertIn('Original native object column',str(self.host._custody.last_attempt.error))
        self.assertEqual(self.admin.execute('TABLE model_join_prior').fetchall(),[('kept',)])
        self.admin.execute('ROLLBACK TO SAVEPOINT before_join_column');self.admin.execute('RELEASE SAVEPOINT before_join_column')
        restored=self.host._run_operation(self.tx,capture_actual);self.assertIsInstance(restored,Ok,str(self.host._custody.last_attempt.error))
        self.assertEqual(restored.value.report,joined.report)
        changed=json.loads(accepted_request);changed['modules'][0]['documentJson']+=' ';changed['modules'][0]['pin']['sha256']=hashlib.sha256(changed['modules'][0]['documentJson'].encode()).hexdigest()
        refused=self.host._run_operation(self.tx,lambda cursor,actual:capture_native_model_correspondence_with_cursor(cursor,current=context,accepted_request=json.dumps(changed,separators=(',',':')).encode()))
        self.assertIsInstance(refused,Error);self.assertIn('accepted compiler source correspondence',str(self.host._custody.last_attempt.error))
        self.assertEqual(self.admin.execute('TABLE model_join_prior').fetchall(),[('kept',)])
        self.retain('join-controls.json',json.dumps({'positiveRecords':5,'positiveFields':12,'positiveSingleComponentKeys':5,'renamedNativeColumnRefused':True,'callerPriorWorkRetained':True,'restoredMetadataEquals':True,'changedOriginalSourceRefused':True,'authority':False,'nativeAdmission':'required'},indent=2).encode())
