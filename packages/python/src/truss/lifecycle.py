# SPDX-License-Identifier: MIT OR Apache-2.0
"""Minimal runtime status and trusted installation role recovery carriers."""
from dataclasses import dataclass, field
from typing import Literal, TypeAlias

from .contracts import _Carrier


@dataclass(frozen=True, slots=True, kw_only=True)
class PersonRuntimeStatus(_Carrier):
    installation: Literal['absent', 'compatible', 'incompatible']
    catalog: Literal['empty', 'accepted', 'unknown']
    outcome: Literal['status'] = field(default='status', init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class AdminInstallRecovery(_Carrier):
    owner_role: str
    registrar_role: str
    outcome: Literal['recovered'] = field(default='recovered', init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class LifecycleRefused(_Carrier):
    reason: Literal['unauthorized', 'profile', 'observation', 'installation']
    outcome: Literal['refused'] = field(default='refused', init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class InstallRefused(_Carrier):
    """A known fresh-install refusal, including confirmed contained grant refusal."""
    code: Literal['busy', 'invalid_roles', 'unsupported_postgres', 'already_installed',
                  'incompatible', 'unauthorized', 'role_exists', 'read_only',
                  'third_party_grant']
    role_name: str | None = None
    object_class: Literal['schema', 'relation', 'sequence', 'routine', 'type', 'column'] | None = None
    phase: Literal['pre_ownership', 'post_installation'] | None = None
    outcome: Literal['refused'] = field(default='refused', init=False)

    def __post_init__(self) -> None:
        _Carrier.__post_init__(self)
        if self.code == 'third_party_grant':
            if (self.role_name is None or '\0' in self.role_name
                    or len(self.role_name.encode('utf8')) > 63
                    or self.object_class is None or self.phase is None):
                raise ValueError('Bounded third-party grant context required')
        elif any(value is not None for value in (self.role_name, self.object_class, self.phase)):
            raise ValueError('Grant context is only valid for third-party grant refusal')


LifecycleStatusResult: TypeAlias = PersonRuntimeStatus | LifecycleRefused
AdminRecoveryResult: TypeAlias = AdminInstallRecovery | LifecycleRefused

__all__ = ['PersonRuntimeStatus', 'AdminInstallRecovery', 'LifecycleRefused',
           'InstallRefused', 'LifecycleStatusResult', 'AdminRecoveryResult']
