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
    def test_exact_packaged_target_and_predecessors(self):
        """@covers US-045-AC6"""
        manifest,artifacts,digest=load_recipe()
        self.assertGreaterEqual(len(manifest['sources']),2)
        self.assertIn('9f6aab31802e9bebcd886f735ba9fe0bb405e69d3501a32f36cee8827b544d00',manifest['sources'])
        for source in manifest['sources']:
            self.assertNotEqual(source,manifest['target'])
            self.assertTrue(json.loads(artifacts[source+'.json'])['inventory']['routines'])
            self.assertTrue(json.loads(artifacts[next(e['artifact'] for e in manifest['edges'] if e['source']==source)])['steps'])
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
            target=root/'_migrations'/manifest['edges'][0]['artifact'];target.write_bytes(target.read_bytes()+b' ')
            with patch('truss._migration_recipe.files',return_value=root),self.assertRaisesRegex(ValueError,'integrity'):
                load_recipe()

    def test_nondurable_recovery_refuses(self):
        class Registry:retention='process_lifetime'
        with self.assertRaisesRegex(ValueError,'Restart-durable'):
            RuntimeMigrations(lambda: self.fail('No connection'),Registry())

    def test_only_exact_native_initialization_profiles_are_admitted_and_preserved(self):
        """@covers US-045-AC6 @covers US-045-AC7"""
        from truss._migration_verify import matches_inventory,require_preserved_initialization
        manifest,artifacts,_=load_recipe();profile=json.loads(artifacts[manifest['sources'][0]+'.json'])
        rule=profile['initializationAlternatives'][0]
        selected=next(i for i,row in enumerate(profile['inventory']['relations']) if row[0]==rule['identity'][0])
        for row in rule['rows']:
            observed=copy.deepcopy(profile['inventory']);observed['relations'][selected]=row
            self.assertTrue(matches_inventory(observed,profile))
        changed=copy.deepcopy(profile);changed['inventory']['relations'][selected]=next(row for row in rule['rows'] if row!=profile['inventory']['relations'][selected])
        with self.assertRaisesRegex(ValueError,'original native initialization'):require_preserved_initialization(profile,changed)
        altered=copy.deepcopy(profile['inventory']);altered['relations'][selected][7]+=' '
        self.assertFalse(matches_inventory(altered,profile))
        altered=copy.deepcopy(profile['inventory']);altered['relations'][selected][3]=True
        self.assertFalse(matches_inventory(altered,profile))


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


class ReleaseLineageTests(unittest.TestCase):
    def test_previous_sources_target_and_published_bytes_cannot_be_dropped(self):
        """@covers US-045-AC8: release gate controls, not native chain proof."""
        path=Path(__file__).resolve().parents[3]/'scripts/qualify-runtime-migrations.py'
        spec=importlib.util.spec_from_file_location('migration_gate',path)
        gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
        original=json.dumps({'sources':['old'],'target':'previous','immutableFiles':['edge'],
                             'files':{'edge':'frozen'}}).encode()
        digest=hashlib.sha256(original).hexdigest();archive=digest+'.manifest.json'
        current={'sources':['old','previous'],'target':'latest','immutableFiles':['edge',archive],
                 'files':{'edge':'frozen',archive:digest}}
        gate.validate_previous_manifest(current,original)
        unchanged=copy.deepcopy(current);unchanged['target']='previous';unchanged['sources']=['old']
        gate.validate_previous_manifest(unchanged,original)
        for field,value,message in [('sources',['previous'],'strands'),('immutableFiles',['edge'],'Archive'),
                                     ('immutableFiles',[archive],'immutable custody'),
                                     ('files',{'edge':'rewritten',archive:digest},'changed')]:
            broken=copy.deepcopy(current);broken[field]=value
            with self.assertRaisesRegex(AssertionError,message):gate.validate_previous_manifest(broken,original)
