from typing import assert_type
from truss import (ConnectedHost, connect_pg8000_host, Ok, HostServices,
    ReferenceAssemblyConfiguration, create_reference_assembly, ReferenceAssembly,
    AssemblyConstructionError, CapabilityUnavailable)
from truss.host import HostRecovery
from truss.execution import TransactionHandle

def host_consumer(sock: str) -> ConnectedHost:
    host=connect_pg8000_host(user="postgres",database="postgres",unix_sock=sock)
    assert_type(host.session.recovery,HostRecovery)
    adopted=host.session.adopt_transaction()
    if isinstance(adopted,Ok):
        assert_type(adopted.value,TransactionHandle)
        host.session.savepoint(adopted.value)
    reference=host.session.last_call_reference
    if reference is not None:host.session.recovery.observe(reference)
    host.session.rollback()
    return host

def assembly_consumer(config: ReferenceAssemblyConfiguration, services: HostServices) -> ReferenceAssembly | AssemblyConstructionError:
    result=create_reference_assembly(config,object(),services)
    if isinstance(result,Ok):
        assert_type(result.value,ReferenceAssembly)
        assert_type(result.value.catalog(config.capabilities[0]),CapabilityUnavailable)
        result.value.dispose()
        return result.value
    return result
