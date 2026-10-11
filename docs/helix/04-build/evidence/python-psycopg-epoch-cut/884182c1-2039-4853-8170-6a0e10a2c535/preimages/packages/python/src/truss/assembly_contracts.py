"""Python assembly carriers; construction/admission is implemented separately.

These shapes never qualify a database, profile, host service or graph operation.
The assembly constructor must capture and validate them before publication.
"""
from dataclasses import dataclass,field
from typing import Literal
from .contracts import ProfilePin,CapabilitySelection,Absent,ABSENT

@dataclass(frozen=True,slots=True,kw_only=True)
class RecoveryConfiguration:
    registry_profile: ProfilePin
    retention: Literal['process_lifetime','restart_durable']

@dataclass(frozen=True,slots=True,kw_only=True)
class RequestReplayConfiguration:
    namespace_authority_profile: ProfilePin

@dataclass(frozen=True,slots=True,kw_only=True)
class ReferenceAssemblyConfiguration:
    assembly_id: str
    assembly_profile: ProfilePin
    recovery: RecoveryConfiguration
    database_identity: str
    schema: str
    capabilities: tuple[CapabilitySelection,...]
    request_replay: RequestReplayConfiguration | Absent = ABSENT
    interface_version: Literal['truss-reference-assembly/0.1.0'] = field(default='truss-reference-assembly/0.1.0',init=False)

@dataclass(frozen=True,slots=True,kw_only=True)
class AssemblyConstructionError:
    code: Literal['invalid_configuration','unsupported_profile','incompatible_selection']
    diagnostic_profile: ProfilePin
    path: str | Absent = ABSENT
    status: Literal['error'] = field(default='error',init=False)

@dataclass(frozen=True,slots=True,kw_only=True)
class CapabilityUnavailable:
    reason: Literal['selection','disposed']
    status: Literal['unavailable'] = field(default='unavailable',init=False)

@dataclass(frozen=True,slots=True,kw_only=True)
class AssemblyDisposed:
    state: Literal['disposed'] = field(default='disposed',init=False)
    owned_resources_released: Literal[True] = field(default=True,init=False)

