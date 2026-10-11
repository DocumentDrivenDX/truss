"""Public construction/lifetime controls; native inspection has separate evidence."""
import hashlib
from importlib.resources import files
from threading import Event,Thread
import unittest
from unittest.mock import patch
from truss import (Ok,Error,PsycopgHost,InstallationObservation,
    InstallationInspectionConfiguration,AssemblyConstructionError,
    INSPECTION_ASSEMBLY_PROFILE,INSPECTION_CONSTRUCTION_DIAGNOSTIC_PROFILE,
    create_reference_assembly)

class PublicInspectionAssemblyTests(unittest.TestCase):
    def host(self):
        # Construction must not use host state; actual host execution is native-tested.
        return object.__new__(PsycopgHost)
    def config(self):
        return InstallationInspectionConfiguration(assembly_id='consumer',assembly_profile=INSPECTION_ASSEMBLY_PROFILE)
    def test_public_construction_has_no_sql_and_profiles_match_packaged_bytes(self):
        for name,pin in [('assembly-inspection.json',INSPECTION_ASSEMBLY_PROFILE),('assembly-inspection-construction-diagnostic.json',INSPECTION_CONSTRUCTION_DIAGNOSTIC_PROFILE)]:
            self.assertEqual(hashlib.sha256(files('truss').joinpath('_profiles',name).read_bytes()).hexdigest(),pin.sha256)
        host=self.host()
        with patch.object(PsycopgHost,'_cursor',side_effect=AssertionError('Construction issued SQL')):
            result=create_reference_assembly(self.config(),host)
        self.assertIsInstance(result,Ok)
        self.assertEqual(result.value.configuration.assembly_id,'consumer')
        result.value.dispose()
    def test_invalid_host_and_hostile_interface_refuse_without_caller_equality(self):
        self.assertIsInstance(create_reference_assembly(self.config(),object()),AssemblyConstructionError)
        class Hostile:
            def __eq__(self,other):raise AssertionError('Caller equality invoked')
            def __ne__(self,other):raise AssertionError('Caller equality invoked')
        config=self.config();object.__setattr__(config,'interface_version',Hostile())
        result=create_reference_assembly(config,self.host())
        self.assertIsInstance(result,AssemblyConstructionError)
        self.assertEqual(result.path,'interface_version')
        self.assertEqual(result.diagnostic_profile,INSPECTION_CONSTRUCTION_DIAGNOSTIC_PROFILE)
    def test_dispose_waits_for_observation_then_refuses_without_host_calls(self):
        host=self.host();assembly=create_reference_assembly(self.config(),host).value
        transaction=object();entered=Event();release=Event();disposed=Event();results=[]
        original=Ok(InstallationObservation(False,()))
        def observe(actual_host,actual_transaction):
            self.assertIs(actual_host,host);self.assertIs(actual_transaction,transaction)
            entered.set()
            if not release.wait(3):raise AssertionError('Test observation was not released')
            return original
        def inspect():results.append(assembly.inspect_installation(transaction))
        def dispose():assembly.dispose();disposed.set()
        with patch('truss.installation.inspect_installation_in_transaction',side_effect=observe) as operation:
            reading=Thread(target=inspect);reading.start()
            try:
                self.assertTrue(entered.wait(3))
                closing=Thread(target=dispose);closing.start()
                self.assertFalse(disposed.wait(0.05))
            finally:
                release.set();reading.join(3)
                if 'closing' in locals():closing.join(3)
            self.assertEqual(results,[original]);self.assertTrue(disposed.is_set())
            self.assertIsInstance(assembly.inspect_installation(transaction),Error)
            self.assertEqual(operation.call_count,1)

if __name__=='__main__':unittest.main()
