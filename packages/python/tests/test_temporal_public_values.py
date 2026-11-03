# SPDX-License-Identifier: MIT OR Apache-2.0
"""Construction controls for the explicit public temporal DTO namespace."""
from dataclasses import FrozenInstanceError
import base64
import json
import sys
from types import ModuleType
import unittest
from unittest.mock import Mock, patch

from truss.contracts import (
    LocalTimestampValue,
    MapEntry,
    MapValue,
    NullValue,
    ObjectKeyComponent,
    ObjectKeySelection,
    ProfilePin,
    QualifiedOwner,
    ReadTypeReference,
    SequenceValue,
    TextValue,
    TypedIdentity,
)
from truss.groups import (
    AuthoredValue as OrdinaryAuthoredValue,
    CreateEdge,
    CurrentCatalog,
    OwnedOwnership,
    RootlessOwnership,
    StoredObjectReference,
    TextOrderKey,
)
from truss.temporal import (
    AuthoredValue,
    CreateObject,
    GroupSemanticInput,
    GroupRuntimeContext,
    ImportCatalogPin,
    ImportRuntimeContext,
    ObjectFound,
    ObjectPage,
    ObjectPageCursor,
    PropertyEquals,
    RequestIdentity,
    RequestPresent,
    TemporalValues,
    ScalarObject,
    OwnedImportRuntimeContext,
    UpdateObject,
)


class TemporalPublicValueTests(unittest.TestCase):
    def setUp(self):
        self.local = LocalTimestampValue(text="2024-11-03T01:30:00.123456")
        self.profile = ProfilePin(identity="profile", version="1", sha256="a" * 64)
        self.identity = TypedIdentity(
            id="17",
            type_id="3",
            definition_pin="type-pin",
            owner=QualifiedOwner(document_id="doc", module_id="module"),
        )

    def test_temporal_authored_value_accepts_local_and_ordinary_values(self):
        local = AuthoredValue(name="seen_at", value=self.local)
        ordinary = AuthoredValue(
            name="label", value=TextValue(kind="string", text="kept exactly")
        )
        self.assertIs(local.value, self.local)
        self.assertEqual(ordinary.value.text, "kept exactly")
        with self.assertRaises(FrozenInstanceError):
            local.name = "changed"

    def test_ordinary_authored_value_remains_closed_to_local(self):
        with self.assertRaises(ValueError):
            OrdinaryAuthoredValue(name="seen_at", value=self.local)

    def test_local_value_cannot_be_nested_in_existing_containers(self):
        with self.assertRaises(ValueError):
            SequenceValue(items=(self.local,))
        with self.assertRaises(ValueError):
            ScalarObject(
                document_id="doc", module_id="module", record_id="record", id=17,
                type_id=3, definition_pin="type-pin", version=2, catalog_revision=4,
                record_revision=5, created_at="created", updated_at="updated",
                values=(), retained=(("unknown", self.local),),
            )
        with self.assertRaises(ValueError):
            MapEntry(key="seen_at", value=self.local)
        ordinary_map = MapValue(
            entries=(MapEntry(key="ordinary", value=NullValue()),)
        )
        self.assertEqual(ordinary_map.entries[0].value.kind, "null")

    def test_temporal_key_component_is_refused(self):
        with self.assertRaises(ValueError):
            ObjectKeyComponent(property_id="seen_at", definition_pin="pin", value=self.local)

    def test_create_and_update_object_are_temporal_exact_dtos(self):
        authored = AuthoredValue(name="seen_at", value=self.local)
        ordinary = OrdinaryAuthoredValue(
            name="nullable", value=NullValue()
        )
        created = CreateObject(
            type_definition_pin="type-pin",
            values=(authored, ordinary),
            ownership=RootlessOwnership(),
        )
        updated = UpdateObject(
            target=StoredObjectReference(identity=self.identity),
            set=(authored,),
            unset=(),
        )
        self.assertEqual(created.operation, "create_object")
        self.assertEqual(updated.operation, "update_object")
        with self.assertRaises(ValueError):
            CreateObject(
                type_definition_pin="type-pin",
                values=(authored,),
                ownership=OwnedOwnership(
                    root=StoredObjectReference(identity=self.identity)
                ),
                alias=object(),
            )

    def test_local_property_precondition_and_temporal_input_profile(self):
        condition = PropertyEquals(
            id="local-equality",
            reason="match local civil value",
            target=self.identity,
            name="seen_at",
            value=self.local,
        )
        operation = CreateObject(
            type_definition_pin="type-pin",
            values=(AuthoredValue(name="seen_at", value=self.local),),
            ownership=RootlessOwnership(),
        )
        semantic_input = GroupSemanticInput(
            layout_profile=self.profile,
            mutation_profile=self.profile,
            value_profile=self.profile,
            catalog=CurrentCatalog(),
            operations=(operation,),
            asserted_origin=MapValue(entries=()),
            preconditions=(condition,),
        )
        self.assertEqual(
            semantic_input.interface_version,
            "truss-group-temporal-input/0.1.0",
        )
        self.assertIs(semantic_input.operations[0], operation)
        self.assertIs(semantic_input.preconditions[0], condition)
        with self.assertRaises(ValueError):
            GroupSemanticInput(
                layout_profile=self.profile,
                mutation_profile=self.profile,
                value_profile=self.profile,
                catalog=CurrentCatalog(),
                operations=(),
                asserted_origin=MapValue(entries=()),
            )

    def test_temporal_request_identity_has_distinct_input_profile(self):
        request = RequestPresent(
            identity=RequestIdentity(
                authorized_scope_identity="scope", request_id="request-1"
            )
        )
        self.assertEqual(
            request.identity.input_profile,
            "truss-group-temporal-input/0.1.0",
        )
        self.assertEqual(
            request.identity.interface_version, "truss-request-identity/0.1.0"
        )

    def test_temporal_read_dtos_admit_local_only_as_a_top_level_value(self):
        scalar = ScalarObject(
            document_id="doc", module_id="module", record_id="record", id=17,
            type_id=3, definition_pin="type-pin", version=2, catalog_revision=4,
            record_revision=5, created_at="created", updated_at="updated",
            values=(("seen_at", self.local), ("nullable", None)), retained=(),
        )
        found = ObjectFound(object=scalar)
        page = ObjectPage(objects=(scalar,), catalog_revision=4, continuation=None)
        self.assertIs(found.object.values[0][1], self.local)
        self.assertEqual(scalar.identity.owner.document_id, "doc")
        self.assertEqual(page.profile, "truss-python-temporal-object-page/0.1")
        cursor = ObjectPageCursor(
            installation_id="install", source_epoch="epoch", release_sha256="b" * 64,
            document_id="doc", module_id="module", record_id="record", type_id=3,
            definition_pin="type-pin", catalog_revision=4, after_id=17,
            value_profile=self.profile, query_abi=self.profile,
        )
        self.assertIs(cursor.value_profile, self.profile)
        with self.assertRaises(ValueError):
            SequenceValue(items=(self.local,))

    def test_temporal_group_context_builds_selected_input_and_request(self):
        context = GroupRuntimeContext(
            layout_profile=self.profile, mutation_profile=self.profile,
            value_profile=self.profile, request_fingerprint_profile=self.profile,
            authorized_scope_identity="scope", source_epoch="epoch", history_profile="history",
            query_abi=self.profile, release_id="release", release_sha256="c" * 64,
        )
        operation = CreateObject(
            type_definition_pin="type-pin",
            values=(AuthoredValue(name="seen_at", value=self.local),),
            ownership=RootlessOwnership(),
        )
        group_input = context.input((operation,), MapValue(entries=()))
        request = context.request("request")
        self.assertEqual(group_input.interface_version, "truss-group-temporal-input/0.1.0")
        self.assertEqual(request.identity.input_profile, group_input.interface_version)
        self.assertEqual(context.query_abi, self.profile)

    def test_temporal_import_context_builds_exact_temporal_payload_wire(self):
        catalog = ImportCatalogPin(revision="4", model_bundle_sha256="d" * 64)
        context = ImportRuntimeContext(
            layout_profile=self.profile, import_profile=self.profile, value_profile=self.profile,
            payload_profile=self.profile, catalog=catalog, query_abi=self.profile,
            release_id="release", release_sha256="c" * 64,
        )
        authored = AuthoredValue(name="seen_at", value=self.local)
        payload = context.object_payload((authored,))
        wire = json.loads(base64.b64decode(payload.bytes_base64))
        self.assertEqual(wire["interfaceVersion"], "truss-import-temporal-payload/0.1.0")
        self.assertEqual(wire["values"][0]["value"], {
            "text": "2024-11-03T01:30:00.123456", "kind": "localTimestamp",
        })
        imported = context.input((), load_id="load", asserted_origin=MapValue(entries=()))
        self.assertEqual(imported.interface_version, "truss-import-temporal-input/0.1.0")
        with self.assertRaises(ValueError):
            imported.__class__(layout_profile=self.profile, import_profile=self.profile,
                value_profile=self.profile, catalog=catalog, load_id="load",
                asserted_origin=MapValue(entries=()), records=(object(),))

        owned = OwnedImportRuntimeContext(
            layout_profile=self.profile, import_profile=self.profile, value_profile=self.profile,
            payload_profile=self.profile, catalog=catalog, query_abi=self.profile,
            release_id="release", release_sha256="c" * 64,
        )
        owned_wire = json.loads(base64.b64decode(owned.object_payload((authored,)).bytes_base64))
        self.assertEqual(owned_wire["interfaceVersion"], "truss-owned-import-temporal-payload/0.1.0")

    def _payload_contexts(self):
        fields = dict(
            layout_profile=self.profile, import_profile=self.profile, value_profile=self.profile,
            payload_profile=self.profile,
            catalog=ImportCatalogPin(revision="4", model_bundle_sha256="d" * 64),
            query_abi=self.profile, release_id="release", release_sha256="c" * 64,
        )
        return ImportRuntimeContext(**fields), OwnedImportRuntimeContext(**fields)

    def _payload_root(self, cls=ObjectKeySelection):
        return cls(
            type=ReadTypeReference(type_id="3", definition_pin="type-pin",
                owner=QualifiedOwner(document_id="doc", module_id="module")),
            key_number="1", key_definition_pin="key-pin", key_encoding_profile=self.profile,
            components=(ObjectKeyComponent(property_id="id", definition_pin="id-pin",
                value=TextValue(kind="string", text="key")),),
        )

    def test_payload_values_and_source_refuse_substitutes_before_serialization(self):
        class AuthoredSubclass(AuthoredValue):
            pass

        class OrdinaryAuthoredSubclass(OrdinaryAuthoredValue):
            pass

        class TupleSubclass(tuple):
            pass

        class MapSubclass(MapValue):
            pass

        authored = AuthoredValue(name="seen_at", value=self.local)
        invalid_values = (
            {"name": "seen_at", "value": self.local},
            [authored], TupleSubclass((authored,)), self.local,
            ({"name": "seen_at", "value": self.local},), ([authored],), (self.local,),
            (AuthoredSubclass(name="seen_at", value=self.local),),
            (OrdinaryAuthoredSubclass(name="nullable", value=NullValue()),),
        )
        invalid_sources = ({}, [], self.local, MapSubclass(entries=()))
        for context in self._payload_contexts():
            cases = [("values", value, None) for value in invalid_values]
            cases += [("source", (authored,), source) for source in invalid_sources]
            for boundary, values, source in cases:
                with self.subTest(context=type(context).__name__, boundary=boundary,
                                  candidate=type(values if boundary == "values" else source).__name__):
                    with patch("truss.temporal._wire") as wire, \
                         patch("truss.temporal._bytes") as encode, \
                         patch("truss.temporal._artifact") as artifact:
                        with self.assertRaises(ValueError):
                            context.object_payload(values, source=source)
                        wire.assert_not_called()
                        encode.assert_not_called()
                        artifact.assert_not_called()

    def test_owned_payload_root_refuses_substitutes_before_serialization(self):
        class RootSubclass(ObjectKeySelection):
            pass

        _, context = self._payload_contexts()
        values = (AuthoredValue(name="seen_at", value=self.local),)
        for root in ({}, [], self.local, MapValue(entries=()), self._payload_root(RootSubclass)):
            with self.subTest(root=type(root).__name__):
                with patch("truss.temporal._wire") as wire, \
                     patch("truss.temporal._bytes") as encode, \
                     patch("truss.temporal._artifact") as artifact:
                    with self.assertRaises(ValueError):
                        context.object_payload(values, root=root)
                    wire.assert_not_called()
                    encode.assert_not_called()
                    artifact.assert_not_called()

    def test_payload_builders_preserve_valid_mixed_values_source_and_root(self):
        source = MapValue(entries=(MapEntry(key="original",
            value=TextValue(kind="string", text="unchanged source")),))
        values = (
            AuthoredValue(name="seen_at", value=self.local),
            OrdinaryAuthoredValue(name="nullable", value=NullValue()),
            AuthoredValue(name="items", value=SequenceValue(items=(NullValue(),))),
            OrdinaryAuthoredValue(name="empty_map", value=MapValue(entries=())),
        )
        for context in self._payload_contexts():
            with self.subTest(context=type(context).__name__):
                kwargs = {"source": source}
                if type(context) is OwnedImportRuntimeContext:
                    kwargs["root"] = self._payload_root()
                artifact = context.object_payload(values, **kwargs)
                wire = json.loads(base64.b64decode(artifact.bytes_base64))
                self.assertEqual(wire["values"], [
                    {"name": "seen_at", "value": {"kind": "localTimestamp", "text": self.local.text}},
                    {"name": "nullable", "value": {"kind": "null"}},
                    {"name": "items", "value": {"kind": "sequence", "items": [{"kind": "null"}]}},
                    {"name": "empty_map", "value": {"kind": "map", "entries": []}},
                ])
                self.assertEqual(wire["source"], {"kind": "map", "entries": [
                    {"key": "original", "value": {"kind": "string", "text": "unchanged source"}},
                ]})
                if type(context) is OwnedImportRuntimeContext:
                    self.assertEqual(wire["ownership"]["state"], "owned")
                    self.assertEqual(wire["ownership"]["root"]["operation"], "object_key")
                else:
                    self.assertEqual(wire["ownership"], {"state": "rootless"})

    def test_temporal_edge_values_are_not_admitted_by_edge_dto(self):
        with self.assertRaises(ValueError):
            CreateEdge(
                relationship_definition_pin="relationship-pin",
                source=StoredObjectReference(identity=self.identity),
                target=StoredObjectReference(identity=self.identity),
                values=(AuthoredValue(name="seen_at", value=self.local),),
                order_key=TextOrderKey(text="position"),
            )

    def test_null_and_ordinary_sequence_values_remain_available(self):
        ordinary_sequence = SequenceValue(
            items=(NullValue(), TextValue(kind="string", text="ordinary"))
        )
        self.assertEqual(ordinary_sequence.kind, "sequence")
        self.assertIsInstance(NullValue(), NullValue)

    def test_facade_constructor_is_inert_and_dispatch_is_exact(self):
        calls = []
        result = object()

        class AssemblyProbe:
            def _temporal_values_operation(self, operation, arguments):
                calls.append((operation, arguments))
                return result

        assembly = AssemblyProbe()
        facade = TemporalValues(assembly)
        self.assertIs(facade._assembly, assembly)
        self.assertEqual(calls, [])
        with self.assertRaises(TypeError):
            facade.complete_in_transaction(object(), unexpected=True)

        transaction = object()
        prepared = object()
        input_value = object()
        request = object()
        docs = (object(),)
        entity = object()
        cursor = object()
        source = object()
        invocations = (
            ("prepare_catalog", (docs,), {}, {"documents": docs, "bun_executable": "bun", "source_version": None}),
            ("accept_in_transaction", (transaction, prepared), {"request_key": "r"}, {
                "transaction": transaction, "prepared": prepared, "request_key": "r",
                "origin_bytes": b"{}", "bun_executable": "bun", "expected_revision": None,
                "expected_documents": (),
            }),
            ("group_context_in_transaction", (transaction,), {}, {"transaction": transaction}),
            ("apply_in_transaction", (transaction, input_value, request), {}, {
                "transaction": transaction, "input": input_value, "request": request,
                "documents": (), "bun_executable": "bun",
            }),
            ("dry_run_in_transaction", (transaction, input_value), {}, {
                "transaction": transaction, "input": input_value, "documents": (),
            }),
            ("complete_in_transaction", (transaction,), {}, {"transaction": transaction}),
            ("import_context_in_transaction", (transaction,), {}, {"transaction": transaction}),
            ("owned_import_context_in_transaction", (transaction,), {}, {"transaction": transaction}),
            ("object_import_record_in_transaction", (transaction,), {
                "document_id": "d", "module_id": "m", "record_id": "r", "values": (),
            }, {"transaction": transaction, "document_id": "d", "module_id": "m",
                "record_id": "r", "values": (), "source": None}),
            ("owned_object_import_record_in_transaction", (transaction,), {
                "document_id": "d", "module_id": "m", "record_id": "r", "values": (),
            }, {"transaction": transaction, "document_id": "d", "module_id": "m",
                "record_id": "r", "values": (), "root": None, "source": None}),
            ("import_in_transaction", (transaction, input_value), {"documents": docs}, {
                "transaction": transaction, "input": input_value, "documents": docs,
                "bun_executable": "bun",
            }),
            ("get_object_in_transaction", (transaction,), {
                "document_id": "d", "module_id": "m", "record_id": "r", "object_id": 4,
            }, {"transaction": transaction, "document_id": "d", "module_id": "m",
                "record_id": "r", "object_id": 4, "maximum_bytes": 1048576}),
            ("page_objects_in_transaction", (transaction,), {
                "document_id": "d", "module_id": "m", "record_id": "r",
            }, {"transaction": transaction, "document_id": "d", "module_id": "m",
                "record_id": "r", "limit": 100, "cursor": None, "maximum_bytes": 1048576}),
            ("lookup_key_in_transaction", (transaction,), {
                "document_id": "d", "module_id": "m", "record_id": "r", "key_id": "k",
                "values": (),
            }, {"transaction": transaction, "document_id": "d", "module_id": "m",
                "record_id": "r", "key_id": "k", "values": (), "original_document": None,
                "maximum_bytes": 1048576, "bun_executable": "bun"}),
            ("page_history_in_transaction", (transaction,), {"entity": entity}, {
                "transaction": transaction, "entity": entity, "cursor": None,
                "maximum_events": 4096, "maximum_bytes": 8388608,
            }),
            ("reconstruct_in_transaction", (transaction,), {"entity": entity, "version": 3}, {
                "transaction": transaction, "entity": entity, "version": 3,
                "maximum_events": 4096, "maximum_bytes": 8388608,
            }),
            ("recover_group_request_in_transaction", (transaction, source), {}, {
                "transaction": transaction, "frame": source,
            }),
        )
        for operation, args, kwargs, expected in invocations:
            with self.subTest(operation=operation):
                calls.clear()
                returned = getattr(facade, operation)(*args, **kwargs)
                self.assertIs(returned, result)
                self.assertEqual(calls, [(operation, expected)])

    def test_freeze_group_request_uses_only_temporal_runtime_delegate(self):
        returned = object()
        freezer = Mock(return_value=returned)
        runtime = ModuleType("truss._temporal_runtime")
        runtime.freeze_group_request = freezer
        documents = (object(),)
        semantic_input = GroupSemanticInput(
            layout_profile=self.profile,
            mutation_profile=self.profile,
            value_profile=self.profile,
            catalog=CurrentCatalog(),
            operations=(CreateObject(
                type_definition_pin="type-pin", values=(), ownership=RootlessOwnership()
            ),),
            asserted_origin=MapValue(entries=()),
        )
        from truss.temporal import RequestPresent, RequestIdentity, freeze_group_request

        request = RequestPresent(identity=RequestIdentity(
            authorized_scope_identity="scope", request_id="req"
        ))
        with unittest.mock.patch.dict(sys.modules, {"truss._temporal_runtime": runtime}):
            self.assertIs(
                freeze_group_request(semantic_input, request, documents=documents), returned
            )
        freezer.assert_called_once_with(semantic_input, request, documents=documents)


if __name__ == "__main__":
    unittest.main()
