"""Bounded one-call live traversal; complete terminals or explicit restart."""
from dataclasses import dataclass,field
from typing import Literal
from .catalog_view import CatalogDefinitionReference
from .object_read import ScalarObject

@dataclass(frozen=True,slots=True,kw_only=True)
class TraversalHop:
    relationship: CatalogDefinitionReference
    direction: Literal['outgoing','incoming','both']='outgoing'

@dataclass(frozen=True,slots=True,kw_only=True)
class TraversalComplete:
    objects: tuple[ScalarObject,...]
    catalog_revision: int
    outcome: Literal['complete']=field(default='complete',init=False)
    consistency: Literal['live']=field(default='live',init=False)

@dataclass(frozen=True,slots=True,kw_only=True)
class TraversalLimited:
    reason: Literal['path_states','result_limit','retained_bytes']
    outcome: Literal['limited']=field(default='limited',init=False)
    completeness: Literal['not_established']=field(default='not_established',init=False)
    continuation: Literal['restart']=field(default='restart',init=False)
