# SPDX-License-Identifier: MIT OR Apache-2.0
"""Pure Python admission controls for the generated-action transport."""
import asyncio
import asyncio
import unittest
from contextlib import AbstractContextManager
from types import SimpleNamespace
from unittest.mock import patch

import psycopg
from psycopg import pq
from truss import ActionBinding, ActionRefusal, ActionWireError, SchemaBinding, TrussActionTransport
from truss.execution import Ok
from truss.action_transport import ActionRefusalResult, _wire_refusal


SOURCE = "a" * 64


class ActionTransportAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.leases = []
        binding = ActionBinding(
            "sample.Create",
            decode=lambda inputs: dict(inputs),
            execute=lambda *args: self.fail("unsupported request must not dispatch"),
            validate_receipt=lambda body, native: True,
        )
        self.transport = TrussActionTransport(
            connection_factory=lambda: self.leases.append("requested"),
            assembly_factory=lambda host: self.fail("unsupported request must not compose"),
            schemas={SOURCE: SchemaBinding(SOURCE, lambda assembly, tx: None,
                                           {binding.action_id: binding})},
        )

    def _run_component_lifecycle(self, *, observer=None, execute=None, receipt=None,
                                 commit_status="COMMIT", lease_exit=None, now=None):
        """Isolate transport lifecycle from native receipt qualification."""
        class Connection:
            def __init__(self):
                self.closed = self.broken = False
                self.autocommit = True
                self.info = SimpleNamespace(transaction_status=pq.TransactionStatus.IDLE,
                                            backend_pid=91)
                self.pgconn = SimpleNamespace(pipeline_status=pq.PipelineStatus.OFF)
                self.statements = []

            def execute(self, statement, **kwargs):
                self.statements.append(statement)
                if statement.startswith("BEGIN"):
                    self.info.transaction_status = pq.TransactionStatus.INTRANS
                    return SimpleNamespace(statusmessage="BEGIN")
                if statement == "ROLLBACK":
                    self.info.transaction_status = pq.TransactionStatus.IDLE
                    return SimpleNamespace(statusmessage="ROLLBACK")
                if statement == "COMMIT":
                    self.info.transaction_status = pq.TransactionStatus.IDLE
                    return SimpleNamespace(statusmessage=commit_status)
                raise AssertionError(statement)

        connection = Connection()
        state = {"discarded": 0, "released": 0, "executed": 0}

        class Lease:
            def __enter__(self): return connection
            def __exit__(self, *args):
                state["released"] += 1
                if lease_exit is not None: raise lease_exit
                return False
            def discard(self): state["discarded"] += 1

        class Host:
            def adopt_transaction(self, **kwargs): return Ok(object())
            def detach(self): return True

        def handler(*args):
            state["executed"] += 1
            if execute is not None: return execute(*args)
            return SimpleNamespace()

        binding = ActionBinding("sample.Create", lambda inputs: dict(inputs), handler,
                                validate_receipt=lambda body, native: True)
        schema = SchemaBinding(SOURCE, observer if observer is not None else (lambda assembly, tx: None),
                               {binding.action_id: binding})
        transport = TrussActionTransport(
            connection_factory=Lease, assembly_factory=lambda host: object(),
            schemas={SOURCE: schema})
        request = {"contract": "umf.access/1", "schema": SOURCE, "kind": "apply",
                   "action": binding.action_id, "inputs": {"x": 1},
                   "idempotency_key": "component-key"}
        from truss import action_transport as module
        staged = SimpleNamespace()
        with (patch.object(psycopg, "Connection", Connection),
              patch("truss.psycopg_host.adopt_psycopg_host", return_value=Host()),
              patch.object(module, "_check_action_request"),
              patch.object(module, "_validate_action_stage",
                           side_effect=receipt if isinstance(receipt, BaseException) else None,
                           return_value=(receipt if not isinstance(receipt, BaseException) else None) or {
                               "created": [], "changed": [], "counts": {},
                               "consistency_token": "component-token"})):
            if now is None:
                response = transport.execute(request)
            else:
                with patch("truss.action_transport.monotonic", side_effect=now):
                    response = transport.execute(request)
        return response, connection.statements, state

    def test_deferred_observer_is_closed_and_blocks_dispatch(self):
        closed = []
        def deferred():
            try: yield
            finally: closed.append(True)
        def observer(assembly, transaction):
            pending = deferred()
            next(pending)
            return pending
        response, statements, state = self._run_component_lifecycle(
            observer=observer)
        self.assertEqual(response["error"]["code"], ActionWireError.SCHEMA_MISMATCH.value)
        self.assertEqual(state["executed"], 0)
        self.assertEqual(statements[-1], "ROLLBACK")
        self.assertEqual(closed, [True])

    def test_postdispatch_cancellation_identity_survives_cleanup_cancellation(self):
        original = asyncio.CancelledError("handler cancellation")
        cleanup = KeyboardInterrupt("lease cleanup cancellation")
        calls = []
        def handler(*args):
            calls.append(True)
            raise original
        with self.assertRaises(asyncio.CancelledError) as raised:
            result = self._run_component_lifecycle(execute=handler, lease_exit=cleanup)
        self.assertIs(raised.exception, original)
        self.assertEqual(calls, [True])

    def test_decoder_mutation_does_not_change_original_input_snapshot(self):
        binding = ActionBinding("sample.Create", lambda inputs: inputs["nested"].update({"x": 2}) or inputs,
                                lambda *args: None,
                                validate_receipt=lambda body, native: True)
        schema = SchemaBinding(SOURCE, lambda assembly, tx: None,
                               {binding.action_id: binding})
        submitted = {"nested": {"x": 1}}
        prepared = self.transport._inputs(schema, binding, submitted)
        self.assertEqual(prepared[0]["nested"]["x"], 2)
        self.assertEqual(prepared[1], {"nested": {"x": 1}})
        self.assertEqual(submitted, {"nested": {"x": 1}})

    def test_malformed_staged_receipt_rolls_back_and_reports_unknown(self):
        response, statements, state = self._run_component_lifecycle(
            receipt=ValueError("malformed staged receipt"))
        self.assertEqual(response["error"]["code"], ActionWireError.WRITE_OUTCOME_UNKNOWN.value)
        self.assertEqual(state["executed"], 1)
        self.assertEqual(statements[-1], "ROLLBACK")

    def test_commit_tag_must_be_exact_and_postcommit_release_failure_is_unknown(self):
        response, statements, state = self._run_component_lifecycle(commit_status="ROLLBACK")
        self.assertEqual(response["error"]["code"], ActionWireError.WRITE_OUTCOME_UNKNOWN.value)
        self.assertEqual(statements[-1], "COMMIT")
        self.assertEqual(state["discarded"], 1)
        release_error = RuntimeError("release failed")
        response, statements, state = self._run_component_lifecycle(lease_exit=release_error)
        self.assertEqual(response["error"]["code"], ActionWireError.WRITE_OUTCOME_UNKNOWN.value)
        self.assertEqual(statements[-1], "COMMIT")
        self.assertEqual(state["discarded"], 1)

    def test_deadline_expiring_during_commit_cleanup_never_acknowledges(self):
        reads = iter((0.0, 0.0, 0.0, 0.0, 31.0))
        response, statements, state = self._run_component_lifecycle(now=lambda: next(reads))
        self.assertEqual(response["error"]["code"], ActionWireError.WRITE_OUTCOME_UNKNOWN.value)
        self.assertEqual(statements[-1], "COMMIT")
        self.assertEqual(state["released"], 1)

    def test_noop_receipt_accepts_empty_counts_and_detaches_validator_body(self):
        from truss.action_transport import StagedAction, _validate_action_stage
        from truss.groups import AppliedPending, GroupSuccess
        pending = object.__new__(AppliedPending)
        object.__setattr__(pending, "semantic", object())
        native = object.__new__(GroupSuccess)
        object.__setattr__(native, "response", pending)
        body = {"created": [], "changed": [], "counts": {},
                "consistency_token": "native-token"}
        stage = StagedAction(body, native, {"created": [], "changed": []}, "digest", "key", {})
        def mutate_validator(copy, success):
            copy["consistency_token"] = None
            return True
        validated = _validate_action_stage(stage, mutate_validator)
        self.assertEqual(validated["consistency_token"], "native-token")
        self.assertEqual(body["consistency_token"], "native-token")

    def test_malformed_batch_key_map_is_rejected_before_commit(self):
        from hashlib import sha256
        from truss.action_transport import StagedBatch, _canonical, _validate_batch_stage
        from truss.groups import AppliedPending, GroupSuccess
        pending = object.__new__(AppliedPending)
        object.__setattr__(pending, "semantic", object())
        native = object.__new__(GroupSuccess)
        object.__setattr__(native, "response", pending)
        request = {"items": [{"input": {}}], "atomic": True,
                   "stop_on_error": True, "idempotency_key": "batch-key"}
        origin = {}
        digest = sha256(_canonical({"request": request,
                                    "asserted_origin": origin})).hexdigest()
        receipt = {"created": [{"record": "Project", "key": {}}],
                   "changed": [], "counts": {}}
        body = {"items": [{"status": "applied", "receipt": receipt}],
                "consistency_token": "native-token"}
        stage = StagedBatch(body, native, ({"created": receipt["created"],
                                           "changed": []},), digest,
                            "batch-key", origin,
                            {"atomic": True, "stop_on_error": True})
        with self.assertRaises(ValueError):
            _validate_batch_stage(stage, lambda response, success: True, request)

    def test_action_inventory_is_scoped_to_schema(self):
        other = "b" * 64
        self.transport = TrussActionTransport(
            connection_factory=lambda: self.leases.append("requested"),
            assembly_factory=lambda host: None,
            schemas={SOURCE: SchemaBinding(SOURCE, lambda assembly, tx: None, {}),
                     other: SchemaBinding(other, lambda assembly, tx: None, {})},
        )
        result = self.transport.execute({
            "contract": "umf.access/1", "schema": SOURCE, "kind": "apply",
            "action": "sample.Create", "inputs": {}, "idempotency_key": None,
        })
        self.assertEqual(result["error"]["code"], ActionWireError.UNSUPPORTED.value)
        self.assertEqual(self.leases, [])

    def test_reads_and_unqualified_actions_are_rejected_before_lease(self):
        for request in (
            {"contract": "umf.access/1", "schema": SOURCE, "kind": "read", "query": "x"},
            {"contract": "umf.access/1", "schema": SOURCE, "kind": "apply",
             "action": "sample.Missing", "inputs": {}, "idempotency_key": "k"},
        ):
            result = self.transport.execute(request)
            self.assertEqual(result["error"]["code"], ActionWireError.UNSUPPORTED.value)
        self.assertEqual(self.leases, [])

    def test_invalid_complete_request_is_rejected_before_lease(self):
        request = {"contract": "umf.access/1", "schema": SOURCE, "kind": "apply",
                   "action": "sample.Create", "inputs": {"n": float("nan")},
                   "idempotency_key": "k"}
        self.assertEqual(self.transport.execute(request)["error"]["code"],
                         ActionWireError.INVALID.value)
        self.assertEqual(self.leases, [])

    def test_native_refusal_keeps_only_bounded_registered_identity_fields(self):
        refusal = ActionRefusal(ActionWireError.PRECONDITION_FAILED,
                                field="Project.code", precondition="fresh")
        wire = _wire_refusal(ActionRefusalResult(refusal.code, SOURCE, "key",
                                                 refusal.field, refusal.precondition))
        self.assertEqual(wire, {"schema": SOURCE, "error": {
            "code": "PRECONDITION_FAILED", "field": "Project.code", "precondition": "fresh"}})
        for value in ("", "\0bad", "x" * 1025):
            with self.assertRaises(TypeError):
                ActionRefusal(ActionWireError.INVALID, precondition=value)

    def test_decoder_refusal_preserves_registered_precondition_identity(self):
        refusal = ActionRefusal(ActionWireError.PRECONDITION_FAILED,
                                field="Project.code", precondition="fresh")
        binding = ActionBinding(
            "sample.Create",
            decode=lambda inputs: (_ for _ in ()).throw(refusal),
            execute=lambda *args: self.fail("decoder refusal must precede dispatch"),
            validate_receipt=lambda body, native: True)
        transport = TrussActionTransport(
            connection_factory=lambda: self.leases.append("requested"),
            assembly_factory=lambda host: self.fail("decoder refusal must precede lease"),
            schemas={SOURCE: SchemaBinding(SOURCE, lambda assembly, tx: None,
                                           {binding.action_id: binding})})
        result = transport.execute({
            "contract": "umf.access/1", "schema": SOURCE, "kind": "apply",
            "action": binding.action_id, "inputs": {}, "idempotency_key": "refused"})
        self.assertEqual(result, {"schema": SOURCE, "error": {
            "code": "PRECONDITION_FAILED", "field": "Project.code",
            "precondition": "fresh"}})
        self.assertEqual(self.leases, [])

    def test_oversized_request_is_limited_before_lease(self):
        request = {"contract": "umf.access/1", "schema": SOURCE, "kind": "apply",
                   "action": "sample.Create", "inputs": {"text": "x" * (1_048_577)},
                   "idempotency_key": "k"}
        self.assertEqual(self.transport.execute(request)["error"]["code"],
                         ActionWireError.LIMIT_EXCEEDED.value)
        self.assertEqual(self.leases, [])

    def test_escaped_canonical_request_bytes_are_limited_before_lease(self):
        request = {"contract": "umf.access/1", "schema": SOURCE, "kind": "apply",
                   "action": "sample.Create", "inputs": {"text": "\n" * 600_000},
                   "idempotency_key": "k"}
        self.assertEqual(self.transport.execute(request)["error"]["code"],
                         ActionWireError.LIMIT_EXCEEDED.value)
        self.assertEqual(self.leases, [])

    def test_foreign_active_connection_is_not_rolled_back_or_closed(self):
        class Connection:
            def __init__(self):
                self.closed = False
                self.broken = False
                self.autocommit = True
                self.calls = []
                self.info = SimpleNamespace(transaction_status=pq.TransactionStatus.INTRANS,
                                            backend_pid=27)
                self.pgconn = SimpleNamespace(pipeline_status=pq.PipelineStatus.OFF)

            def execute(self, *args, **kwargs):
                self.calls.append(args[0])
                raise AssertionError("transport must not issue SQL on a foreign transaction")

        connection = Connection()

        class Lease:
            def __enter__(self):
                return connection

            def __exit__(self, *args):
                return False

            def discard(self):
                raise AssertionError("foreign active lease is not transport-owned")

        binding = ActionBinding("sample.Create", lambda inputs: dict(inputs),
                                lambda *args: self.fail("must not dispatch"),
                                validate_receipt=lambda body, native: True)
        transport = TrussActionTransport(
            connection_factory=Lease,
            assembly_factory=lambda host: None,
            schemas={SOURCE: SchemaBinding(SOURCE, lambda assembly, tx: None,
                                           {binding.action_id: binding})})
        request = {"contract": "umf.access/1", "schema": SOURCE, "kind": "apply",
                   "action": "sample.Create", "inputs": {}, "idempotency_key": "foreign"}
        with patch.object(psycopg, "Connection", Connection):
            response = transport.execute(request)
        self.assertEqual(response["error"]["code"], ActionWireError.UNSUPPORTED.value)
        self.assertEqual(connection.calls, [])
        self.assertFalse(connection.closed)
        self.assertEqual(connection.info.transaction_status, pq.TransactionStatus.INTRANS)

    def test_original_cancellation_is_reraised_after_owned_rollback(self):
        class Connection:
            def __init__(self):
                self.closed = False
                self.broken = False
                self.autocommit = True
                self.statements = []
                self.info = SimpleNamespace(transaction_status=pq.TransactionStatus.IDLE,
                                            backend_pid=27)
                self.pgconn = SimpleNamespace(pipeline_status=pq.PipelineStatus.OFF)

            def execute(self, statement, **kwargs):
                self.statements.append(statement)
                if statement.startswith("BEGIN"):
                    self.info.transaction_status = pq.TransactionStatus.INTRANS
                    status = "BEGIN"
                elif statement == "ROLLBACK":
                    self.info.transaction_status = pq.TransactionStatus.IDLE
                    status = "ROLLBACK"
                else:
                    raise AssertionError(statement)
                return SimpleNamespace(statusmessage=status)

        connection = Connection()
        cancellation = KeyboardInterrupt("original cancellation")

        class Lease(AbstractContextManager):
            def __enter__(self):
                return connection

            def __exit__(self, *args):
                return False

            def discard(self):
                raise AssertionError("confirmed rollback lease should be reusable")

        class Host:
            def adopt_transaction(self, **kwargs):
                return Ok(object())

            def detach(self):
                return True

        binding = ActionBinding("sample.Create", lambda inputs: dict(inputs),
                                lambda *args: self.fail("cancellation precedes dispatch"),
                                validate_receipt=lambda body, native: True)
        transport = TrussActionTransport(
            connection_factory=Lease,
            assembly_factory=lambda host: object(),
            schemas={SOURCE: SchemaBinding(SOURCE,
                lambda assembly, tx: (_ for _ in ()).throw(cancellation),
                {binding.action_id: binding})})
        request = {"contract": "umf.access/1", "schema": SOURCE, "kind": "apply",
                   "action": "sample.Create", "inputs": {}, "idempotency_key": "cancel"}
        with (patch.object(psycopg, "Connection", Connection),
              patch("truss.psycopg_host.adopt_psycopg_host", return_value=Host())):
            with self.assertRaises(KeyboardInterrupt) as raised:
                transport.execute(request)
        self.assertIs(raised.exception, cancellation)
        self.assertEqual(connection.statements, ["BEGIN ISOLATION LEVEL READ COMMITTED READ WRITE", "ROLLBACK"])
        self.assertEqual(connection.info.transaction_status, pq.TransactionStatus.IDLE)

    def test_cleanup_cancellation_is_reraised_after_primary_refusal(self):
        class Connection:
            def __init__(self):
                self.closed = False
                self.broken = False
                self.autocommit = True
                self.info = SimpleNamespace(transaction_status=pq.TransactionStatus.IDLE,
                                            backend_pid=27)
                self.pgconn = SimpleNamespace(pipeline_status=pq.PipelineStatus.OFF)

            def execute(self, statement, **kwargs):
                if statement.startswith("BEGIN"):
                    self.info.transaction_status = pq.TransactionStatus.INTRANS
                    status = "BEGIN"
                elif statement == "ROLLBACK":
                    self.info.transaction_status = pq.TransactionStatus.IDLE
                    status = "ROLLBACK"
                else:
                    raise AssertionError(statement)
                return SimpleNamespace(statusmessage=status)

        connection = Connection()
        cleanup_cancel = KeyboardInterrupt("cleanup cancellation")
        discarded = []

        class Lease:
            def __enter__(self):
                return connection

            def __exit__(self, *args):
                raise cleanup_cancel

            def discard(self):
                discarded.append(True)

        class Host:
            def adopt_transaction(self, **kwargs):
                return Ok(object())

            def detach(self):
                return True

        binding = ActionBinding("sample.Create", lambda inputs: dict(inputs),
                                lambda *args: self.fail("observer refusal precedes dispatch"),
                                validate_receipt=lambda body, native: True)
        transport = TrussActionTransport(
            connection_factory=Lease, assembly_factory=lambda host: object(),
            schemas={SOURCE: SchemaBinding(SOURCE,
                lambda assembly, tx: (_ for _ in ()).throw(ActionRefusal(ActionWireError.INVALID)),
                {binding.action_id: binding})})
        request = {"contract": "umf.access/1", "schema": SOURCE, "kind": "apply",
                   "action": "sample.Create", "inputs": {}, "idempotency_key": "cleanup"}
        with (patch.object(psycopg, "Connection", Connection),
              patch("truss.psycopg_host.adopt_psycopg_host", return_value=Host())):
            with self.assertRaises(KeyboardInterrupt) as raised:
                transport.execute(request)
        self.assertIs(raised.exception, cleanup_cancel)
        self.assertEqual(connection.info.transaction_status, pq.TransactionStatus.IDLE)
        self.assertEqual(discarded, [True])

    def test_failed_predispatch_rollback_quarantines_and_reports_unknown(self):
        class Connection:
            def __init__(self):
                self.closed = False
                self.broken = False
                self.autocommit = True
                self.info = SimpleNamespace(transaction_status=pq.TransactionStatus.IDLE,
                                            backend_pid=27)
                self.pgconn = SimpleNamespace(pipeline_status=pq.PipelineStatus.OFF)

            def execute(self, statement, **kwargs):
                if statement.startswith("BEGIN"):
                    self.info.transaction_status = pq.TransactionStatus.INTRANS
                    return SimpleNamespace(statusmessage="BEGIN")
                if statement == "ROLLBACK":
                    raise RuntimeError("lost rollback acknowledgement")
                raise AssertionError(statement)

        connection = Connection()
        discarded = []

        class Lease:
            def __enter__(self):
                return connection

            def __exit__(self, *args):
                return False

            def discard(self):
                discarded.append(True)

        class Host:
            def adopt_transaction(self, **kwargs):
                return Ok(object())

            def detach(self):
                return True

        binding = ActionBinding("sample.Create", lambda inputs: dict(inputs),
                                lambda *args: self.fail("observer refusal precedes dispatch"),
                                validate_receipt=lambda body, native: True)
        transport = TrussActionTransport(
            connection_factory=Lease, assembly_factory=lambda host: object(),
            schemas={SOURCE: SchemaBinding(SOURCE,
                lambda assembly, tx: (_ for _ in ()).throw(ActionRefusal(ActionWireError.INVALID)),
                {binding.action_id: binding})})
        request = {"contract": "umf.access/1", "schema": SOURCE, "kind": "apply",
                   "action": "sample.Create", "inputs": {}, "idempotency_key": "rollback"}
        with (patch.object(psycopg, "Connection", Connection),
              patch("truss.psycopg_host.adopt_psycopg_host", return_value=Host())):
            response = transport.execute(request)
        self.assertEqual(response["error"]["code"], ActionWireError.WRITE_OUTCOME_UNKNOWN.value)
        self.assertEqual(discarded, [True])

    def test_closed_owned_connection_before_dispatch_is_quarantined(self):
        class Connection:
            def __init__(self):
                self.closed = False
                self.broken = False
                self.autocommit = True
                self.info = SimpleNamespace(transaction_status=pq.TransactionStatus.IDLE,
                                            backend_pid=27)
                self.pgconn = SimpleNamespace(pipeline_status=pq.PipelineStatus.OFF)
                self.statements = []

            def execute(self, statement, **kwargs):
                self.statements.append(statement)
                if statement.startswith("BEGIN"):
                    self.info.transaction_status = pq.TransactionStatus.INTRANS
                    return SimpleNamespace(statusmessage="BEGIN")
                raise AssertionError(statement)

        connection = Connection()
        discarded = []

        class Lease:
            def __enter__(self):
                return connection

            def __exit__(self, *args):
                return False

            def discard(self):
                discarded.append(True)

        class Host:
            def adopt_transaction(self, **kwargs):
                return Ok(object())

            def detach(self):
                return True

        binding = ActionBinding("sample.Create", lambda inputs: dict(inputs),
                                lambda *args: self.fail("observer fails before dispatch"),
                                validate_receipt=lambda body, native: True)

        def observe(assembly, transaction):
            connection.broken = True
            raise ActionRefusal(ActionWireError.SCHEMA_MISMATCH)

        transport = TrussActionTransport(
            connection_factory=Lease, assembly_factory=lambda host: object(),
            schemas={SOURCE: SchemaBinding(SOURCE, observe,
                                           {binding.action_id: binding})})
        request = {"contract": "umf.access/1", "schema": SOURCE, "kind": "apply",
                   "action": "sample.Create", "inputs": {}, "idempotency_key": "closed"}
        with (patch.object(psycopg, "Connection", Connection),
              patch("truss.psycopg_host.adopt_psycopg_host", return_value=Host())):
            response = transport.execute(request)
        self.assertEqual(connection.statements,
                         ["BEGIN ISOLATION LEVEL READ COMMITTED READ WRITE"])
        self.assertEqual(response["error"]["code"], ActionWireError.WRITE_OUTCOME_UNKNOWN.value)
        self.assertEqual(discarded, [True])


if __name__ == "__main__":
    unittest.main()
