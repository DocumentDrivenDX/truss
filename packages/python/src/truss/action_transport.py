# SPDX-License-Identifier: MIT OR Apache-2.0
"""Synchronous, engine-owned transport for generated UMF actions.

This is a composition boundary, not an action interpreter. A host registers an
original accepted-source observer, typed decoder and native group executor for
each qualified action. This initial transport refuses read operations and
unqualified non-atomic batches.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
import inspect
import json
from time import monotonic
from collections.abc import Mapping
from types import MappingProxyType
from typing import Any, Callable


class ActionWireError(StrEnum):
    INVALID = "INVALID"
    DENIED = "DENIED"
    CONFLICT = "CONFLICT"
    PRECONDITION_FAILED = "PRECONDITION_FAILED"
    TOO_MANY_ROWS = "TOO_MANY_ROWS"
    LIMIT_EXCEEDED = "LIMIT_EXCEEDED"
    BUSY = "BUSY"
    UNSUPPORTED = "UNSUPPORTED"
    SCHEMA_MISMATCH = "SCHEMA_MISMATCH"
    WRITE_OUTCOME_UNKNOWN = "WRITE_OUTCOME_UNKNOWN"
    NOT_YET_CURRENT = "NOT_YET_CURRENT"
    INVALID_CURSOR = "INVALID_CURSOR"


class ActionRefusal(Exception):
    """Explicit refusal carrying only a registered UMF wire error code."""

    def __init__(self, code: ActionWireError, message: str = "Action refused", *,
                 field: str | None = None, precondition: str | None = None) -> None:
        if (type(code) is not ActionWireError or type(message) is not str
                or any(value is not None and (type(value) is not str or not value
                    or "\0" in value or len(value.encode("utf-8")) > 1024)
                    for value in (field, precondition))):
            raise TypeError("Registered wire code and fixed refusal message required")
        super().__init__(message)
        self.code = code
        self.field = field
        self.precondition = precondition


class _RequestLimitExceeded(ValueError):
    pass


_MAX_JSON_BYTES = 1_048_576
_MAX_JSON_NODES = 100_000
_MAX_JSON_DEPTH = 64


def _deferred(port: Callable[..., Any]) -> bool:
    call = getattr(port, "__call__", None)
    return any(inspect.iscoroutinefunction(item) or inspect.isgeneratorfunction(item)
               or inspect.isasyncgenfunction(item) for item in (port, call))


def _json_tree(value: Any) -> bool:
    try:
        _validate_json_tree(value)
        return True
    except (TypeError, ValueError, UnicodeError):
        return False


def _validate_json_tree(value: Any) -> None:
    pending = [(value, 0)]
    nodes = 0
    size = 0
    while pending:
        item, depth = pending.pop()
        nodes += 1
        if nodes > _MAX_JSON_NODES or depth > _MAX_JSON_DEPTH:
            raise _RequestLimitExceeded("JSON structure exceeds transport bounds")
        if item is None or type(item) is bool:
            size += 5
        elif type(item) is int:
            if not -(2**63) <= item < 2**63:
                raise ValueError("Integer outside signed 64-bit transport range")
            size += 20
        elif type(item) is str:
            size += len(item.encode("utf-8")) + 2
        elif type(item) is list:
            size += 2
            pending.extend((child, depth + 1) for child in item)
        elif type(item) is dict:
            size += 2
            for key, child in item.items():
                if type(key) is not str:
                    raise TypeError("JSON object keys must be strings")
                size += len(key.encode("utf-8")) + 3
                pending.append((child, depth + 1))
        else:
            raise TypeError("JSON-only transport value required")
        if size > _MAX_JSON_BYTES:
            raise _RequestLimitExceeded("JSON value exceeds transport byte bound")


def _canonical(value: Any) -> bytes:
    _validate_json_tree(value)
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")
    if len(raw) > _MAX_JSON_BYTES:
        raise _RequestLimitExceeded("Canonical JSON exceeds transport byte bound")
    return raw


def _clone_json(value: Any) -> Any:
    """Detach and normalize one complete JSON request before native callbacks."""
    return json.loads(_canonical(value).decode("utf-8"))


def _same_json(left: Any, right: Any) -> bool:
    try:
        return _canonical(left) == _canonical(right)
    except (TypeError, ValueError, UnicodeError):
        return False


@dataclass(frozen=True, slots=True)
class SchemaBinding:
    """Source digest plus a fresh native accepted-document observer per call.

    ``observe`` must use the public Truss accepted-document operation and raise
    ``ActionRefusal`` unless that native result corresponds byte-for-byte to
    the generated package's original source.
    """

    schema: str
    observe: Callable[[Any, Any], None]
    actions: Mapping[str, "ActionBinding"]

    def __post_init__(self) -> None:
        if (type(self.schema) is not str or len(self.schema) != 64
                or any(char not in "0123456789abcdef" for char in self.schema)
                or not callable(self.observe) or _deferred(self.observe)
                or not isinstance(self.actions, Mapping)
                or any(type(key) is not str or type(value) is not ActionBinding or key != value.action_id
                       for key, value in self.actions.items())):
            raise ValueError("Original source digest and synchronous native observer required")
        object.__setattr__(self, "actions", MappingProxyType(dict(self.actions)))


@dataclass(frozen=True, slots=True)
class StagedAction:
    """One exact UMF receipt body paired with its actual native group success."""

    body: Mapping[str, Any]
    native_group_success: Any
    native_key_maps: Mapping[str, Any]
    request_digest: str
    request_key: str | None
    asserted_origin: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class StagedBatch:
    """Atomic whole-batch receipt paired with its actual native group result."""

    body: Mapping[str, Any]
    native_group_success: Any
    native_key_maps: tuple[Mapping[str, Any], ...]
    request_digest: str
    request_key: str | None
    asserted_origin: Mapping[str, Any]
    flags: Mapping[str, bool]


@dataclass(frozen=True, slots=True)
class ActionBinding:
    action_id: str
    decode: Callable[[Mapping[str, Any]], Any]
    execute: Callable[[Any, Any, Any, str | None, Mapping[str, Any]], StagedAction]
    validate: Callable[[Any, Any, Any, Mapping[str, Any]], bool] | None = None
    validate_receipt: Callable[[Mapping[str, Any], Any], bool] | None = None
    execute_batch: Callable[[Any, Any, tuple[Any, ...], Mapping[str, Any]], StagedBatch] | None = None
    validate_batch_receipt: Callable[[Mapping[str, Any], Any], bool] | None = None

    def __post_init__(self) -> None:
        ports = (self.decode, self.execute, self.validate, self.validate_receipt,
                 self.execute_batch, self.validate_batch_receipt)
        if (type(self.action_id) is not str or not self.action_id or "." not in self.action_id
                or "\0" in self.action_id or len(self.action_id.encode("utf-8")) > 1024
                or self.validate_receipt is None
                or (self.execute_batch is not None and self.validate_batch_receipt is None)
                or any(port is not None and (not callable(port) or _deferred(port)) for port in ports)):
            raise ValueError("Qualified action identity and synchronous registered ports required")


@dataclass(frozen=True, slots=True)
class ActionApplied:
    action_id: str
    request_key: str | None
    body: Mapping[str, Any]
    schema: str


@dataclass(frozen=True, slots=True)
class ActionRefusalResult:
    code: ActionWireError
    schema: str
    request_key: str | None = None
    field: str | None = None
    precondition: str | None = None


@dataclass(frozen=True, slots=True)
class ActionOutcomeUnknown:
    request_key: str | None
    schema: str


@dataclass(frozen=True, slots=True)
class ActionValidated:
    schema: str


def _check_action_request(stage: StagedAction, request: Mapping[str, Any], key: str | None) -> None:
    if (type(stage.asserted_origin) is not dict or not _json_tree(stage.asserted_origin)
            or type(stage.request_digest) is not str):
        raise ValueError("Trusted original asserted origin and digest required")
    canonical = {"request": dict(request), "asserted_origin": stage.asserted_origin}
    if stage.request_key != key or stage.request_digest != sha256(_canonical(canonical)).hexdigest():
        raise ValueError("Native result does not bind the complete original action request")


def _validate_action_stage(stage: Any, validator: Callable | None) -> Mapping[str, Any]:
    from .groups import (AppliedPending, CommittedReceiptReplay, GroupSuccess,
                         SameTransactionReplay)

    if type(stage) is not StagedAction or type(stage.body) is not dict:
        raise ValueError("Complete staged action result required")
    body = _clone_json(stage.body)
    if set(body) != {"created", "changed", "counts", "consistency_token"} or not _json_tree(body):
        raise ValueError("Exact generated action receipt fields required")
    for name in ("created", "changed"):
        items = body[name]
        if type(items) is not list or any(type(item) is not dict or set(item) != {"record", "key"}
                or type(item["record"]) is not str or not item["record"]
                or type(item["key"]) is not dict or not item["key"] or not _json_tree(item["key"])
                for item in items):
            raise ValueError("Exact generated record/key maps required")
    counts = body["counts"]
    if (type(counts) is not dict or any(type(name) is not str or type(value) is not int or value < 0
            for name, value in counts.items())):
        raise ValueError("Complete nonnegative receipt counts required")
    token = body["consistency_token"]
    if type(token) is not str or not token:
        raise ValueError("Nonempty native consistency token required")
    expected_keys = {"created": body["created"], "changed": body["changed"]}
    if type(stage.native_key_maps) is not dict or not _same_json(stage.native_key_maps, expected_keys):
        raise ValueError("Exact native generated-key correspondence required")
    native = stage.native_group_success
    if type(native) is not GroupSuccess or type(native.response) not in (
            AppliedPending, SameTransactionReplay, CommittedReceiptReplay):
        raise ValueError("Original native GroupSuccess required")
    if validator is not None and validator(_clone_json(body), native) is not True:
        raise ValueError("Original action receipt validator refused")
    return body


def _validate_batch_stage(stage: Any, validator: Callable | None,
                          request_metadata: Mapping[str, Any]) -> Mapping[str, Any]:
    from .groups import (AppliedPending, CommittedReceiptReplay, GroupSuccess,
                         SameTransactionReplay)

    if type(stage) is not StagedBatch or type(stage.body) is not dict:
        raise ValueError("Complete staged atomic batch result required")
    flags = {"atomic": request_metadata.get("atomic"), "stop_on_error": request_metadata.get("stop_on_error")}
    if (type(stage.asserted_origin) is not dict or not _json_tree(stage.asserted_origin)
            or type(stage.flags) is not dict or not _same_json(stage.flags, flags)
            or stage.request_key != request_metadata.get("idempotency_key")):
        raise ValueError("Original native batch request correspondence required")
    canonical = {"request": dict(request_metadata), "asserted_origin": stage.asserted_origin}
    expected_digest = sha256(_canonical(canonical)).hexdigest()
    if stage.request_digest != expected_digest:
        raise ValueError("Native batch digest does not bind original ordered request and origin")
    body = _clone_json(stage.body)
    if set(body) != {"items", "consistency_token"} or not _json_tree(body):
        raise ValueError("Complete generated atomic batch receipt required")
    items = body["items"]
    if type(items) is not list or len(items) != len(request_metadata["items"]):
        raise ValueError("Complete original batch ordering required")
    applied_keys = []
    for item in items:
        if (type(item) is not dict or set(item) != {"status", "receipt"} or item["status"] != "applied"
                or type(item["receipt"]) is not dict
                or set(item["receipt"]) != {"created", "changed", "counts"}):
            raise ValueError("Atomic batches require one complete applied receipt per ordered input")
        receipt = item["receipt"]
        for field in ("created", "changed"):
            records = receipt[field]
            if (type(records) is not list or any(
                    type(record) is not dict or set(record) != {"record", "key"}
                    or type(record["record"]) is not str or not record["record"]
                    or type(record["key"]) is not dict or not record["key"]
                    or not _json_tree(record["key"]) for record in records)):
                raise ValueError("Complete atomic batch record/key maps required")
        counts = receipt["counts"]
        if (type(counts) is not dict or any(type(k) is not str or type(v) is not int or v < 0
                for k, v in counts.items())):
            raise ValueError("Complete atomic batch counts required")
        applied_keys.append({"created": receipt["created"], "changed": receipt["changed"]})
    if (type(body["consistency_token"]) is not str or not body["consistency_token"]
            or type(stage.native_key_maps) is not tuple or len(stage.native_key_maps) != len(items)
            or not _same_json(list(stage.native_key_maps), applied_keys)):
        raise ValueError("Exact atomic native key maps and consistency token required")
    native = stage.native_group_success
    if type(native) is not GroupSuccess or type(native.response) not in (
            AppliedPending, SameTransactionReplay, CommittedReceiptReplay):
        raise ValueError("Atomic batch must return one original native GroupSuccess")
    if validator is not None and validator(_clone_json(body), native) is not True:
        raise ValueError("Original atomic batch receipt validator refused")
    return body


def _wire_refusal(result: ActionRefusalResult) -> Mapping[str, Any]:
    error: dict[str, str] = {"code": result.code.value}
    if result.field is not None:
        error["field"] = result.field
    if result.precondition is not None:
        error["precondition"] = result.precondition
    return {"schema": result.schema, "error": error}


class TrussActionTransport:
    """Synchronous UMF ``SyncTransport`` over owned Truss group transactions.

    The host owns credentials and pool policy. The connection factory returns
    an exclusive context-managed lease over an idle, autocommit stock psycopg
    connection; lease exit only releases the resource and does not settle a
    transaction. This transport owns one READ COMMITTED transaction and never
    retries a dispatched operation.
    """

    def __init__(self, *, connection_factory: Callable[[], Any], assembly_factory: Callable[[Any], Any],
                 schemas: Mapping[str, SchemaBinding],
                 statement_timeout_ms: int = 2000, operation_timeout_ms: int = 5000) -> None:
        if (not callable(connection_factory) or _deferred(connection_factory)
                or not callable(assembly_factory) or _deferred(assembly_factory)
                or type(schemas) is not dict
                or type(statement_timeout_ms) is not int or not 1 <= statement_timeout_ms <= 10000
                or type(operation_timeout_ms) is not int or not 1 <= operation_timeout_ms <= 30000):
            raise ValueError("Synchronous registered ports and bounded local profile required")
        if any(type(key) is not str or type(value) is not SchemaBinding or key != value.schema
               for key, value in schemas.items()):
            raise ValueError("Exact source binding inventory required")
        self._connection_factory = connection_factory
        self._assembly_factory = assembly_factory
        self._schemas = dict(schemas)
        self._statement_timeout_ms = statement_timeout_ms
        self._operation_timeout_ms = operation_timeout_ms

    def execute(self, request: Mapping[str, Any]) -> Mapping[str, Any]:
        """Execute one generated UMF ``umf.access/1`` request."""
        if not isinstance(request, Mapping):
            return {"schema": "", "error": {"code": ActionWireError.INVALID.value}}
        deadline = monotonic() + self._operation_timeout_ms / 1000
        try:
            supplied_digest = request.get("schema")
            registered_digest = (supplied_digest if type(supplied_digest) is str
                                 and supplied_digest in self._schemas else "")
        except Exception:
            registered_digest = ""
        if any(type(key) is not str for key in request):
            code = ActionWireError.BUSY if monotonic() >= deadline else ActionWireError.INVALID
            return {"schema": registered_digest, "error": {"code": code.value}}
        try:
            request = json.loads(_canonical(dict(request)).decode("utf-8"))
        except _RequestLimitExceeded:
            code = ActionWireError.BUSY if monotonic() >= deadline else ActionWireError.LIMIT_EXCEEDED
            return {"schema": registered_digest,
                    "error": {"code": code.value}}
        except (TypeError, ValueError, UnicodeError):
            code = ActionWireError.BUSY if monotonic() >= deadline else ActionWireError.INVALID
            return {"schema": registered_digest,
                    "error": {"code": code.value}}
        if monotonic() >= deadline:
            return {"schema": registered_digest,
                    "error": {"code": ActionWireError.BUSY.value}}
        digest = request.get("schema")
        schema = self._schemas.get(digest) if type(digest) is str else None
        if schema is None:
            return {"schema": digest if type(digest) is str else "",
                    "error": {"code": ActionWireError.SCHEMA_MISMATCH.value}}
        if request.get("contract") != "umf.access/1":
            return {"schema": digest, "error": {"code": ActionWireError.UNSUPPORTED.value}}
        if request.get("kind") == "read":
            return {"schema": digest, "error": {"code": ActionWireError.UNSUPPORTED.value}}
        action_id = request.get("action")
        binding = schema.actions.get(action_id) if type(action_id) is str else None
        if binding is None:
            return {"schema": digest, "error": {"code": ActionWireError.UNSUPPORTED.value}}
        kind = request.get("kind")
        if kind == "validate":
            return self._validate(schema, binding, request, deadline)
        if kind == "apply":
            return self._apply(schema, binding, request, deadline)
        if kind == "apply_batch":
            return self._apply_batch(schema, binding, request, deadline)
        return {"schema": digest, "error": {"code": ActionWireError.UNSUPPORTED.value}}

    def _inputs(self, schema: SchemaBinding, binding: ActionBinding,
                raw: Any) -> tuple[Any, Mapping[str, Any]] | Mapping[str, Any]:
        if not isinstance(raw, Mapping) or any(type(key) is not str for key in raw):
            return {"schema": schema.schema, "error": {"code": ActionWireError.INVALID.value}}
        try:
            original = _clone_json(dict(raw))
            inputs = _clone_json(original)
            decoded = binding.decode(inputs)
            if inspect.isawaitable(decoded) or inspect.isgenerator(decoded) or inspect.isasyncgen(decoded):
                if hasattr(decoded, "close"): decoded.close()
                raise ActionRefusal(ActionWireError.INVALID)
            return decoded, original
        except ActionRefusal as refusal:
            return _wire_refusal(ActionRefusalResult(
                refusal.code, schema.schema, None, refusal.field, refusal.precondition))
        except Exception:
            return {"schema": schema.schema, "error": {"code": ActionWireError.INVALID.value}}

    def _apply(self, schema: SchemaBinding, binding: ActionBinding,
               request: Mapping[str, Any], deadline: float) -> Mapping[str, Any]:
        if set(request) != {"contract", "schema", "kind", "action", "inputs", "idempotency_key"}:
            return {"schema": schema.schema, "error": {"code": ActionWireError.INVALID.value}}
        key = request["idempotency_key"]
        if key is not None and (type(key) is not str or not key or "\0" in key):
            return {"schema": schema.schema, "error": {"code": ActionWireError.INVALID.value}}
        prepared = self._inputs(schema, binding, request["inputs"])
        if monotonic() >= deadline:
            return {"schema": schema.schema, "error": {"code": ActionWireError.BUSY.value}}
        if isinstance(prepared, Mapping):
            return prepared
        decoded, _inputs = prepared
        result = self._run(schema, binding, decoded, key, deadline=deadline,
                           original_request=_clone_json(dict(request)))
        if type(result) is ActionApplied:
            return {"schema": schema.schema, "status": "committed", **result.body}
        if type(result) is ActionRefusalResult:
            return _wire_refusal(result)
        return {"schema": schema.schema, "error": {"code": ActionWireError.WRITE_OUTCOME_UNKNOWN.value}}

    def _validate(self, schema: SchemaBinding, binding: ActionBinding,
                  request: Mapping[str, Any], deadline: float) -> Mapping[str, Any]:
        if set(request) != {"contract", "schema", "kind", "action", "inputs"}:
            return {"schema": schema.schema, "error": {"code": ActionWireError.INVALID.value}}
        if binding.validate is None:
            return {"schema": schema.schema, "error": {"code": ActionWireError.UNSUPPORTED.value}}
        prepared = self._inputs(schema, binding, request["inputs"])
        if monotonic() >= deadline:
            return {"schema": schema.schema, "error": {"code": ActionWireError.BUSY.value}}
        if isinstance(prepared, Mapping):
            return prepared
        decoded, _inputs = prepared
        result = self._run(schema, binding, decoded, None, deadline=deadline,
                           original_request=_clone_json(dict(request)), advisory=True)
        if type(result) is ActionValidated:
            return {"schema": schema.schema, "valid": True}
        if type(result) is ActionRefusalResult:
            return _wire_refusal(result)
        return {"schema": schema.schema, "error": {"code": ActionWireError.BUSY.value}}

    def _apply_batch(self, schema: SchemaBinding, binding: ActionBinding,
                     request: Mapping[str, Any], deadline: float) -> Mapping[str, Any]:
        if binding.execute_batch is None or binding.validate_batch_receipt is None:
            return {"schema": schema.schema, "error": {"code": ActionWireError.UNSUPPORTED.value}}
        fields = {"contract", "schema", "kind", "action", "items", "atomic", "stop_on_error", "idempotency_key"}
        if set(request) != fields:
            return {"schema": schema.schema, "error": {"code": ActionWireError.INVALID.value}}
        raw_items, atomic, stop, key = (request["items"], request["atomic"],
                                        request["stop_on_error"], request["idempotency_key"])
        if (type(raw_items) is not list or not 1 <= len(raw_items) <= 100 or type(atomic) is not bool
                or type(stop) is not bool or (key is not None and (type(key) is not str or not key or "\0" in key))):
            return {"schema": schema.schema, "error": {"code": ActionWireError.INVALID.value}}
        if not atomic:
            return {"schema": schema.schema, "error": {"code": ActionWireError.UNSUPPORTED.value}}
        decoded_items = []
        original_items = []
        for raw in raw_items:
            prepared = self._inputs(schema, binding, raw)
            if monotonic() >= deadline:
                return {"schema": schema.schema, "error": {"code": ActionWireError.BUSY.value}}
            if isinstance(prepared, Mapping):
                return prepared
            decoded, original = prepared
            decoded_items.append(decoded)
            original_items.append(original)
        request_key = key
        flags = {"atomic": atomic, "stop_on_error": stop}
        original_request = _clone_json(dict(request))
        context = {"request": _clone_json(original_request), "request_key": request_key,
                   "flags": flags, "original_items": tuple(original_items)}
        result = self._run(schema, binding, tuple(decoded_items), request_key, deadline=deadline,
                           original_request=original_request, batch_context=context)
        if type(result) is ActionApplied:
            return {"schema": schema.schema, "status": "committed", **result.body}
        if type(result) is ActionRefusalResult:
            return _wire_refusal(result)
        return {"schema": schema.schema, "error": {"code": ActionWireError.WRITE_OUTCOME_UNKNOWN.value}}

    def _run(self, schema: SchemaBinding, binding: ActionBinding, decoded: Any,
             request_key: str | None, *, deadline: float, original_request: Mapping[str, Any],
             batch_context: Mapping[str, Any] | None = None, advisory: bool = False) -> Any:
        from psycopg import pq
        from .psycopg_host import adopt_psycopg_host
        connection = host = assembly = lease = None
        lease_entered = False
        transaction = None
        dispatched = False
        owned_transaction = False
        begin_submitted = False
        commit_started = False
        commit_confirmed = False
        rollback_confirmed = False
        validation_confirmed = False
        explicit_refusal: ActionRefusal | None = None
        primary: BaseException | None = None
        cleanup_failed = False
        quarantine_required = False
        discard_attempted = False
        cleanup_base_exception: BaseException | None = None
        staged: StagedAction | StagedBatch | None = None
        backend_pid = None
        try:
            if monotonic() >= deadline:
                raise ActionRefusal(ActionWireError.BUSY)
            lease = self._connection_factory()
            if not (callable(getattr(lease, "__enter__", None)) and callable(getattr(lease, "__exit__", None))):
                raise ActionRefusal(ActionWireError.UNSUPPORTED)
            if not callable(getattr(lease, "discard", None)):
                raise ActionRefusal(ActionWireError.UNSUPPORTED)
            connection = lease.__enter__()
            lease_entered = True
            import psycopg
            if (type(connection) is not psycopg.Connection or connection.closed or connection.broken
                    or not connection.autocommit or connection.info.transaction_status != pq.TransactionStatus.IDLE
                    or connection.pgconn.pipeline_status != pq.PipelineStatus.OFF):
                raise ActionRefusal(ActionWireError.UNSUPPORTED)
            backend_pid = connection.info.backend_pid
            if monotonic() >= deadline:
                raise ActionRefusal(ActionWireError.BUSY)
            begin_submitted = True
            cursor = connection.execute("BEGIN ISOLATION LEVEL READ COMMITTED READ WRITE", prepare=False)
            owned_transaction = connection.info.transaction_status == pq.TransactionStatus.INTRANS
            if cursor.statusmessage != "BEGIN" or connection.info.transaction_status != pq.TransactionStatus.INTRANS:
                raise RuntimeError("Owned BEGIN completion unconfirmed")
            host = adopt_psycopg_host(connection, statement_timeout_ms=self._statement_timeout_ms,
                                      operation_timeout_ms=self._operation_timeout_ms)
            adopted = host.adopt_transaction(isolation="read_committed", access_mode="read_write")
            from .execution import Error
            if isinstance(adopted, Error):
                raise RuntimeError("Original owned transaction adoption failed")
            transaction = adopted.value
            assembly = self._assembly_factory(host)
            observation = schema.observe(assembly, transaction)
            if inspect.isawaitable(observation) or inspect.isgenerator(observation) or inspect.isasyncgen(observation):
                if hasattr(observation, "close"):
                    observation.close()
                raise ActionRefusal(ActionWireError.SCHEMA_MISMATCH)
            if observation is not None:
                raise ActionRefusal(ActionWireError.SCHEMA_MISMATCH)
            if monotonic() >= deadline:
                raise ActionRefusal(ActionWireError.BUSY)
            if advisory:
                dispatched = True
                valid = binding.validate(assembly, transaction, decoded, original_request)
                if valid is not True:
                    raise ActionRefusal(ActionWireError.INVALID)
                if not host.detach():
                    host = None
                    quarantine_required = True
                    raise RuntimeError("Original validation host detach unconfirmed")
                host = None
                if monotonic() >= deadline:
                    raise ActionRefusal(ActionWireError.BUSY)
                cursor = connection.execute("ROLLBACK", prepare=False)
                rollback_confirmed = (cursor.statusmessage == "ROLLBACK"
                                      and connection.info.transaction_status == pq.TransactionStatus.IDLE
                                      and connection.info.backend_pid == backend_pid)
                if not rollback_confirmed:
                    raise RuntimeError("Advisory rollback acknowledgement unconfirmed")
                validation_confirmed = True
            else:
                dispatched = True
                if batch_context is None:
                    staged = binding.execute(assembly, transaction, decoded, request_key,
                                             _clone_json(original_request))
                    _check_action_request(staged, original_request, request_key)
                    body = _validate_action_stage(staged, binding.validate_receipt)
                else:
                    callback_context = dict(batch_context)
                    callback_context["request"] = _clone_json(batch_context["request"])
                    callback_context["flags"] = dict(batch_context["flags"])
                    staged = binding.execute_batch(assembly, transaction, decoded, callback_context)
                    if type(staged) is not StagedBatch:
                        raise ValueError("Original whole-batch native callback required")
                    expected_meta = original_request
                    # The callback observes authenticated asserted origin while
                    # building the exact canonical native group request.
                    body = _validate_batch_stage(staged, binding.validate_batch_receipt, expected_meta)
                if not host.detach():
                    host = None
                    quarantine_required = True
                    raise RuntimeError("Original host detach unconfirmed")
                host = None
                if monotonic() >= deadline:
                    raise ActionRefusal(ActionWireError.BUSY)
                commit_started = True
                cursor = connection.execute("COMMIT", prepare=False)
                commit_confirmed = (cursor.statusmessage == "COMMIT"
                                    and connection.info.transaction_status == pq.TransactionStatus.IDLE
                                    and connection.info.backend_pid == backend_pid)
                if not commit_confirmed:
                    raise RuntimeError("Original commit acknowledgement/profile mismatch")
        except ActionRefusal as error:
            explicit_refusal = error
            primary = error
        except BaseException as error:
            primary = error
        finally:
            if host is not None:
                try:
                    if not host.detach():
                        cleanup_failed = True
                        quarantine_required = True
                except BaseException as error:
                    cleanup_failed = True
                    quarantine_required = True
                    if not isinstance(error, Exception) and cleanup_base_exception is None:
                        cleanup_base_exception = error
            # Never compete with an attempted COMMIT whose outcome is unknown.
            if (connection is not None and begin_submitted and not commit_started
                    and not commit_confirmed):
                try:
                    if not connection.closed and not connection.broken:
                        status = connection.info.transaction_status
                        if status in (pq.TransactionStatus.INTRANS, pq.TransactionStatus.INERROR):
                            if connection.info.backend_pid == backend_pid:
                                owned_transaction = True
                                cursor = connection.execute("ROLLBACK", prepare=False)
                                rollback_confirmed = (cursor.statusmessage == "ROLLBACK"
                                                      and connection.info.transaction_status == pq.TransactionStatus.IDLE
                                                      and connection.info.backend_pid == backend_pid)
                            else:
                                cleanup_failed = True
                        elif status == pq.TransactionStatus.IDLE:
                            rollback_confirmed = rollback_confirmed or not dispatched
                        if not rollback_confirmed:
                            quarantine_required = True
                except BaseException as error:
                    cleanup_failed = True
                    quarantine_required = True
                    if not isinstance(error, Exception) and cleanup_base_exception is None:
                        cleanup_base_exception = error
                if not rollback_confirmed:
                    quarantine_required = True
            # A host lease owns release/discard policy. It must not settle a
            # transaction; Truss has explicitly settled owned transactions.
            # If COMMIT was submitted without a confirmed acknowledgement,
            # tell a lease that supports discard to quarantine that connection.
            if (commit_started and not commit_confirmed) or cleanup_failed:
                quarantine_required = True
            if quarantine_required and lease is not None:
                try:
                    discard = getattr(lease, "discard", None)
                    if callable(discard):
                        discard()
                        discard_attempted = True
                    else:
                        cleanup_failed = True
                except BaseException as error:
                    cleanup_failed = True
                    if not isinstance(error, Exception) and cleanup_base_exception is None:
                        cleanup_base_exception = error
            if lease_entered:
                try:
                    lease.__exit__(None, None, None)
                except BaseException as error:
                    cleanup_failed = True
                    try:
                        discard = getattr(lease, "discard", None)
                        if callable(discard) and not discard_attempted:
                            discard()
                            discard_attempted = True
                    except BaseException as discard_error:
                        if not isinstance(discard_error, Exception) and cleanup_base_exception is None:
                            cleanup_base_exception = discard_error
                    if not isinstance(error, Exception) and cleanup_base_exception is None:
                        cleanup_base_exception = error
        # Cancellation and other BaseException values retain their original
        # identity after transaction cleanup; the generated client records its key.
        if primary is not None and not isinstance(primary, Exception):
            if cleanup_base_exception is not None:
                raise primary from cleanup_base_exception
            raise primary
        if cleanup_base_exception is not None:
            if primary is not None:
                raise cleanup_base_exception from primary
            raise cleanup_base_exception
        if advisory and validation_confirmed and rollback_confirmed and not cleanup_failed and primary is None:
            if monotonic() >= deadline:
                return ActionRefusalResult(ActionWireError.BUSY, schema.schema, request_key)
            return ActionValidated(schema.schema)
        if commit_confirmed and not cleanup_failed and primary is None and monotonic() < deadline:
            return ActionApplied(binding.action_id, request_key, body, schema.schema)
        if explicit_refusal is not None and rollback_confirmed and not cleanup_failed:
            return ActionRefusalResult(explicit_refusal.code, schema.schema, request_key,
                                       explicit_refusal.field, explicit_refusal.precondition)
        if (explicit_refusal is not None and not dispatched and not owned_transaction
                and not cleanup_failed):
            return ActionRefusalResult(explicit_refusal.code, schema.schema, request_key,
                                       explicit_refusal.field, explicit_refusal.precondition)
        if not dispatched and not cleanup_failed and not quarantine_required:
            return ActionRefusalResult(ActionWireError.BUSY, schema.schema, request_key)
        return ActionOutcomeUnknown(request_key, schema.schema)
