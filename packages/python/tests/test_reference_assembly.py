# SPDX-License-Identifier: MIT OR Apache-2.0
import unittest
from dataclasses import replace
from truss.assembly import (INERT_ASSEMBLY_PROFILE,create_reference_assembly,HostServices,RecoveryServiceRegistration)
from truss.assembly_contracts import ReferenceAssemblyConfiguration,RecoveryConfiguration,AssemblyConstructionError
from truss.contracts import ProfilePin,CapabilitySelection
from truss import Ok

def configuration(identity='one'):
    p=ProfilePin(identity='declared',version='1',sha256='0'*64)
    return ReferenceAssemblyConfiguration(assembly_id=identity,assembly_profile=INERT_ASSEMBLY_PROFILE,
        recovery=RecoveryConfiguration(registry_profile=p,retention='process_lifetime'),database_identity='db',schema='truss',
        capabilities=(CapabilitySelection(family='catalog',capability_profile=p,layout_profile=p,adapter_profile=p,value_profile=p,policy_profile=p),))

class AssemblyTests(unittest.TestCase):
    def test_original_services_are_never_called_and_disposal_is_local(self):
        class Trap:
            def __getattribute__(self,name):raise AssertionError('Host callback')
        cfg=configuration();executor=Trap();registry=Trap()
        services=HostServices(recovery_registry=RecoveryServiceRegistration(profile=cfg.recovery.registry_profile,retention='process_lifetime',implementation=registry))
        a=create_reference_assembly(cfg,executor,services);b=create_reference_assembly(configuration('two'),executor,services)
        self.assertIsInstance(a,Ok);self.assertIsInstance(b,Ok)
        a.value.dispose()
        self.assertEqual(a.value.catalog(cfg.capabilities[0]).reason,'disposed')
        self.assertEqual(b.value.catalog(cfg.capabilities[0]).reason,'selection')
        self.assertEqual(b.value.observe_readiness(cfg.capabilities[0]).value.state,'unverified')
    def test_configuration_snapshot_survives_original_mutation(self):
        cfg=configuration();services=HostServices(recovery_registry=RecoveryServiceRegistration(profile=cfg.recovery.registry_profile,retention='process_lifetime',implementation=object()))
        result=create_reference_assembly(cfg,object(),services).value
        object.__setattr__(cfg.capabilities[0].layout_profile,'identity','changed')
        object.__setattr__(cfg,'schema','changed')
        self.assertEqual(result.configuration.schema,'truss')
        self.assertEqual(result.configuration.capabilities[0].layout_profile.identity,'declared')
    def test_invalid_configuration_uses_release_diagnostic(self):
        result=create_reference_assembly({},object(),object())
        self.assertIsInstance(result,AssemblyConstructionError)
        self.assertEqual(result.diagnostic_profile.identity,'truss-python-assembly-construction-diagnostic')

    def test_interface_version_rejects_callback_before_comparison(self):
        class Trap:
            def __eq__(self,other):raise AssertionError('Caller equality callback')
        cfg=configuration()
        object.__setattr__(cfg,'interface_version',Trap())
        result=create_reference_assembly(cfg,object(),object())
        self.assertIsInstance(result,AssemblyConstructionError)
        self.assertEqual(result.path,'interface_version')

    def test_readiness_cannot_claim_available_without_evidence(self):
        from truss.assembly import CapabilityReadiness
        with self.assertRaises(ValueError):
            CapabilityReadiness(selection=configuration().capabilities[0],state='available')

    def test_direct_constructor_does_not_bypass_capture(self):
        from truss.assembly import ReferenceAssembly
        with self.assertRaises(ValueError):ReferenceAssembly(configuration(),object(),object())

    def test_packaged_diagnostic_matches_fixed_owner_pin(self):
        import hashlib,json
        from importlib.resources import files
        from truss.assembly import CONSTRUCTION_DIAGNOSTIC_PROFILE
        raw=files('truss').joinpath('_profiles/assembly-construction-diagnostic.json').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),CONSTRUCTION_DIAGNOSTIC_PROFILE.sha256)
        document=json.loads(raw)
        self.assertEqual(document['identity'],CONSTRUCTION_DIAGNOSTIC_PROFILE.identity)
