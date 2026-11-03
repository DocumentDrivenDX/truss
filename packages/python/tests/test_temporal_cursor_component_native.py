# SPDX-License-Identifier: MIT OR Apache-2.0
"""Real native cursor custody over an authentic installed ABI1.3 capture.

The catalog is accepted through the existing ordinary public provider; no
compiled temporal inspector/compiler is simulated. Authored continuation
inputs qualify native seal/person/context custody only, never EngineRead/PV1
composition, temporal catalog acceptance or owner semantic compilation.
"""
import json
from uuid import uuid4
import psycopg
from truss import Ok,adopt_psycopg_host
from truss.catalog_runtime import _pin_cursor,_release
from truss._temporal_query_execution import _after
import temporal_native_fixture as fixture


class TemporalCursorComponentNativeTests(fixture.TemporalNativeFixture):
    def ready_cursor(self):
        def current(source):
            source['umf']='0.10.0'
            for module in source['modules']:
                for element in module['elements']:element.setdefault('name',element['id'])
        c,h,a,tx=self.ready(current,document_ids=('adoc',))
        captured=a.query_temporal_catalog_sources_in_transaction(tx,sql='SELECT "A-label" FROM "A"',document_ids=('adoc',))
        self.assertIsInstance(captured,Ok,repr(captured));request=json.loads(captured.value.request_json)
        self.assertEqual(json.loads(request['target']['bindingJson'])['queryAbi']['version'],'1.3')
        self.binding=request['target']['bindingJson'];binding=json.loads(self.binding)
        self.record=next(r for r in binding['records'] if r['identity']['element']=='A')
        # Select the actual authored composite primary Key, never first-key
        # inference. All source/field coordinates come from native capture.
        self.key=next(k for k in self.record['keys'] if k['keyId']=='a-primary')
        self.selected={'module':self.record['identity']['module'],'record':'A','key':self.key['keyId']}
        self.context=b'authored native cursor component context; no compiled owner program'
        self.packet={'version':'weft.engine-temporal-after/0.2','selectedKey':self.selected,
                     'sortValues':[{'state':'present','value':'same-prefix'},{'state':'present','value':'tail'}],
                     'keyValues':['same-prefix','tail']}
        self.assertEqual(len(self.key['propertyIds']),2)
        return c,h,a,tx

    def encode(self,c,packet=None,kinds=None):
        with c.cursor() as cursor:
            _pin_cursor(cursor)
            cursor.execute('SELECT cursor_bytes,after_json FROM truss.person_query_temporal_cursor_encode(%s::jsonb,%s,%s,%s::jsonb)',
                (self.binding,self.context,json.dumps(self.packet if packet is None else packet),json.dumps(['string','string'] if kinds is None else kinds)))
            token,after=cursor.fetchone()
        self.assertIs(type(after),str);self.assertLessEqual(len(token),65536)
        return bytes(token),after

    def decode(self,c,token,*,binding=None,context=None):
        return c.execute('SELECT truss.person_query_temporal_cursor_decode(%s::jsonb,%s,%s)',
            (self.binding if binding is None else binding,self.context if context is None else context,token)).fetchone()[0]

    def test_native_person_cursor_roundtrip_canonicalization_and_actual_acl(self):
        c,h,a,tx=self.ready_cursor();token,after=self.encode(c)
        self.assertEqual(json.loads(after),self.packet);self.assertEqual(self.decode(c,token),after)
        packet={**self.packet,'sortValues':[{'state':'missing'},{'state':'null'},
            {'state':'present','value':'2000-02-29'}, {'state':'present','value':'2024-01-01T01:00:00.1+01:00'},
            {'state':'present','value':'2000-02-29T00:00:00.1'},*self.packet['sortValues']]}
        canonical_token,canonical=self.encode(c,packet,['local','instant','date','instant','local','string','string'])
        value=json.loads(canonical)
        self.assertEqual(value['sortValues'][:2],[{'state':'missing'},{'state':'null'}])
        self.assertEqual([v['value'] for v in value['sortValues'][2:5]],
            ['2000-02-29','2024-01-01T00:00:00.100000Z','2000-02-29T00:00:00.100000'])
        self.assertEqual(self.decode(c,canonical_token),canonical)
        owner=self.admin.execute('SELECT owner_oid FROM truss.catalog_runtime_installation').fetchone()[0]
        inventory=[]
        for name,args in (('encode','jsonb,bytea,text,jsonb'),('decode','jsonb,bytea,bytea')):
            for prefix in ('','person_'):
                signature=f'truss.{prefix}query_temporal_cursor_{name}({args})'
                row=self.admin.execute("SELECT proowner,provolatile,prosecdef,pg_get_functiondef(oid),"
                    "EXISTS(SELECT 1 FROM aclexplode(coalesce(proacl,acldefault('f',proowner))) a WHERE grantee=0 AND privilege_type='EXECUTE') "
                    "FROM pg_proc WHERE oid=%s::regprocedure",(signature,)).fetchone()
                self.assertEqual((row[0],row[1],row[2],row[4]),(owner,'v',True,False))
                inventory.append({'signature':signature,'ownerOid':owner,'definition':row[3],'publicExecute':row[4]})
        print('temporal-cursor-component-inventory '+json.dumps({'release':_release()[0]['releaseId'],
            'manifestSha256':_release()[1],'functions':inventory,'scope':'native cursor custody only'},sort_keys=True))

    def test_native_person_cursor_refuses_other_actor_context_binding_and_seal(self):
        c,h,a,tx=self.ready_cursor();token,after=self.encode(c)
        damaged=json.loads(token);damaged['digest']='0'*64
        for name,kwargs,state in (('context',{'context':self.context+b' changed'},'P1002'),
                ('seal',{},'P1002'),('binding',{'binding':json.dumps({**json.loads(self.binding),'catalogRevision':999})},'0A000')):
            with self.subTest(control=name),self.assertRaises(psycopg.Error) as caught:
                with c.transaction():self.decode(c,json.dumps(damaged).encode() if name=='seal' else token,**kwargs)
            self.assertEqual(caught.exception.sqlstate,state)
        role='cursor_reader_'+uuid4().hex[:8]
        self.admin.execute(psycopg.sql.SQL('CREATE ROLE {} LOGIN').format(psycopg.sql.Identifier(role)))
        self.addCleanup(self.admin.execute,psycopg.sql.SQL('DROP ROLE {}').format(psycopg.sql.Identifier(role)))
        self.admin.execute(psycopg.sql.SQL('GRANT group_reader TO {} WITH SET FALSE').format(psycopg.sql.Identifier(role)))
        params={**psycopg.conninfo.conninfo_to_dict(self.info.connection_uri),'user':role}
        with psycopg.connect(**params,autocommit=True) as other:
            with other.transaction():
                other_host=adopt_psycopg_host(other)
                try:
                    self.assertIsInstance(other_host.adopt_transaction(),Ok)
                    with other.cursor() as pinned:_pin_cursor(pinned)
                    with self.assertRaises(psycopg.Error) as caught:
                        with other.transaction():self.decode(other,token)
                    self.assertEqual(caught.exception.sqlstate,'P1002')
                finally:other_host.detach()
            self.admin.execute(psycopg.sql.SQL('REVOKE group_reader FROM {}').format(psycopg.sql.Identifier(role)))
            with self.assertRaises(psycopg.errors.InsufficientPrivilege) as denied:
                with other.transaction():self.decode(other,token)
            self.assertEqual(denied.exception.sqlstate,'42501')
        self.assertEqual(self.decode(c,token),after)

    def test_native_decoded_complete_tuple_cannot_be_replaced_or_shortened(self):
        c,h,a,tx=self.ready_cursor();token,after=self.encode(c)
        # Closed consumer metadata uses genuine captured field identities.
        # It is not a fabricated compiled program and confers no execution permit.
        outputs=[]
        for index,property_id in enumerate(self.key['propertyIds']):
            source=next(f['identity'] for f in self.record['fields'] if f['propertyId']==property_id)
            outputs.append({'name':'key'+str(index),'source':source,'carrier':'string','missing':False,'nullable':False})
        program={'outputs':outputs,'selectedKey':self.selected,'page':{
            'version':'weft.engine-temporal-page/0.2','selectedKey':self.selected,'visibleOutputPositions':[2],
            'keyOutputPositions':[1,2],'sort':[{'field':o['source'],'direction':'asc','nulls':'last',
                'kind':'string','outputPosition':i} for i,o in enumerate(outputs,1)]}}
        original=self.decode(c,token);states=tuple(json.loads(original)['sortValues'])
        self.assertEqual(_after(program,original,expected_values=states),json.loads(after))
        for values in (states[:1],states[::-1],({'state':'present','value':'foreign'},states[1])):
            with self.subTest(tuple=values),self.assertRaises(ValueError):_after(program,original,expected_values=values)
        self.assertEqual(self.decode(c,token),after)
