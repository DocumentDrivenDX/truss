import json,hashlib,copy
from pathlib import Path
from dataclasses import replace
from unittest.mock import patch
import truss._action_store as storemod
import truss._action_role_installation as installmod
from truss.psycopg_host import PsycopgHost
from truss.execution import Error
from truss.bulk_action_gateway import ActionRegistration
root=Path('/private/tmp/truss-security-main-integration');out=Path(__file__).resolve().parent
report=json.loads((root/'docs/helix/04-build/evidence/action-store-20261014/receipt.json').read_bytes())
raw=bytes.fromhex(report['actionStore']['receiptHex']);r=json.loads(raw)
def original():
    return storemod.ActionStoreObservation(bytes.fromhex(r['registrationKeyHex']),raw,bytes.fromhex(r['storeIdentityHex']),bytes.fromhex(r['tenantIdentityHex']),bytes.fromhex(r['epochIdentityHex']),r['installationId'],'matches')
checks=[]
def passed(name):checks.append({'name':name,'status':'passed'})
# Execute the actual installer preflight, without admitting any host/native work.
host=object.__new__(PsycopgHost);registry=ActionRegistration(lambda *a:b'')
for field in ('registration_key','receipt_bytes','store_identity','tenant_identity','epoch_identity'):
    for carrier in (bytearray,memoryview):
        bad=replace(original(),**{field:carrier(getattr(original(),field))})
        with patch.object(PsycopgHost,'_run_operation') as operation:
            result=installmod.bootstrap_action_roles_in_transaction(host,None,registration=registry,entries=(),store_context=bad)
            assert isinstance(result,Error);operation.assert_not_called()
        passed(field+'-'+carrier.__name__+'-before-host')
for badraw in (b'['*2000+b'0'+b']'*2000,b'\xff',b'{',b'{}'):
    context=replace(original(),receipt_bytes=badraw)
    try:storemod._capture_action_store_context(context)
    except ValueError:pass
    else:raise AssertionError('malformed receipt accepted')
    with patch.object(PsycopgHost,'_run_operation') as operation:
        result=installmod.bootstrap_action_roles_in_transaction(host,None,registration=registry,entries=(),store_context=context)
        assert isinstance(result,Error);operation.assert_not_called()
    passed('malformed-receipt-'+hashlib.sha256(badraw).hexdigest()[:8])
# Mutation at the first call to the receipt parser must not change retained slots.
context=original();expected=original();reader=storemod._receipt
mutations={'registration_key':b'other','receipt_bytes':b'other','store_identity':b'other','tenant_identity':b'other','epoch_identity':b'other','installation_id':'other','binding_correspondence':'fenced','authority':True}
def mutating_reader(data):
    for key,value in mutations.items():object.__setattr__(context,key,value)
    return reader(data)
with patch.object(storemod,'_receipt',mutating_reader):captured=storemod._capture_action_store_context(context)
assert captured==expected and captured is not context
passed('all-eight-original-slots-mutated-during-parse-private-copy-retained')
# Actual native-comparison Python, with finite synthetic query rows only.
expected_row=(raw.hex(),expected.store_identity.hex(),expected.tenant_identity.hex(),expected.epoch_identity.hex(),expected.installation_id)
class Cursor:
    def __init__(self,mutate=None):self.queries=[];self.mutate=mutate
    def execute(self,query,*args,**kw):
        self.queries.append(query)
        if self.mutate:self.mutate();self.mutate=None
for name,rows,identity,refuse in [('valid',[expected_row],expected.installation_id,False),('missing',[],expected.installation_id,True),('duplicate',[expected_row,expected_row],expected.installation_id,True),('wrong-installation-input',[expected_row],'other',True)]+[(f'changed-native-field-{i}',[tuple('changed' if j==i else v for j,v in enumerate(expected_row))],expected.installation_id,True) for i in range(5)]:
    cursor=Cursor()
    with patch.object(storemod,'_text_rows',side_effect=lambda cursor,q,*a,**kw: [('180006','read committed','off','none')] if 'server_version_num' in q else rows):
        try:storemod.verify_action_store_enrollment_context_with_cursor(cursor,original(),identity)
        except ValueError:assert refuse,name
        else:assert not refuse,name
    assert cursor.queries==['LOCK TABLE ONLY truss.action_store_registration IN SHARE MODE NOWAIT']
    passed('enrollment-comparator-'+name)
context=original();cursor=Cursor(lambda:object.__setattr__(context,'store_identity',b'changed-after-native-entry'))
with patch.object(storemod,'_text_rows',side_effect=lambda cursor,q,*a,**kw: [('180006','read committed','off','none')] if 'server_version_num' in q else [expected_row]):storemod.verify_action_store_enrollment_context_with_cursor(cursor,context,expected.installation_id)
passed('enrollment-original-object-mutation-after-cut-entry-ignored')
for i,value in enumerate(('180005','repeatable read','on','other')):
    state=list(('180006','read committed','off','none'));state[i]=value;cursor=Cursor()
    with patch.object(storemod,'_text_rows',return_value=[tuple(state)]):
        try:storemod.verify_action_store_enrollment_context_with_cursor(cursor,original(),expected.installation_id)
        except ValueError as exc:assert str(exc)=='Original native administrative enrollment context required'
        else:raise AssertionError('wrong native context accepted')
    assert not cursor.queries
    passed('native-enrollment-profile-field-'+str(i)+'-refused-before-lock')
# Original owner exports are replayed in this temp directory, never over source.
artifacts=['docs/helix/02-design/models/truss-action-role-registry-storage-0.1.proposal.umf.json','docs/helix/04-build/action-role-registry.generated.sql','packages/python/src/truss/_security_bootstrap/action-role-registry-storage.sql']
for path in artifacts:
    assert (root/path).read_bytes()==(out/path).read_bytes(),path
    passed('original-owner-build-byte-equality:'+path)
result={'status':'passed','count':len(checks),'sourceSha256':{str(Path(m.__file__).relative_to(root)):hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest() for m in (storemod,installmod)},'checks':checks,'scope':'Actual Python immutable input preflight/capture and exact comparison over finite synthetic native rows, plus original owner export byte equality. Host/native authority guards are not executed or established by these controls.'}
(out/'final-custody-results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':'passed','count':len(checks)}))
