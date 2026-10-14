"""Create a real optional-only rebind using the installed native60 predecessor."""
import os,pickle,sys
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from truss import Ok
from truss.contracts import BooleanValue,TextValue,MapValue
from truss.groups import AuthoredValue,GroupSuccess
from test_catalog_rebind_native import CatalogRebindTests

fixture=CatalogRebindTests('test_register_rebind_read_report_history_and_retry')
fixture.source_version='0.8.0';fixture.info=SimpleNamespace(connection_uri=sys.argv[1]);fixture.setUp()
c,h,a,t=fixture.ready(fixture.fields)
operation=replace(fixture.create(),values=fixture.create().values+(
    AuthoredValue(name='giftWrap',value=BooleanValue(value=True)),
    AuthoredValue(name='laterRequired',value=TextValue(kind='string',text='retained later'))))
context=a.group_context_in_transaction(t).value
created=fixture.apply(a,t,context.input((operation,),MapValue(entries=())),context.request('old-rebind-create'))
assert isinstance(created,GroupSuccess);identity=created.response.semantic.results[0].identity
h.detach();c.commit()
fixture.admin.execute('GRANT '+fixture.installation.registrar_role+' TO consumer WITH SET FALSE')
document=fixture.revised(next(d for d in fixture.documents if d.document_id=='adoc'))
c,h,a,t=fixture.consumer();prepared=a.prepare_catalog((document,),source_version='0.8.0',bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
accepted=a.accept_in_transaction(t,prepared,request_key='original-optional-rebind')
assert isinstance(accepted,Ok),repr(accepted)+' '+str(h._custody.last_attempt.error)
h.detach();c.commit()
Path(sys.argv[2]).write_bytes(pickle.dumps((document,identity,accepted.value.revision,accepted.value.report_bytes)))
for connection,host in fixture.consumer_connections:
    host.detach();connection.close()
fixture.host.detach();fixture.admin.close()
