# SPDX-License-Identifier: MIT OR Apache-2.0
"""Public directed relationship reads with exact retained scalar values."""
from dataclasses import dataclass,field
from typing import Literal
from .contracts import TypedIdentity,TextValue

@dataclass(frozen=True,slots=True,kw_only=True)
class ScalarEdge:
    identity: TypedIdentity
    source: TypedIdentity
    target: TypedIdentity
    version: int
    catalog_revision: int
    record_revision: int
    created_at: str
    updated_at: str
    order_key: str | None
    retained: tuple[tuple[str,str | bool | TextValue | None],...]

@dataclass(frozen=True,slots=True,kw_only=True)
class EdgeFound:
    edge: ScalarEdge
    outcome: Literal['found']=field(default='found',init=False)

@dataclass(frozen=True,slots=True)
class EdgeNotFound:
    outcome: Literal['not_found']=field(default='not_found',init=False)

@dataclass(frozen=True,slots=True,kw_only=True)
class EdgePageCursor:
    content: bytes

@dataclass(frozen=True,slots=True,kw_only=True)
class EdgePage:
    edges: tuple[ScalarEdge,...]
    catalog_revision: int
    continuation: EdgePageCursor | None
    consistency: Literal['live']=field(default='live',init=False)
    outcome: Literal['page']=field(default='page',init=False)
