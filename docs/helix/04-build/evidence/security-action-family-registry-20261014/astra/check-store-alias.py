import json,hashlib,importlib.util
from pathlib import Path
from unittest.mock import patch
from truss.bulk_action_gateway import ActionRegistration
from truss._action_store import ActionStoreObservation
from truss.psycopg_host import PsycopgHost
out=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('truss._astra_role_before',out/'role-installer-before-snapshot.py')
module=importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name]=module;spec.loader.exec_module(module)
fixture=json.loads(Path('/Users/erik/Projects/weft/tests/mutation/fixtures/postgres-owner-plan.json').read_text())
request=fixture['request'];model=json.dumps(request['model']).encode();pin=json.dumps(request['action']).encode();prep=json.dumps(fixture['registry']['actions'][0]['preparation']).encode()
reg=ActionRegistration(lambda *a:prep);ticket=reg.register(model,pin,prep);pol=reg.family_policy(ticket)
store_alias=bytearray(b'original-store')
ctx=ActionStoreObservation(b'key',b'receipt',store_alias,b'tenant',b'epoch','installation','matches')
class Cursor:
    def execute(self,query,params=(),**kw):self.query=query;self.params=params
    def fetchone(self):return ('pg_catalog, pg_temp',)
    def fetchmany(self,n):return [(10,)]
cur=Cursor()
def text_rows(cursor,query,params=(),limit=256):
    if "current_setting('search_path')" in query:return [('pg_catalog, pg_temp',)]
    if "current_setting('server_version_num')" in query:return [('180006','read committed','off')]
    if 'SELECT installation_id::text,owner_oid::text' in query:return [('installation','100')]
    if 'SELECT rolname::text' in query:return [('owner',)+('false',)*6]
    if 'pg_catalog.encode(r.initial_receipt_bytes' in query:return [('72656365697074',store_alias.hex(),'74656e616e74','65706f6368','installation')]
    if 'SELECT oid::text' in query:return [('200',)+('false',)*7]
    if 'FROM ONLY truss.action_family_registration ORDER' in query:return [(pol.family_identity.hex(),pin.hex(),model.hex(),prep.hex(),json.dumps(['2262756c6b2d656469746f7222'],separators=(',',':')),'true','installation',store_alias.hex())]
    if 'FROM ONLY truss.action_role_binding ORDER' in query:return [(pol.family_identity.hex(),'2262756c6b2d656469746f7222','200',pin.hex(),'installation',store_alias.hex())]
    if 'aclexplode' in query:return [('100','100','false')]
    raise AssertionError(query)
host=object.__new__(PsycopgHost)
with patch.object(module,'_pin_cursor',lambda c:None),patch.object(module,'_text_rows',text_rows),patch.object(module,'installation_administrator_with_cursor',lambda *a:(None,None,True)),patch.object(PsycopgHost,'_run_operation',lambda self,tx,operation:operation(cur,None)):
    result=module.bootstrap_action_roles_in_transaction(host,object(),registration=reg,entries=((ticket,(('bulk-editor','native-role'),)),),store_context=ctx)
assert result.store_identity is store_alias
before=bytes(result.store_identity);store_alias[:]=b'changed-after-return'
assert bytes(result.store_identity)!=before
report={'status':'reproduced','actualInstallerExecuted':True,'scope':'Synthetic native query/host doubles exercise the actual captured installer control flow and returned object alias; not native issuer or SQL evidence.','storeFieldType':type(result.store_identity).__name__,'returnedIdentityAliasesInput':True,'beforeHex':before.hex(),'afterHex':bytes(result.store_identity).hex(),'sourceSha256':hashlib.sha256((out/'role-installer-before-snapshot.py').read_bytes()).hexdigest()}
(out/'store-alias-before.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
