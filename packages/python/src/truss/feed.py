# SPDX-License-Identifier: MIT OR Apache-2.0
"""Complete committed transaction delivery and caller-asserted source checkpoints.

An acknowledgement asserts the consumer durably applied the delivered interval.
It does not verify another database's commit or release retained history.
"""
from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True, slots=True, kw_only=True)
class FeedCursor:
    content: bytes


@dataclass(frozen=True, slots=True, kw_only=True)
class FeedPage:
    consumer_id: str
    registration_id: str
    prior: FeedCursor
    next: FeedCursor
    content: bytes
    sha256: str
    writer_xid: str | None
    safe_watermark_xid: str
    outcome: Literal['transaction', 'empty_interval']


@dataclass(frozen=True, slots=True, kw_only=True)
class FeedConsumer:
    consumer_id: str
    registration_id: str
    checkpoint: FeedCursor
    durability: Literal['pending'] = field(default='pending', init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class FeedAcknowledged:
    checkpoint: FeedCursor
    outcome: Literal['advanced', 'equal']
    durability: Literal['pending'] = field(default='pending', init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class FeedUnavailable:
    reason: Literal['authorization', 'context', 'profile', 'integrity', 'resource', 'conflict']
    outcome: Literal['unavailable'] = field(default='unavailable', init=False)

@dataclass(frozen=True, slots=True, kw_only=True)
class FeedAckReceipt:
    """Exact source-retained evidence; destination commit is consumer-verified."""
    installation_id: str
    source_epoch: str
    consumer_id: str
    registration_id: str
    prior: FeedCursor
    next: FeedCursor
    feed_sha256: str
    destination_id: str
    request_sha256: str
    publication_id: str
    receipt_bytes: bytes
    receipt_sha256: str

@dataclass(frozen=True, slots=True, kw_only=True)
class FeedReceiptAcknowledged:
    receipt: FeedAckReceipt
    checkpoint: FeedCursor
    outcome: Literal['advanced', 'equal']
    durability: Literal['pending'] = field(default='pending', init=False)

@dataclass(frozen=True, slots=True, kw_only=True)
class FeedAckReconciled:
    """Missing is an observation, never proof of rollback or permission to republish."""
    checkpoint: FeedCursor
    outcome: Literal['matched', 'missing', 'conflicting']
    receipt: FeedAckReceipt | None
