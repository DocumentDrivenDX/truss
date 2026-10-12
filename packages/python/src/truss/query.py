"""Public compiled-query results. Numbers remain exact Python values."""
from dataclasses import dataclass, field
from typing import Literal, Mapping, TypeAlias

@dataclass(frozen=True, slots=True)
class QueryAbsent:
    state: Literal['absent'] = field(default='absent', init=False)

QueryValue: TypeAlias = str | bool | int | None | QueryAbsent | Mapping[str, 'QueryValue']

@dataclass(frozen=True, slots=True)
class QueryRows:
    columns: tuple[str, ...]
    rows: tuple[tuple[QueryValue, ...], ...]
    catalog_revision: int
    outcome: Literal['rows'] = field(default='rows', init=False)

@dataclass(frozen=True, slots=True)
class QueryDiagnostic:
    code: str
    message: str

@dataclass(frozen=True, slots=True)
class QueryRefused:
    code: Literal['unauthorized', 'invalid_query', 'unsupported_query', 'limits', 'stale_context']
    diagnostics: tuple[QueryDiagnostic, ...] = ()
    outcome: Literal['refused'] = field(default='refused', init=False)

@dataclass(frozen=True, slots=True)
class QueryUnavailable:
    reason: Literal['compiler', 'installation', 'resource', 'observation']
    outcome: Literal['unavailable'] = field(default='unavailable', init=False)
