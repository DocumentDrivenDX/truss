# SPDX-License-Identifier: MIT OR Apache-2.0
"""Bounded, whole-load-authorized audit page carriers."""
from dataclasses import dataclass, field
from typing import Literal
from .contracts import _Carrier


@dataclass(frozen=True, slots=True, kw_only=True)
class LoadAuditEntry(_Carrier):
    input_index: str
    outcome: Literal['created', 'skipped', 'rejected']
    record_kind: Literal['object', 'edge']
    identity: dict
    payload_profile: dict
    payload_sha256: str
    group_attempt_id: str | None


@dataclass(frozen=True, slots=True, kw_only=True)
class LoadAuditCursor(_Carrier):
    """Invocation-bound continuation for one sequential load-audit page."""
    invocation_id: str
    chunk_index: str
    interface_version: Literal['truss-load-audit-cursor/0.1.0'] = field(
        default='truss-load-audit-cursor/0.1.0', init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class LoadAuditListingCursor(_Carrier):
    """Opaque continuation for snapshot-bounded discovery across invocations."""
    installation_id: str
    source_epoch: str
    release_id: str
    release_sha256: str
    frontier_xid: str
    filters_sha256: str
    after_observed_at: str
    after_invocation_id: str
    profile: Literal['truss-import-load-audit-cursor/0.2'] = field(
        default='truss-import-load-audit-cursor/0.2', init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class LoadAuditChunkSummary(_Carrier):
    chunk_index: str
    observed_at: str
    created_count: str
    skipped_count: str
    rejected_count: str


@dataclass(frozen=True, slots=True, kw_only=True)
class LoadAuditInvocationSummary(_Carrier):
    """Metadata-only summary of one visible committed import invocation."""
    invocation_id: str
    load_id: str
    asserted_origin_sha256: str
    native_actor_oid: str
    native_actor_name: str
    input_sha256: str
    input_count: str
    total_chunks: str
    observed_chunk_count: str
    observed_chunks: tuple[str, ...]
    state: Literal['partial', 'complete']
    observed_at_from: str
    observed_at_until: str
    created_count: str
    skipped_count: str
    rejected_count: str
    chunks: tuple[LoadAuditChunkSummary, ...]
    next_page_cursor: LoadAuditListingCursor | None
    interface_version: Literal['truss-load-audit-summary/0.1.0'] = field(
        default='truss-load-audit-summary/0.1.0', init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class LoadAuditPage(_Carrier):
    invocation_id: str
    load_id: str
    asserted_origin_sha256: str
    native_actor: str
    native_actor_name: str
    observed_at: str
    created_count: str
    skipped_count: str
    rejected_count: str
    load_created_count: str | None
    load_skipped_count: str | None
    load_rejected_count: str | None
    input_sha256: str
    input_count: str
    total_chunks: str
    observed_chunks: tuple[str, ...]
    state: Literal['partial', 'complete']
    entries: tuple[LoadAuditEntry, ...]
    next_cursor: LoadAuditCursor | None
    next_page_cursor: LoadAuditListingCursor | None = None
    interface_version: Literal['truss-load-audit-page/0.1.0'] = field(
        default='truss-load-audit-page/0.1.0', init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class LoadAuditUnavailable(_Carrier):
    reason: Literal['unauthorized', 'not_found', 'incomplete_scope', 'resource',
                    'unsupported_profile', 'observation']
    interface_version: Literal['truss-load-audit-unavailable/0.1.0'] = field(
        default='truss-load-audit-unavailable/0.1.0', init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class LoadAuditListingEnd(_Carrier):
    """The frozen listing frontier has no further visible chunks."""
    interface_version: Literal['truss-load-audit-listing-end/0.1.0'] = field(
        default='truss-load-audit-listing-end/0.1.0', init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class ModuleAuditGrant(_Carrier):
    document_id: str
    module_id: str
    auditor_role: str


@dataclass(frozen=True, slots=True, kw_only=True)
class AuditAccessUpdated(_Carrier):
    document_id: str
    module_id: str
    auditor_role: str
    outcome: Literal['updated'] = field(default='updated', init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class MutationGroupAuditEntry(_Carrier):
    operation_index: str
    entity_kind: Literal['object', 'edge']
    entity_id: str
    entity_type: str
    operation: Literal['create', 'metadata', 'delete', 'property', 'rebind',
                       'create_object', 'update_object', 'delete_object',
                       'create_edge', 'update_edge', 'delete_edge']
    observed_at: str


@dataclass(frozen=True, slots=True, kw_only=True)
class MutationGroupAuditListingCursor(_Carrier):
    """Opaque continuation for snapshot-bounded mutation group discovery."""
    installation_id: str
    source_epoch: str
    release_id: str
    release_sha256: str
    frontier_xid: str
    filters_sha256: str
    after_observed_at: str
    after_attempt_id: str
    profile: Literal['truss-mutation-group-audit-cursor/0.2'] = field(
        default='truss-mutation-group-audit-cursor/0.2', init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class MutationGroupAuditPage(_Carrier):
    attempt_id: str
    native_actor: str
    native_actor_name: str | None = None
    asserted_action: str | None
    writer_xid: str
    operation_count: str
    event_count: str
    entries: tuple[MutationGroupAuditEntry, ...]
    next_page_cursor: MutationGroupAuditListingCursor | None = None
    observed_at: str | None = None
    owner_scopes: tuple[dict, ...] = ()
    interface_version: Literal['truss-mutation-group-audit-page/0.1.0'] = field(
        default='truss-mutation-group-audit-page/0.1.0', init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class MutationGroupAuditListingEnd(_Carrier):
    """The frozen mutation audit frontier has no further visible groups."""
    interface_version: Literal['truss-mutation-group-audit-listing-end/0.1.0'] = field(
        default='truss-mutation-group-audit-listing-end/0.1.0', init=False)

