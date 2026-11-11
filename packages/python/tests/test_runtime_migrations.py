# SPDX-License-Identifier: MIT OR Apache-2.0
"""Fast original recipe/registry admission controls; native proof is separate."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
import importlib.util
import hashlib
from unittest.mock import patch
from truss._migration_recipe import load_recipe,plan_route
from truss.recovery_registry import HostRecoveryRegistry
from truss.migrations import RuntimeMigrations


class MigrationRecipeTests(unittest.TestCase):
    def test_packaged_target_is_the_fresh_baseline(self):
        """@covers US-045-AC6"""
        manifest,artifacts,digest=load_recipe()
        self.assertEqual(manifest['sources'],[])
        self.assertEqual(manifest['edges'],[])
        profile=json.loads(artifacts[manifest['target']+'.json'])
        self.assertTrue(profile['inventory']['routines'])
        self.assertEqual(profile['sha256'],manifest['target'])
        self.assertEqual(len(digest),64)

    def test_skipped_release_uses_only_latest_tool_and_cycles_refuse(self):
        """@covers US-045-AC8: metadata planning only, not native chain qualification."""
        manifest={'target':'latest','edges':[
            {'source':'old','target':'previous','direction':'forward','artifact':'first'},
            {'source':'previous','target':'latest','direction':'forward','artifact':'second'}]}
        self.assertEqual([e['artifact'] for e in plan_route(manifest,'old')],['first','second'])
        with self.assertRaisesRegex(ValueError,'No declared'):plan_route(manifest,'unknown')
        manifest['edges']+=[{'source':'unselected','target':'unselected','direction':'forward','artifact':'bad'}]
        with self.assertRaisesRegex(ValueError,'forward'):plan_route(manifest,'old')

    def test_artifact_corruption_refuses_before_connection(self):
        """@covers US-045-AC6"""
        from importlib.resources import files
        import shutil
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            shutil.copytree(files('truss').joinpath('_migrations'),root/'_migrations')
            shutil.copytree(files('truss').joinpath('_catalog_runtime'),root/'_catalog_runtime')
            manifest=json.loads((root/'_migrations/manifest.json').read_bytes())
            target=root/'_migrations'/(manifest['target']+'.json');target.write_bytes(target.read_bytes()+b' ')
            with patch('truss._migration_recipe.files',return_value=root),self.assertRaisesRegex(ValueError,'integrity'):
                load_recipe()

    def test_nondurable_recovery_refuses(self):
        class Registry:retention='process_lifetime'
        with self.assertRaisesRegex(ValueError,'Restart-durable'):
            RuntimeMigrations(lambda: self.fail('No connection'),Registry())

    def test_dynamic_initialization_policy_admits_only_the_closed_target_profile(self):
        """@covers US-045-AC6 @covers US-045-AC7"""
        from truss._migration_verify import matches_inventory
        manifest,artifacts,_=load_recipe();profile=json.loads(artifacts[manifest['target']+'.json'])
        self.assertEqual(len(profile['initializationPolicies']),1)
        self.assertEqual(profile['initializationAlternatives'],[])
        self.assertEqual(profile['definitionAlternatives'],[])
        # An installation without the new custody policy is never admitted by inventory alone.
        legacy=copy.deepcopy(profile);del legacy['initializationPolicies']
        self.assertFalse(matches_inventory(profile['inventory'],legacy))


class RecoveryRegistryTests(unittest.TestCase):
    def test_original_evidence_conflict_restart_and_observation_order(self):
        """@covers US-045-AC7"""
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'registry.sqlite';registry=HostRecoveryRegistry(path)
            original={'obligationId':'attempt','target':{'kind':'installed','installationId':'one'},'originalEvidence':{'recipe':'original'}}
            reference=registry.register(original)
            self.assertEqual(registry.register(original),reference)
            changed=copy.deepcopy(original);changed['originalEvidence']['recipe']='changed'
            with self.assertRaisesRegex(ValueError,'conflict'):registry.register(changed)
            observation={'observationId':'first','expectedPreviousObservationId':None,'applicationDurability':'unknown'}
            registry.append(reference,observation)
            restarted=HostRecoveryRegistry(path)
            observed=restarted.inspect(reference,original['target'])
            self.assertEqual(observed,{'obligation':original,'observations':[observation]})
            with self.assertRaisesRegex(ValueError,'conflict'):restarted.append(reference,observation)
            with self.assertRaisesRegex(ValueError,'context'):restarted.inspect(reference,{'kind':'installed','installationId':'other'})
            self.assertEqual(path.stat().st_mode & 0o777,0o600)

    def test_latest_runtime_has_no_predecessor_application_import(self):
        """@covers US-045-AC8"""
        from importlib.resources import files
        root=files('truss')
        for name in ['_group_runtime.py','_query_runtime.py','catalog_preparation.py']:
            self.assertNotIn('_migration_',root.joinpath(name).read_text())
