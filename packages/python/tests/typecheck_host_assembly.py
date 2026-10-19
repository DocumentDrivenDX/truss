# SPDX-License-Identifier: MIT OR Apache-2.0
from typing import assert_type
from truss import (ConnectedHost, connect_pg8000_host, Ok, HostServices,
    ReferenceAssemblyConfiguration, create_reference_assembly, ReferenceAssembly,
    AssemblyConstructionError, CapabilityUnavailable, HostRecovery,
    TransactionHandle, Isolation, AccessMode, BorrowedHost, adopt_pg8000_host)

def borrowed_consumer(connection: object) -> BorrowedHost:
    host=adopt_pg8000_host(connection)
    host.connection.run_non_lifecycle('SELECT 1')
    baseline=host.session.observe_host_resource_baseline()
    if isinstance(baseline,Ok):
        begun=host.session.begin()
        if isinstance(begun,Ok):
            adopted=host.session.adopt_transaction()
            if isinstance(adopted,Ok):assert_type(adopted.value,TransactionHandle)
            host.session.rollback()
    assert_type(host.detach(),bool)
    return host

def host_consumer(sock: str) -> ConnectedHost:
    host=connect_pg8000_host(user="postgres",database="postgres",unix_sock=sock)
    assert_type(host.session.recovery,HostRecovery)
    isolation: Isolation='read_committed'
    access_mode: AccessMode='read_write'
    baseline=host.session.observe_host_resource_baseline()
    if isinstance(baseline,Ok):
        begun=host.session.begin(isolation=isolation,access_mode=access_mode)
        if isinstance(begun,Ok):
            adopted=host.session.adopt_transaction(isolation=isolation,access_mode=access_mode)
            if isinstance(adopted,Ok):
                assert_type(adopted.value,TransactionHandle)
                saved=host.session.savepoint(adopted.value)
                if isinstance(saved,Ok):
                    rolled=host.session.rollback_to_savepoint(adopted.value,saved.value)
                    if isinstance(rolled,Ok):
                        host.session.release_savepoint(adopted.value,saved.value)
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
