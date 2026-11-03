# SPDX-License-Identifier: MIT OR Apache-2.0
"""Construction controls for the explicit public temporal DTO namespace."""
from dataclasses import FrozenInstanceError
import unittest

from truss.contracts import (
    LocalTimestampValue,
    MapEntry,
    MapValue,
    NullValue,
    ObjectKeyComponent,
    ProfilePin,
    QualifiedOwner,
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
    PropertyEquals,
    RequestIdentity,
    RequestPresent,
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


if __name__ == "__main__":
    unittest.main()
