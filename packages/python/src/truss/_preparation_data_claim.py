# SPDX-License-Identifier: MIT OR Apache-2.0
"""Engine data capture and excluded control issuance; no native authority.

Consumes UMF a8f73415's private claim ABI only when independently installed and
admitted by its owner. Its spike storage is not installed or vendored here.
"""
from dataclasses import dataclass, field
import uuid
from ._engine_preparation import _EnginePreparationSession
from ._security_catalog_subject_installation import _text_rows
from .catalog_runtime import _pin_cursor
from .execution import Error, ExecutionFailure
from .psycopg_host import PsycopgHost


@dataclass(frozen=True, slots=True)
class PreparationClaimData:
    data_pid: int
    data_xid: str
    _session: object = field(repr=False, compare=False)
    _transaction: object = field(repr=False, compare=False)
    authority: bool = False


@dataclass(frozen=True, slots=True)
class PendingPreparationDataClaim:
    claim_id: str
    anchor_id: int
    anchor_nonce: str
    data_pid: int
    data_xid: str
    status: str = 'pending_commit'
    authority: bool = False


def _current_data(cursor, observed):
    _pin_cursor(cursor)
    rows = _text_rows(cursor, """SELECT pg_catalog.current_setting('server_version_num'),
        pg_catalog.current_setting('transaction_isolation'),
        pg_catalog.current_setting('transaction_read_only'),pg_catalog.current_setting('role'),
        session_user::pg_catalog.text,current_user::pg_catalog.text,
        pg_catalog.pg_backend_pid()::pg_catalog.text,
        pg_catalog.pg_current_xact_id()::pg_catalog.text""", limit=1)
    if (len(rows) != 1 or rows[0][:4] != ('180006', 'repeatable read', 'off', 'none')
            or rows[0][4] != rows[0][5]):
        raise ValueError('Original writable native RR data transaction required')
    return int(rows[0][6]), rows[0][7]


def capture_preparation_claim_data(session):
    """Retain actual original engine session/handle association, not a PID claim."""
    if type(session) is not _EnginePreparationSession:
        return Error(ExecutionFailure('execution_obligation', 'Original engine preparation session required'))
    def capture(cursor, observed):
        pid, xid = _current_data(cursor, observed)
        if pid != session._backend_pid:
            raise ValueError('Original engine data backend required')
        return PreparationClaimData(pid, xid, session, session._transaction)
    return session.run_operation(capture)


def issue_preparation_data_claim_in_transaction(host, transaction, *, anchor_id,
                                               anchor_nonce, data):
    """Excluded E only; caller owns independent commit, with no automatic retry.

    The original coordinator must consume committed native identity inside its
    eventual guard. A returned UUID is pending and never permission. Native E
    independently verifies the original peers, anchor, program and store.
    """
    try:
        if (type(host) is not PsycopgHost or type(data) is not PreparationClaimData
                or type(anchor_id) is not int or not 0 < anchor_id < 2**31
                or type(anchor_nonce) is not str or str(uuid.UUID(anchor_nonce)) != anchor_nonce
                or type(data._session) is not _EnginePreparationSession
                or data._transaction is not data._session._transaction or data.authority is not False):
            raise ValueError('Original retained engine data and anchor required')
    except (ValueError, TypeError, AttributeError):
        return Error(ExecutionFailure('execution_obligation', 'Original retained data claim input required'))

    # Observe through the same original handle again; no replacement connection
    # or caller-supplied tuple is promoted to captured engine custody.
    current = data._session.run_operation(_current_data)
    if isinstance(current, Error): return current
    if current.value != (data.data_pid, data.data_xid):
        return Error(ExecutionFailure('invalid_transaction', 'Original data transaction changed'))

    def issue(cursor, observed):
        _pin_cursor(cursor)
        rows = _text_rows(cursor, """SELECT umf_security.claim_preparation_data(
            %s::pg_catalog.int4,%s::pg_catalog.uuid,%s::pg_catalog.xid8)::pg_catalog.text""",
            (anchor_id, anchor_nonce, data.data_xid), 1)
        if len(rows) != 1 or str(uuid.UUID(rows[0][0])) != rows[0][0]:
            raise ValueError('Original pending native claim identity required')
        return PendingPreparationDataClaim(rows[0][0], anchor_id, anchor_nonce,
                                           data.data_pid, data.data_xid)
    return host._run_operation(transaction, issue)
