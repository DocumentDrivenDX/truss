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
    """A known fresh-install preflight result, before installation DDL begins."""
    code: Literal['busy', 'invalid_roles', 'unsupported_postgres', 'already_installed',
                  'incompatible', 'unauthorized', 'role_exists', 'read_only']
    outcome: Literal['refused'] = field(default='refused', init=False)


LifecycleStatusResult: TypeAlias = PersonRuntimeStatus | LifecycleRefused
AdminRecoveryResult: TypeAlias = AdminInstallRecovery | LifecycleRefused

__all__ = ['PersonRuntimeStatus', 'AdminInstallRecovery', 'LifecycleRefused',
           'InstallRefused', 'LifecycleStatusResult', 'AdminRecoveryResult']
