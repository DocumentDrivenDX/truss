# SPDX-License-Identifier: MIT OR Apache-2.0
"""A thousand-type catalog view keeps source once and transmits references."""
import base64,hashlib,json
from truss import Ok
from truss.catalog_view import CatalogViewAvailable,_definition_sources
import test_stress_registration_native as base
class CatalogViewCapacityTests(base.StressRegistrationTests):
    for name in tuple(n for n in dir(base.StressRegistrationTests) if n.startswith('test_')):locals()[name]=None
    def test_thousand_type_complete_view_is_compact_and_exact(self):
        base.StressRegistrationTests.test_many_types(self)
        c,h,a,t=self.consumer()
        result=a.catalog_view_in_transaction(t,a.catalog_view_request())
        self.assertIsInstance(result,Ok,repr(result)+' '+str(h._custody.last_attempt.error))
        self.assertIsInstance(result.value,CatalogViewAvailable,repr(result))
        view=result.value.view;self.assertEqual(len(view.definitions),16000)
        wire=json.loads(view.original_bytes)
        self.assertLess(len(view.original_bytes),16*1024*1024)
        self.assertEqual(wire['interfaceVersion'],'truss-catalog-view/0.2.0')
        self.assertTrue(all(set(entry['definition'])=={'sha256'} for entry in wire['definitions']))
        self.assertTrue(all(type(pin) is str for entry in wire['definitions'] for pin in entry['dependencies']))
        self.assertEqual(len({id(_definition_sources[id(entry.definition)][1]) for entry in view.definitions}),1)
        for entry in (view.definitions[0],view.definitions[-1]):
            raw=base64.b64decode(entry.definition.bytes_base64)
            self.assertEqual(hashlib.sha256(raw).hexdigest(),entry.definition.sha256)
        print(json.dumps({'completeViewBytes':len(view.original_bytes),'definitions':len(view.definitions),'sharedSources':1}),flush=True)
        h.detach();c.rollback()
