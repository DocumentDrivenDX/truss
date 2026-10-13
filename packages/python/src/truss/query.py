"""Public compiled-query results. Numbers remain exact Python values."""
from decimal import Decimal
from dataclasses import dataclass, field
from typing import Literal, Mapping, TypeAlias
from .contracts import TextValue

@dataclass(frozen=True, slots=True)
class QueryAbsent:
    state: Literal['absent'] = field(default='absent', init=False)

@dataclass(frozen=True, slots=True)
class QueryRelatedKeys:
    items: tuple[tuple[str, ...], ...]
    truncated: bool

QueryValue: TypeAlias = str | bool | int | Decimal | TextValue | None | QueryAbsent | QueryRelatedKeys | tuple['QueryValue', ...] | Mapping[str, 'QueryValue']

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
    code: Literal['unauthorized', 'invalid_query', 'unsupported_query', 'limits', 'stale_context', 'native_domain']
    diagnostics: tuple[QueryDiagnostic, ...] = ()
    outcome: Literal['refused'] = field(default='refused', init=False)

@dataclass(frozen=True, slots=True)
class QueryUnavailable:
    reason: Literal['compiler', 'installation', 'resource', 'observation']
    outcome: Literal['unavailable'] = field(default='unavailable', init=False)

@dataclass(frozen=True, slots=True)
class QueryPageCursor:
    original_bytes: bytes

@dataclass(frozen=True, slots=True)
class QueryPage:
    columns: tuple[str, ...]
    rows: tuple[tuple[QueryValue, ...], ...]
    catalog_revision: int
    next_cursor: QueryPageCursor | None
    outcome: Literal['page'] = field(default='page', init=False)
