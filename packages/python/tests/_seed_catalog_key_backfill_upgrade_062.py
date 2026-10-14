"""Seed an original native62 alternate-key report and a retained future key cell."""
import os,pickle,sys
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import truss
from truss import Ok,CatalogRegistration
from truss.contracts import TextValue,MapValue
from truss.groups import AuthoredValue,GroupSuccess
from test_catalog_key_backfill_native import CatalogKeyBackfillTests

assert Path(truss.__file__).resolve().is_relative_to(Path(os.environ['TRUSS_KEYED_UPGRADE_SOURCE_PACKAGE']).resolve())

fixture=CatalogKeyBackfillTests('test_register_existing_objects_lookup_and_query')
fixture.source_version='0.8.0';fixture.info=SimpleNamespace(connection_uri=sys.argv[1]);fixture.setUp()
c,h,a,t=fixture.ready(fixture.fields)
assert fixture.installation.release_id=='truss-catalog-runtime/0.62-candidate'
operation=replace(fixture.create(),values=fixture.create().values+(
    AuthoredValue(name='giftCode',value=TextValue(kind='string',text='retained-code')),))
context=a.group_context_in_transaction(t).value
created=fixture.apply(a,t,context.input((operation,),MapValue(entries=())),context.request('old-key-create'))
assert isinstance(created,GroupSuccess);identity=created.response.semantic.results[0].identity
h.detach();c.commit()
fixture.admin.execute('GRANT '+fixture.installation.registrar_role+' TO consumer WITH SET FALSE')
c,h,a,t=fixture.consumer();accepted=fixture.register(a,t)
assert isinstance(accepted,Ok) and isinstance(accepted.value,CatalogRegistration),repr(accepted)
h.detach();c.commit()
Path(sys.argv[2]).write_bytes(pickle.dumps((fixture.with_key(),identity,accepted.value.revision,accepted.value.report_bytes)))
for connection,host in fixture.consumer_connections:
    host.detach();connection.close()
fixture.host.detach();fixture.admin.close()
