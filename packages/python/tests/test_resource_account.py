"""Original scalar arithmetic witnesses plus nonrefundable custody controls."""
import json
from pathlib import Path
import unittest
from truss._resource_account import BytePermitAccount, BytePermit, ByteAllocation


class BytePermitTests(unittest.TestCase):
    def test_original_arithmetic_witnesses(self):
        original = Path(__file__).resolve().parents[3] / 'docs/helix/02-design/contracts/bindings/bootstrap-permit-arithmetic-v0.1.proposal.json'
        cases = json.loads(original.read_bytes())['cases']
        for case in cases:
            with self.subTest(case=case['id']):
                producer = object()
                account = BytePermitAccount(producer, int(case['ceiling']), 1000, 20)
                owned = int(case['ownedBefore'])
                reserved = int(case['unconsumedReservedBefore'])
                initial = account.reserve(producer, owned)
                account.allocate(producer, initial, owned)
                permit = account.reserve(producer, reserved)
                allocation = None
                if 'reserveAdditional' in case:
                    amount = int(case['reserveAdditional'])
                    if case['expected'] == 'refuse':
                        with self.assertRaises(ValueError): account.reserve(producer, amount)
                        self.assertEqual(account.snapshot(producer), (owned, reserved, owned, True))
                    else:
                        account.reserve(producer, amount)
                        self.assertEqual(sum(account.snapshot(producer)[:2]), int(case['expectedCommittedCapacity']))
                elif 'allocation' in case:
                    amount = int(case['allocation'])
                    if amount > reserved:
                        with self.assertRaises(ValueError): account.allocate(producer, permit, amount)
                        self.assertEqual(account.snapshot(producer), (owned, reserved, owned, True))
                    else:
                        allocation = account.allocate(producer, permit, amount)
                        self.assertEqual(account.snapshot(producer), (int(case['ownedAfter']), int(case['unconsumedReservedAfter']), owned + amount, False))
                elif 'qualifiedOwnedRelease' in case:
                    # Split the owned footprint so release names its original allocation.
                    split = BytePermitAccount(producer, 100, 1000, 20)
                    release_amount = int(case['qualifiedOwnedRelease'])
                    permit2 = split.reserve(producer, owned)
                    original_allocation = split.allocate(producer, permit2, release_amount)
                    split.allocate(producer, permit2, owned - release_amount)
                    split.reserve(producer, reserved)
                    split.release(producer, original_allocation)
                    self.assertEqual(split.snapshot(producer), (int(case['ownedAfter']), int(case['unconsumedReservedAfter']), owned, False))
                else:
                    self.assertFalse(case['qualifiedTermination'])
                    self.assertEqual(account.snapshot(producer), (owned, int(case['unconsumedReservedAfter']), owned, False))

    def test_spent_and_unknown_custody_survive_release_and_close(self):
        producer = object(); account = BytePermitAccount(producer, 100, 100, 20)
        permit = account.reserve(producer, 100)
        allocation = account.allocate(producer, permit, 60)
        account.release(producer, allocation)
        self.assertEqual(account.snapshot(producer), (0, 40, 60, False))
        account.close(producer)
        self.assertEqual(account.snapshot(producer), (0, 40, 60, True))
        with self.assertRaises(ValueError): account.reserve(producer, 1)
        account.terminate(producer, permit)
        self.assertEqual(account.snapshot(producer), (0, 0, 60, True))
        with self.assertRaises(ValueError): account.release(producer, allocation)
        with self.assertRaises(ValueError): account.terminate(producer, permit)

    def test_original_tokens_and_atomic_cumulative_refusal(self):
        producer = object(); account = BytePermitAccount(producer, 100, 60, 20)
        permit = account.reserve(producer, 60)
        for operation in [lambda: account.allocate(object(), permit, 1),
                          lambda: account.allocate(producer, BytePermit(), 1),
                          lambda: account.release(producer, ByteAllocation()),
                          lambda: account.close(object())]:
            with self.assertRaises(ValueError): operation()
            self.assertEqual(account.snapshot(producer), (0, 60, 0, False))
        calls = []
        class Proxy:
            def __hash__(self):
                calls.append('hash')
                return hash(permit)
            def __eq__(self, other):
                calls.append('equality')
                return True
        class PermitSubclass(BytePermit):
            __hash__ = Proxy.__hash__
            __eq__ = Proxy.__eq__
        for token in (Proxy(), PermitSubclass(), []):
            for operation in (lambda: account.allocate(producer, token, 1),
                              lambda: account.terminate(producer, token),
                              lambda: account.release(producer, token)):
                with self.assertRaises(ValueError): operation()
                self.assertEqual(account.snapshot(producer), (0, 60, 0, False))
        self.assertEqual(calls, [])
        allocation = account.allocate(producer, permit, 60)
        account.release(producer, allocation)
        account.terminate(producer, permit)
        with self.assertRaises(ValueError): account.reserve(producer, 1)
        self.assertEqual(account.snapshot(producer), (0, 0, 60, True))
        for value in (-1, True, 1.0, '1'):
            with self.assertRaises(ValueError): BytePermitAccount(producer, value, 100, 20)

    def test_retained_record_capacity_never_refunded(self):
        producer = object(); account = BytePermitAccount(producer, 100, 100, 1)
        permit = account.reserve(producer, 0)
        account.terminate(producer, permit)
        with self.assertRaises(ValueError): account.reserve(producer, 0)
        self.assertEqual(account.snapshot(producer), (0, 0, 0, True))
