"""Immutable comparison custody only; historical native receipt is no authority."""
from dataclasses import replace
import json
from pathlib import Path
import unittest
from truss._action_store import ActionStoreObservation, _capture_action_store_context


class ActionStoreContextTests(unittest.TestCase):
    def original(self):
        root=Path(__file__).resolve().parents[3]
        report=json.loads((root/'docs/helix/04-build/evidence/action-store-20261014/receipt.json').read_bytes())
        raw=bytes.fromhex(report['actionStore']['receiptHex']);r=json.loads(raw)
        return ActionStoreObservation(bytes.fromhex(r['registrationKeyHex']),raw,
            bytes.fromhex(r['storeIdentityHex']),bytes.fromhex(r['tenantIdentityHex']),
            bytes.fromhex(r['epochIdentityHex']),r['installationId'],'matches')

    def test_capture_does_not_retain_caller_context_or_mutable_fields(self):
        context=self.original();captured=_capture_action_store_context(context)
        self.assertEqual(captured,context);self.assertIsNot(captured,context)
        # A hostile trusted-host object may bypass frozen dataclass assignment;
        # the captured comparison must still retain its original immutable bytes.
        object.__setattr__(context,'store_identity',b'changed-after-capture')
        self.assertNotEqual(captured.store_identity,context.store_identity)
        original=self.original()
        for field in ('registration_key','receipt_bytes','store_identity','tenant_identity','epoch_identity'):
            for carrier in (bytearray(getattr(original,field)),memoryview(getattr(original,field))):
                with self.subTest(field=field,carrier=type(carrier).__name__):
                    with self.assertRaises(ValueError):_capture_action_store_context(replace(original,**{field:carrier}))

    def test_changed_components_and_nonexact_labels_cannot_compare_as_original(self):
        original=self.original()
        class Text(str):pass
        for field in ('installation_id','binding_correspondence'):
            with self.assertRaises(ValueError):_capture_action_store_context(replace(original,**{field:Text(getattr(original,field))}))
        for field in ('registration_key','store_identity','tenant_identity','epoch_identity'):
            with self.assertRaises(ValueError):_capture_action_store_context(replace(original,**{field:b'changed'}))
        with self.assertRaises(ValueError):_capture_action_store_context(replace(original,authority=0))
        malformed=json.loads(original.receipt_bytes);del malformed['logicalStoreId']
        with self.assertRaises(ValueError):_capture_action_store_context(replace(original,receipt_bytes=json.dumps(malformed).encode()))
        deep=b'['*2000+b'0'+b']'*2000
        with self.assertRaises(ValueError):_capture_action_store_context(replace(original,receipt_bytes=deep))
        fenced=_capture_action_store_context(replace(original,binding_correspondence='fenced'))
        self.assertFalse(fenced.binding_matches)  # Receipt recognition survives fencing.
