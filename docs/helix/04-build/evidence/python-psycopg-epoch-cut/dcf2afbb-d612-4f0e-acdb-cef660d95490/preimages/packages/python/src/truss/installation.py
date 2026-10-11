"""Public installation footprint observation, without readiness authority.

Only PostgreSQL system catalogs are read. No Truss relation body, report,
revision, lifecycle control or installer is invoked. A present namespace is not
proof of an installed runtime. The observation belongs to the caller's current
snapshot and is not a stable installation marker.
"""
from dataclasses import dataclass
from typing import Literal
from .host import HostConnection
from .execution import Ok, Error, Outcome, ExecutionFailure

_RELATIONS=('schema_head','schema_rev','schema_doc','catalog_acceptance_report',
            'installation_admission','row_home_operation')
_QUERY="""SELECT
 EXISTS(SELECT 1 FROM pg_catalog.pg_namespace WHERE nspname OPERATOR(pg_catalog.=) 'truss')::pg_catalog.text,
"""+',\n'.join(
    "(SELECT c.relkind::pg_catalog.text FROM pg_catalog.pg_class c "
    "JOIN pg_catalog.pg_namespace n ON n.oid OPERATOR(pg_catalog.=) c.relnamespace "
    "WHERE n.nspname OPERATOR(pg_catalog.=) 'truss' AND c.relname OPERATOR(pg_catalog.=) '"+name+"')"
    for name in _RELATIONS)

@dataclass(frozen=True,slots=True)
class InstallationRelationObservation:
    name: str
    # None means the catalog contained no relation of this exact name.
    kind: str | None

@dataclass(frozen=True,slots=True)
class InstallationObservation:
    namespace_present: bool
    relations: tuple[InstallationRelationObservation,...]
    readiness: Literal['unverified'] = 'unverified'
    scope: Literal['current_snapshot_catalog_footprint'] = 'current_snapshot_catalog_footprint'


def inspect_installation(connection: HostConnection) -> Outcome[InstallationObservation]:
    """Observe the fixed Truss namespace through the public host mediator.

    Never begin, settle, retry or close the host transaction. Exceptions from
    the host mediator propagate; this diagnostic issues no recovery reference
    or transaction-usability guarantee. A malformed completed response yields an Error,
    never an absent-installation claim. No application data is disclosed.
    """
    if type(connection) is not HostConnection:
        return Error(ExecutionFailure('execution_obligation','Public HostConnection required'))
    rows=connection.run_non_lifecycle(_QUERY)
    if (type(rows) is not list or len(rows)!=1 or type(rows[0]) not in (list,tuple)
            or len(rows[0])!=1+len(_RELATIONS)
            or type(rows[0][0]) is not str or rows[0][0] not in ('true','false')
            or any(value is not None and (type(value) is not str or len(value)!=1)
                   for value in rows[0][1:])):
        return Error(ExecutionFailure('execution_obligation','Invalid installation footprint response'))
    present=rows[0][0]=='true'
    if not present and any(value is not None for value in rows[0][1:]):
        return Error(ExecutionFailure('execution_obligation','Inconsistent installation footprint response'))
    return Ok(InstallationObservation(namespace_present=present,relations=tuple(
        InstallationRelationObservation(name,kind) for name,kind in zip(_RELATIONS,rows[0][1:],strict=True))))
