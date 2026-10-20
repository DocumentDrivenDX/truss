# SPDX-License-Identifier: MIT OR Apache-2.0
"""Host-side group input checks that do not need PostgreSQL."""
from dataclasses import fields
import base64
import unittest

from truss._group_runtime import apply_group
from truss.contracts import MapValue, ProfilePin, TextValue
from truss.execution import Ok
from truss.groups import (CreateObject, CurrentCatalog, GroupFailed,
    GroupSemanticInput, InvalidGroupInput, RequestNone, RootlessOwnership, AuthoredValue)


class NoHostCall:
    def _run_operation(self, *args, **kwargs):
        raise AssertionError('malformed preconditions must be refused before host access')


class GroupRuntimeBoundsTests(unittest.TestCase):
    def test_non_tuple_preconditions_are_typed_input_refusals_before_host_access(self):
        pin = ProfilePin(identity='fixture', version='0.1', sha256='0' * 64)
        operation = CreateObject(type_definition_pin='definition',
            values=(AuthoredValue(name='label', value=TextValue(kind='string', text='one')) ,),
            ownership=RootlessOwnership())
        original = GroupSemanticInput(layout_profile=pin,
            mutation_profile=ProfilePin(identity='truss-rootless-scalar-graph', version='0.4',
                sha256='b814eb5b33ff59340d2f9bd13866ccb97d49f42fd38ce1e9c97facab5668a2f8'),
            value_profile=pin, catalog=CurrentCatalog(), operations=(operation,),
            asserted_origin=MapValue(entries=()))
        for malformed in (None, [], 129, iter(())):
            with self.subTest(malformed=type(malformed).__name__):
                candidate = object.__new__(GroupSemanticInput)
                for member in fields(original):
                    object.__setattr__(candidate, member.name,
                        malformed if member.name == 'preconditions' else getattr(original, member.name))
                result = apply_group(NoHostCall(), None, candidate,
                    RequestNone(), None, None, None, None)
                self.assertIsInstance(result, Ok)
                self.assertIsInstance(result.value, GroupFailed)
                self.assertIsInstance(result.value.failure, InvalidGroupInput)
                self.assertEqual(base64.b64decode(result.value.failure.diagnostic.bytes_base64, validate=True),
                    b'{"code":"preconditions_shape"}')


if __name__ == '__main__':
    unittest.main()
