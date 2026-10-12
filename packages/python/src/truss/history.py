"""Exact retained native history, independent of live canonical rows."""
from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True,slots=True,kw_only=True)
class HistoryEntity:
    kind: Literal['object','edge']
    document_id: str
    module_id: str
    definition_id: str
    id: int


@dataclass(frozen=True,slots=True,kw_only=True)
class HistoryCursor:
    content: bytes


@dataclass(frozen=True,slots=True,kw_only=True)
class RetainedHistoryEvent:
    content: bytes
    sha256: str
    writer_xid: str
    seq: str
    version: int


@dataclass(frozen=True,slots=True,kw_only=True)
class HistoryPage:
    events: tuple[RetainedHistoryEvent,...]
    continuation: HistoryCursor | None
    safe_watermark_xid: str
    outcome: Literal['page'] = field(default='page',init=False)


@dataclass(frozen=True,slots=True,kw_only=True)
class HistoricalRecord:
    record: bytes
    event: RetainedHistoryEvent
    outcome: Literal['record'] = field(default='record',init=False)


@dataclass(frozen=True,slots=True,kw_only=True)
class HistoricalDeleted:
    deletion_version: int
    before: bytes
    event: RetainedHistoryEvent
    outcome: Literal['deleted'] = field(default='deleted',init=False)


@dataclass(frozen=True,slots=True,kw_only=True)
class HistoryUnavailable:
    reason: Literal['authorization','profile','resource','observation','integrity','context','history']
    outcome: Literal['unavailable'] = field(default='unavailable',init=False)
