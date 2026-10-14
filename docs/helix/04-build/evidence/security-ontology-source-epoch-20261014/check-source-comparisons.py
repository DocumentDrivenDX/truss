"""Replay original-carrier comparison controls; never issuer authentication."""
from pathlib import Path
from dataclasses import replace
from hashlib import sha256
import json
from truss._security_graph_source import PreparedGraphSecuritySource,snapshot_graph_security_source
root=Path(__file__).resolve().parent
value=PreparedGraphSecuritySource(*((root/f).read_bytes() for f in ('physical-request.json','compiler-output.json','accepted-catalog.json','compiler-request.json')))
snapshot_graph_security_source(value)
def changed(change):
 request=json.loads(value.native_dependencies);binding=json.loads(request['bindingJson']);change(binding)
 request['bindingJson']=json.dumps(binding,separators=(',',':'));raw=json.dumps(request,separators=(',',':')).encode()
 output=json.loads(value.original_response);output['sourceRequestSha256']=sha256(raw).hexdigest();output['bindingSha256']=sha256(request['bindingJson'].encode()).hexdigest()
 return replace(value,native_dependencies=raw,original_response=json.dumps(output).encode())
def bool_census(binding):
 census=json.loads(binding['inventoryJson']);census['inventory']['types'][0]['type_id']=True;binding['inventoryJson']=json.dumps(census)
controls=[changed(lambda b:b.update(nativeSchemaRevision=1)),changed(bool_census),changed(lambda b:b['physicalModule']['pin'].update(revision='1')),changed(lambda b:b['physicalModule']['pin'].update(revision='r2')),replace(value,native_dependencies=value.native_dependencies+b' ')]
for bad in controls:
 try:snapshot_graph_security_source(bad)
 except (ValueError,KeyError,TypeError):pass
 else:raise AssertionError('Altered source accepted')
print('Original snapshot and five source comparison refusals pass')
