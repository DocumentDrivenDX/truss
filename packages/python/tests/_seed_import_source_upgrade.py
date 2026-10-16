"""Populate source rows using an independently installed published predecessor."""
import json,pickle,sys
from pathlib import Path
from types import SimpleNamespace
from truss import Ok
from truss.contracts import MapValue,MapEntry,TextValue
from truss.imports import ImportReported,ImportCreated
from test_import_runtime_native import ImportRuntimeTests
fixture=ImportRuntimeTests()
fixture.info=SimpleNamespace(connection_uri=sys.argv[1])
fixture.setUp()
connection,host,assembly,tx=fixture.ready(document_ids=('adoc',))
context=assembly.import_context_in_transaction(tx).value
source=MapValue(entries=(MapEntry(key='author',value=TextValue(kind='string',text='original')),))
records=tuple(fixture.record(assembly,tx,label='legacy-'+str(i),source=source) for i in range(2))
input=context.input(records,load_id='original-load',asserted_origin=MapValue(entries=()))
result=assembly.import_in_transaction(tx,input,documents=fixture.documents)
assert isinstance(result,ImportReported),repr(result)
assert all(isinstance(o,ImportCreated) for o in result.report.outcomes),repr(result)
host.detach();connection.commit()
Path(sys.argv[2]).write_bytes(pickle.dumps((fixture.documents,input,tuple(o.identity for o in result.report.outcomes))))
for connection,host in fixture.consumer_connections:
 host.detach();connection.close()
fixture.admin.close()
