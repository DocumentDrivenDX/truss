"""Inert Python ReferenceAssembly; graph providers remain unavailable.

Construction captures host-supplied service registrations without calling them.
Count/text bounds do not establish complete Python heap or native qualification.
"""
from __future__ import annotations
from dataclasses import dataclass
from threading import Lock
from typing import Literal, overload
from .execution import TransactionHandle, Outcome
from .psycopg_host import PsycopgHost
from .installation import InstallationObservation
from .contracts import ProfilePin,CapabilitySelection,ABSENT,Absent
from .assembly_contracts import (RecoveryConfiguration,RequestReplayConfiguration,
    ReferenceAssemblyConfiguration,InstallationInspectionConfiguration,AssemblyConstructionError,CapabilityUnavailable,AssemblyDisposed)
from .execution import Ok,Error,ExecutionFailure
from .catalog_runtime import CatalogRuntimeConfiguration, CatalogReferenceAssembly

INSPECTION_ASSEMBLY_PROFILE=ProfilePin(identity='truss-reference-assembly-inspection',version='0.1.0-candidate',sha256='5df8b93c35dc11d710744b89b5a1aafd11a8c5aa957c514458db5ad5bb8c3b8d')

INSPECTION_CONSTRUCTION_DIAGNOSTIC_PROFILE=ProfilePin(identity='truss-python-inspection-assembly-construction-diagnostic',version='0.1.0-candidate',sha256='b8c53a93d67ec97a9895d3c4d862f1118758204ab06b1e625f8a0793c74c45d1')

INERT_ASSEMBLY_PROFILE=ProfilePin(identity='truss-reference-assembly-inert',version='0.1.0',sha256='3cca9dddd4b39f0325392acae67832137a9f3d6ddc2824e344f6f1a182742d09')
CONSTRUCTION_DIAGNOSTIC_PROFILE=ProfilePin(identity='truss-python-assembly-construction-diagnostic',version='0.1.0',sha256='2e42e685d6e18169d31cd34abc2d43b720f088c39b74182d5f02944d06e56b94')
FAMILIES=('catalog','mutation','group','import','direct_read','history','feed','weft_execution','bootstrap','physical_optimization','conformance')

@dataclass(frozen=True,slots=True,kw_only=True)
class RecoveryServiceRegistration:
    profile: ProfilePin
    retention: str
    implementation: object

@dataclass(frozen=True,slots=True,kw_only=True)
class NamespaceAuthorityRegistration:
    profile: ProfilePin
    implementation: object

@dataclass(frozen=True,slots=True,kw_only=True)
class HostServices:
    recovery_registry: RecoveryServiceRegistration
    request_namespace_authority: NamespaceAuthorityRegistration | None = None
    feed_proof_verifiers: tuple[object,...] = ()


def _text(value: object) -> bool:
    if type(value) is not str or not value or len(value)>1024 or '\0' in value:return False
    try:return len(value.encode('utf8'))<=4096
    except UnicodeError:return False

def _pin(value: object) -> ProfilePin:
    if (type(value) is not ProfilePin or not _text(value.identity) or not _text(value.version)
            or type(value.sha256) is not str or len(value.sha256)!=64
            or any(c not in '0123456789abcdef' for c in value.sha256)):raise ValueError('pin')
    return ProfilePin(identity=value.identity,version=value.version,sha256=value.sha256)

def _selection(value: object) -> CapabilitySelection:
    if type(value) is not CapabilitySelection or type(value.family) is not str or value.family not in FAMILIES:raise ValueError('selection')
    return CapabilitySelection(family=value.family,capability_profile=_pin(value.capability_profile),
        layout_profile=_pin(value.layout_profile),adapter_profile=_pin(value.adapter_profile),
        value_profile=_pin(value.value_profile),policy_profile=_pin(value.policy_profile))

def _error(code: Literal['invalid_configuration','unsupported_profile','incompatible_selection'],path: str | Absent = ABSENT) -> AssemblyConstructionError:
    return AssemblyConstructionError(code=code,path=path,diagnostic_profile=CONSTRUCTION_DIAGNOSTIC_PROFILE)

_ASSEMBLY_ISSUER=object()

class ReferenceAssembly:
    def __init__(self,configuration: ReferenceAssemblyConfiguration,executor: object,services: HostServices, *, _issuer: object = None) -> None:
        if _issuer is not _ASSEMBLY_ISSUER:raise ValueError('Use create_reference_assembly')
        self._configuration=configuration
        self._executor=executor
        self._services=services
        self._disposed=False
        self._lock=Lock()
    @property
    def configuration(self) -> ReferenceAssemblyConfiguration:return self._configuration
    def _select(self,selection: CapabilitySelection,family: str) -> CapabilityUnavailable:
        with self._lock:
            if self._disposed:return CapabilityUnavailable(reason='disposed')
            # No registered graph provider is shipped by this inert profile.
            return CapabilityUnavailable(reason='selection')
    def direct_reads(self,selection: CapabilitySelection) -> CapabilityUnavailable:return self._select(selection,'direct_read')
    def catalog(self,selection: CapabilitySelection) -> CapabilityUnavailable:return self._select(selection,'catalog')
    def groups(self,selection: CapabilitySelection) -> CapabilityUnavailable:return self._select(selection,'group')
    def mutations(self,selection: CapabilitySelection) -> CapabilityUnavailable:return self._select(selection,'mutation')
    def imports(self,selection: CapabilitySelection) -> CapabilityUnavailable:return self._select(selection,'import')
    def history(self,selection: CapabilitySelection) -> CapabilityUnavailable:return self._select(selection,'history')
    def feed(self,selection: CapabilitySelection) -> CapabilityUnavailable:return self._select(selection,'feed')
    def compiled_execution(self,selection: CapabilitySelection) -> CapabilityUnavailable:return self._select(selection,'weft_execution')
    def observe_readiness(self,selection: CapabilitySelection) -> Ok[CapabilityReadiness] | Error:
        try:captured=_selection(selection)
        except ValueError:return Error(ExecutionFailure('execution_obligation','Invalid capability selection'))
        with self._lock:
            if self._disposed:return Error(ExecutionFailure('execution_obligation','Assembly disposed'))
            if captured not in self._configuration.capabilities:
                return Error(ExecutionFailure('execution_obligation','Capability selection is not configured'))
            return Ok(CapabilityReadiness(selection=captured,state='unverified'))
    def dispose(self) -> AssemblyDisposed:
        with self._lock:
            self._disposed=True
            # Inert assembly owns no native resources. Never dispose its executor.
            return AssemblyDisposed()

@dataclass(frozen=True,slots=True,kw_only=True)
class CapabilityReadiness:
    selection: CapabilitySelection
    state: Literal['unverified'] = 'unverified'
    interface_version: Literal['truss-capability-readiness/0.1.0'] = 'truss-capability-readiness/0.1.0'

    def __post_init__(self) -> None:
        if type(self.state) is not str or self.state!='unverified':raise ValueError('Only unverified readiness is produced')
        if type(self.interface_version) is not str or self.interface_version!='truss-capability-readiness/0.1.0':raise ValueError('Unsupported readiness interface')


@overload
def create_reference_assembly(configuration: ReferenceAssemblyConfiguration,executor: object,host_services: HostServices) -> Ok[ReferenceAssembly] | AssemblyConstructionError: ...

@overload
def create_reference_assembly(configuration: InstallationInspectionConfiguration,executor: PsycopgHost,host_services: None = None) -> Ok[InstallationInspectionAssembly] | AssemblyConstructionError: ...

@overload
def create_reference_assembly(configuration: CatalogRuntimeConfiguration,executor: PsycopgHost,host_services: None = None) -> Ok[CatalogReferenceAssembly] | AssemblyConstructionError: ...

def create_reference_assembly(configuration: ReferenceAssemblyConfiguration | InstallationInspectionConfiguration | CatalogRuntimeConfiguration,executor: object,host_services: HostServices | None = None) -> Ok[ReferenceAssembly | InstallationInspectionAssembly | CatalogReferenceAssembly] | AssemblyConstructionError:
    """Construct the selected assembly without opening or settling a connection."""
    if type(configuration) is CatalogRuntimeConfiguration and host_services is None:
        try:return Ok(CatalogReferenceAssembly(configuration,executor))
        except ValueError:return _error('incompatible_selection','catalog_runtime')
    if type(configuration) is InstallationInspectionConfiguration:
        return _create_inspection_assembly(configuration,executor,host_services)
    if type(configuration) is not ReferenceAssemblyConfiguration:return _error('invalid_configuration')
    if type(configuration.interface_version) is not str or configuration.interface_version!='truss-reference-assembly/0.1.0':return _error('invalid_configuration','interface_version')
    for name,value in (('assembly_id',configuration.assembly_id),('database_identity',configuration.database_identity),('schema',configuration.schema)):
        if not _text(value):return _error('invalid_configuration',name)
    try:profile=_pin(configuration.assembly_profile)
    except ValueError:return _error('invalid_configuration','assembly_profile')
    if profile!=INERT_ASSEMBLY_PROFILE:return _error('unsupported_profile','assembly_profile')
    recovery=configuration.recovery
    if type(recovery) is not RecoveryConfiguration or type(recovery.retention) is not str or recovery.retention not in ('process_lifetime','restart_durable'):
        return _error('invalid_configuration','recovery')
    try:registry_pin=_pin(recovery.registry_profile)
    except ValueError:return _error('invalid_configuration','recovery')
    if type(host_services) is not HostServices or type(host_services.recovery_registry) is not RecoveryServiceRegistration:
        return _error('incompatible_selection','host_services')
    service=host_services.recovery_registry
    try:actual=_pin(service.profile)
    except ValueError:return _error('incompatible_selection','recovery')
    if type(service.retention) is not str or actual!=registry_pin or service.retention!=recovery.retention or service.implementation is None:
        return _error('incompatible_selection','recovery')
    if type(host_services.feed_proof_verifiers) is not tuple or host_services.feed_proof_verifiers:
        return _error('unsupported_profile','host_services')
    replay=configuration.request_replay;authority=host_services.request_namespace_authority
    captured_replay=ABSENT;captured_authority=None
    if replay is not ABSENT:
        if type(replay) is not RequestReplayConfiguration or type(authority) is not NamespaceAuthorityRegistration:
            return _error('incompatible_selection','request_replay')
        try:
            replay_pin=_pin(replay.namespace_authority_profile);authority_pin=_pin(authority.profile)
        except ValueError:return _error('incompatible_selection','request_replay')
        if replay_pin!=authority_pin or authority.implementation is None:return _error('incompatible_selection','request_replay')
        captured_replay=RequestReplayConfiguration(namespace_authority_profile=replay_pin)
        captured_authority=NamespaceAuthorityRegistration(profile=authority_pin,implementation=authority.implementation)
    elif authority is not None:return _error('incompatible_selection','request_replay')
    values=configuration.capabilities
    if type(values) is not tuple or not 1<=len(values)<=128:return _error('invalid_configuration','capabilities')
    try:capabilities=tuple(_selection(v) for v in values)
    except ValueError:return _error('incompatible_selection','capabilities')
    if len(set(capabilities))!=len(capabilities):return _error('incompatible_selection','capabilities')
    if executor is None:return _error('invalid_configuration','host_services')
    captured=ReferenceAssemblyConfiguration(assembly_id=configuration.assembly_id,assembly_profile=profile,
        recovery=RecoveryConfiguration(registry_profile=registry_pin,retention=recovery.retention),
        database_identity=configuration.database_identity,schema=configuration.schema,
        capabilities=capabilities,request_replay=captured_replay)
    services=HostServices(recovery_registry=RecoveryServiceRegistration(profile=actual,retention=service.retention,implementation=service.implementation),request_namespace_authority=captured_authority)
    return Ok(ReferenceAssembly(captured,executor,services,_issuer=_ASSEMBLY_ISSUER))


class InstallationInspectionAssembly:
    """Caller-owned transaction diagnostic; no graph providers or readiness claim.

    Disposal waits for an in-flight inspection to finish. It then refuses later
    inspections without issuing SQL and leaves the caller-owned host attached.
    """
    def __init__(self,configuration: InstallationInspectionConfiguration,host: PsycopgHost,*,_issuer: object = None) -> None:
        if _issuer is not _ASSEMBLY_ISSUER:raise ValueError('Use create_reference_assembly')
        self._configuration=configuration
        self._host=host
        self._disposed=False
        self._lock=Lock()

    @property
    def configuration(self) -> InstallationInspectionConfiguration:return self._configuration

    def inspect_installation(self,transaction: TransactionHandle) -> Outcome[InstallationObservation]:
        from .installation import inspect_installation_in_transaction
        with self._lock:
            if self._disposed:
                return Error(ExecutionFailure('execution_obligation','Assembly disposed'))
            return inspect_installation_in_transaction(self._host,transaction)

    def dispose(self) -> AssemblyDisposed:
        with self._lock:
            self._disposed=True
            return AssemblyDisposed()


def _inspection_error(code: Literal['invalid_configuration','unsupported_profile','incompatible_selection'],path: str) -> AssemblyConstructionError:
    return AssemblyConstructionError(code=code,path=path,diagnostic_profile=INSPECTION_CONSTRUCTION_DIAGNOSTIC_PROFILE)

def _create_inspection_assembly(configuration: InstallationInspectionConfiguration,executor: object,host_services: object) -> Ok[InstallationInspectionAssembly] | AssemblyConstructionError:
    from .psycopg_host import PsycopgHost
    if not _text(configuration.assembly_id):return _inspection_error('invalid_configuration','assembly_id')
    if type(configuration.interface_version) is not str or configuration.interface_version!='truss-installation-inspection-assembly/0.1.0':
        return _inspection_error('invalid_configuration','interface_version')
    try:profile=_pin(configuration.assembly_profile)
    except ValueError:return _inspection_error('invalid_configuration','assembly_profile')
    if profile!=INSPECTION_ASSEMBLY_PROFILE:return _inspection_error('unsupported_profile','assembly_profile')
    if type(executor) is not PsycopgHost or host_services is not None:
        return _inspection_error('incompatible_selection','host_services')
    captured=InstallationInspectionConfiguration(assembly_id=configuration.assembly_id,assembly_profile=profile)
    return Ok(InstallationInspectionAssembly(captured,executor,_issuer=_ASSEMBLY_ISSUER))
