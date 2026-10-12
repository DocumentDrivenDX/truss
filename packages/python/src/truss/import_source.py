"""Retained import provenance, independent of live object or edge rows."""
from dataclasses import dataclass,field
from typing import Literal

@dataclass(frozen=True,slots=True,kw_only=True)
class ImportSourceFound:
    load_id: str
    content: bytes
    sha256: str
    writer_xid: str
    outcome: Literal['found']=field(default='found',init=False)

@dataclass(frozen=True,slots=True,kw_only=True)
class ImportSourceAbsent:
    outcome: Literal['absent']=field(default='absent',init=False)

@dataclass(frozen=True,slots=True,kw_only=True)
class ImportSourceUnavailable:
    reason: Literal['authorization','context','profile','integrity','resource','observation']
    outcome: Literal['unavailable']=field(default='unavailable',init=False)
