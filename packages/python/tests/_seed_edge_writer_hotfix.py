# SPDX-License-Identifier: MIT OR Apache-2.0
"""Leave a genuine published35 graph/receipt for the hotfix upgrade test."""
import os,pickle,sys
from pathlib import Path
from types import SimpleNamespace
import truss
from truss.contracts import TextValue
from truss.groups import AuthoredValue,StoredObjectReference,UpdateObject,GroupSuccess
from test_edge_mutations_native import EdgeMutationTests

assert Path(truss.__file__).resolve().is_relative_to(Path(os.environ['TRUSS_EDGE_HOTFIX_SOURCE_PACKAGE']).resolve())
f=EdgeMutationTests('test_link_retarget_unlink_and_original_retry')
f.info=SimpleNamespace(connection_uri=sys.argv[1]);f.setUp()
c,h,a,t,first,second,pin=f.initialized()
assert f.installation.release_id=='truss-catalog-runtime/0.68-candidate'
edge=f.link(pin,StoredObjectReference(identity=first),StoredObjectReference(identity=second))
update=UpdateObject(target=StoredObjectReference(identity=first),set=(AuthoredValue(name='A-value',value=TextValue(kind='string',text='before-hotfix')),),unset=())
result,original,request=f.run_group(a,t,(edge,update),'before-hotfix')
assert isinstance(result,GroupSuccess),repr(result)
h.detach();c.commit()
Path(sys.argv[2]).write_bytes(pickle.dumps((f.documents,first,second,result.response.semantic.results[0].identity,original,request,result.response.semantic)))
# The parent owns this disposable server and intentionally retains roles/data.
for connection,host in f.consumer_connections:
    host.detach();connection.close()
f.host.detach();f.admin.close()
