"""Produce real native64 object and edge transitions through published Python."""
import os,pickle,sys
from pathlib import Path
from types import SimpleNamespace
import truss
from truss.contracts import TextValue
from truss.groups import AuthoredValue,StoredObjectReference,UpdateObject,GroupSuccess
from test_edge_mutations_native import EdgeMutationTests

assert Path(truss.__file__).resolve().is_relative_to(Path(os.environ['TRUSS_OWNED_UPGRADE_SOURCE_PACKAGE']).resolve())
f=EdgeMutationTests('test_link_retarget_unlink_and_original_retry')
f.info=SimpleNamespace(connection_uri=sys.argv[1]);f.setUp()
c,h,a,t,first,second,pin=f.initialized()
assert f.installation.release_id==os.environ.get('TRUSS_OWNED_UPGRADE_SOURCE_RELEASE','truss-catalog-runtime/0.64-candidate')
edge=f.link(pin,StoredObjectReference(identity=first),StoredObjectReference(identity=second))
update=UpdateObject(target=StoredObjectReference(identity=first),set=(AuthoredValue(name='value',value=TextValue(kind='string',text='before-upgrade')),),unset=())
result,input,request=f.run_group(a,t,(edge,update),'pre-owned-transitions')
assert isinstance(result,GroupSuccess),repr(result)
h.detach();c.commit()
Path(sys.argv[2]).write_bytes(pickle.dumps((f.documents,first,result.response.semantic.results[0].identity,input,request,result.response.semantic)))
f.doCleanups()
