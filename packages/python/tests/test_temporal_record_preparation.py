# SPDX-License-Identifier: MIT OR Apache-2.0
"""Pure prepared-patch profile/cache controls; no installed native claim."""
import copy
import json
import unittest
from unittest.mock import Mock
from truss import temporal
from truss.contracts import LocalTimestampValue,NullValue,TextValue,MapValue
from truss.groups import RootlessOwnership
from truss._record_schema import compile_records,SchemaCompilationError
from truss._record_preparation import prepare_records
from truss._schema_memory import record_schemas
from truss._temporal_profiles import profiles,abi
from test_record_schema import prop,PIN


def records():
    wall=prop(1,'wall','localTimestamp',nullability='absent-allowed')
    wall['native_temporal']={'profile':'truss.local-timestamp/0.1','kind':'local','source':{
        'documentId':'doc','sha256':'a'*64,'record':{'module':'m','element':'r'},
        'field':{'module':'m','element':'wall'},'fieldViewPointer':'/extensions/view/fields/0'}}
    return [{'typeId':'7','definitionPin':PIN,'properties':[wall,prop(2,'name','string')]}]


class TemporalRecordPreparationTests(unittest.TestCase):
    def test_selected_local_known_property_only_and_original_bytes(self):
        schema=compile_records(records(),temporal=True)
        local=LocalTimestampValue(text='2000-02-29T12:34:56.000001')
        values=(temporal.AuthoredValue(name='wall',value=local),temporal.AuthoredValue(name='name',value=TextValue(kind='string',text='n')))
        patch=schema.prepare_patch('7',PIN,values,mode='create')
        self.assertTrue(patch.eligible);self.assertEqual(patch.wire_payload()['propsSet']['1'],{'kind':'localTimestamp','text':local.text})
        for name,value in (('unknown',local),('wall',TextValue(kind='timestamp',text='2000-02-29T12:34:56Z'))):
            self.assertFalse(schema.prepare_patch('7',PIN,(temporal.AuthoredValue(name=name,value=value),)).eligible)
        self.assertTrue(schema.prepare_patch('7',PIN,(temporal.AuthoredValue(name='wall',value=NullValue()),)).eligible)
        self.assertFalse(schema.prepare_patch('7',PIN,(),mode='create').eligible)

    def test_ordinary_schema_and_missing_or_relabelled_descriptor_stay_closed(self):
        with self.assertRaises(SchemaCompilationError):compile_records(records())
        for mutation in ('missing','wrongkind','ordinary'):
            r=records();p=r[0]['properties'][0]
            if mutation=='missing':p.pop('native_temporal')
            if mutation=='wrongkind':p['native_temporal']['kind']='instant'
            if mutation=='ordinary':p['scalar_type']='timestamp'
            with self.subTest(mutation=mutation),self.assertRaises(SchemaCompilationError):compile_records(r,temporal=True)
        with self.assertRaises(SchemaCompilationError):compile_records([],temporal=1)

    def test_cache_profile_discriminator_prevents_shared_key_aliasing(self):
        key=object();basis={}
        temporal_selection=record_schemas(key,records(),basis,temporal=True)
        self.assertIs(record_schemas(key,temporal=True),temporal_selection)
        self.assertIsNone(record_schemas(key))
        ordinary=record_schemas(key,[],basis)
        self.assertIsNot(ordinary,record_schemas(key,temporal=True))

    def test_cold_then_warm_issuer_keeps_selected_route_and_exact_native_basis(self):
        from hashlib import sha256
        documents=b'[]';raw=b'original temporal input';digest='d'*64
        basis={'documentsSha256':sha256(documents).hexdigest(),'releaseSha256':digest,
            'valueProfile':profiles()['valueProfile'],'queryAbi':abi(),'inputProfile':'truss-group-temporal-input/0.1.0',
            'declarationSha256':'a'*64,'ownerSourceSha256':'b'*64,'nativeSchemaSha256':'c'*64,'personOid':'123'}
        cursor=Mock();cursor.fetchone.return_value=(json.dumps({'basis':basis,'records':records()}).encode(),)
        input=Mock();input.operations=(temporal.CreateObject(type_definition_pin=PIN,ownership=RootlessOwnership(),
            values=(temporal.AuthoredValue(name='wall',value=LocalTimestampValue(text='2000-02-29T12:34:56.000001')),
                    temporal.AuthoredValue(name='name',value=TextValue(kind='string',text='n')))),)
        state={};cold=prepare_records(cursor,state,input,raw,documents,'release',digest,temporal=True)
        self.assertEqual(cold['profile'],'truss-python-temporal-record-patch/0.1')
        self.assertEqual(json.loads(json.dumps(cold))['basis'],basis);self.assertEqual(cold['basis'],basis);self.assertEqual(cold['valueProfile'],profiles()['valueProfile']);self.assertEqual(cold['queryAbi'],abi())
        self.assertIn('person_temporal_writer_schema_basis',cursor.execute.call_args.args[0])
        cursor.reset_mock();warm=prepare_records(cursor,state,input,raw,documents,'release',digest,temporal=True)
        self.assertEqual(warm,cold);cursor.execute.assert_not_called()
        # Selecting ordinary preparation never reads the selected temporal cache.
        self.assertIsNone(prepare_records(cursor,state,input,raw,documents,'release',digest))
        cursor.execute.assert_not_called()
