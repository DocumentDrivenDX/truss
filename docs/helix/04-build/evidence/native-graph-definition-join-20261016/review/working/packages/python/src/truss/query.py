"""Public compiled-query results. Numbers remain exact Python values."""
from decimal import Decimal
from datetime import datetime
from dataclasses import dataclass, field
from typing import Literal, Mapping, TypeAlias
from .contracts import TextValue

@dataclass(frozen=True, slots=True)
class QueryAbsent:
    state: Literal['absent'] = field(default='absent', init=False)

@dataclass(frozen=True, slots=True)
class QueryRelatedKeys:
    items: tuple[tuple[str | bool | int | Decimal, ...], ...]
    truncated: bool

QueryValue: TypeAlias = str | bool | int | Decimal | TextValue | None | QueryAbsent | QueryRelatedKeys | tuple['QueryValue', ...] | Mapping[str, 'QueryValue']

@dataclass(frozen=True, slots=True)
class QueryReadPosition:
    """Committed lower bound captured before a query; separate from receipt tokens."""
    value: str
    at: datetime
    caller_xid_assigned: bool
    semantics: Literal['committed-lower-bound'] = field(default='committed-lower-bound', init=False)

@dataclass(frozen=True, slots=True)
class QueryRows:
    columns: tuple[str, ...]
    rows: tuple[tuple[QueryValue, ...], ...]
    catalog_revision: int
    as_of: QueryReadPosition | None = None
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
    sort_values: tuple[QueryValue, ...] | None = None

@dataclass(frozen=True, slots=True)
class QueryPage:
    columns: tuple[str, ...]
    rows: tuple[tuple[QueryValue, ...], ...]
    catalog_revision: int
    next_cursor: QueryPageCursor | None
    as_of: QueryReadPosition | None = None
    next_sort_values: tuple[QueryValue, ...] | None = None
    outcome: Literal['page'] = field(default='page', init=False)

@dataclass(frozen=True, slots=True)
class QueryCatalogSources:
    """Original admitted compiler inputs for an inert build-time catalog.

    These bytes grant no authority; every execution reacquires native context.
    """
    request_json: str
