# SPDX-License-Identifier: MIT OR Apache-2.0
"""Real temporary-Git ancestry/cleanliness controls; no native capability issued."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from temporal_qualification_support import assert_qualification_checkout,commit_tree,validate_capture_transition,journal_custody_inputs,_JH_INPUTS


class TemporalQualificationProvenanceTests(unittest.TestCase):
    def git(self,*args):
        return subprocess.check_output(['git','-C',str(self.root),*args],stderr=subprocess.PIPE).decode().strip()
    def write(self,name,body):
        p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(body);return p
    def commit(self):
        self.git('add','.');self.git('-c','user.name=Qualification Control','-c','user.email=control@example.invalid','commit','-qm','control')
        c=self.git('rev-parse','HEAD');return c,commit_tree(self.root,c)
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);self.root=Path(temp.name).resolve()
        self.git('init','-q');self.native='d'*64;self.payload={'code.py':sha256(b'original').hexdigest()}
        self.write('packages/python/src/truss/code.py','original')
        self.write('scripts/capture-temporal-native-inventory.py','# original capture producer\n')
        self.write('scripts/truss-release-cohort.json','{"sealed":true}')
        self.write('packages/python/src/truss/_migrations/frozen075.json','original frozen bytes')
        self.write('packages/python/src/truss/_migrations/manifest.json','{}')
        self.capture,self.capture_tree=self.commit()
        self.receipt={'sourceCommit':self.capture,'sourceTree':self.capture_tree,
            'sourceIdentity':{'commit':self.capture,'tree':self.capture_tree,'qualificationInputsClean':True},
            'runtimeManifestSha256':self.native,'nonMigrationPackageFiles':self.payload,
            'producerSha256':sha256(b'# original capture producer\n').hexdigest()}
    def baseline(self):
        body='{"actual-capture-shape-control":true}'
        self.write('packages/python/src/truss/_migrations/fresh076.json',body)
        self.write('packages/python/src/truss/_migrations/manifest.json',json.dumps({'target':self.native,
            'targetRelease':'truss-catalog-runtime/0.76-temporal-candidate','baseline':{'fresh':True},
            'sources':[],'edges':[],'sourceWheels':{},'files':{'fresh076.json':sha256(body.encode()).hexdigest()}}))
    def validate(self,c,t,receipt=None):
        return validate_capture_transition(self.root,self.receipt if receipt is None else receipt,c,t,
            native_digest=self.native,nonmigration_payload=self.payload)
    def test_real_descendant_preserves_original_capture_commit_tree(self):
        self.baseline();final,tree=self.commit();before=dict(self.receipt)
        result=self.validate(final,tree)
        self.assertEqual(result['captureCommit'],self.capture);self.assertEqual(result['captureTree'],self.capture_tree)
        self.assertEqual(result['finalCommit'],final);self.assertEqual(result['finalTree'],tree);self.assertEqual(self.receipt,before)
        self.assertEqual(len(result['interveningPackagePaths']),2)
    def test_nonmigration_package_change_and_change_then_revert_refuse(self):
        for revert in (False,True):
            with self.subTest(reverted=revert):
                self.git('reset','--hard',self.capture)
                self.write('packages/python/src/truss/code.py','changed');self.commit()
                if revert:self.write('packages/python/src/truss/code.py','original');self.commit()
                self.baseline();c,t=self.commit()
                with self.assertRaisesRegex(ValueError,'requires a new source capture'):self.validate(c,t)
    def test_seal_or_frozen_inventory_changes_refuse(self):
        for path in ('scripts/truss-release-cohort.json','packages/python/src/truss/_migrations/frozen075.json'):
            with self.subTest(path=path):
                self.git('reset','--hard',self.capture);self.baseline();self.write(path,'altered');c,t=self.commit()
                with self.assertRaises(ValueError):self.validate(c,t)
    def test_wrong_tree_payload_native_manifest_and_nonancestor_refuse(self):
        self.baseline();c,t=self.commit()
        with self.assertRaises(ValueError):self.validate(c,'0'*40)
        for field,value in (('sourceTree','0'*40),('nonMigrationPackageFiles',{}),('runtimeManifestSha256','a'*64),('sourceIdentity',{})):
            with self.subTest(field=field),self.assertRaises(ValueError):self.validate(c,t,{**self.receipt,field:value})
        self.git('checkout','--orphan','unrelated');self.git('rm','-rf','.');self.baseline();other,other_tree=self.commit()
        with self.assertRaises(ValueError):self.validate(other,other_tree)
    def test_dirty_tracked_staged_or_untracked_inputs_refuse(self):
        c,t=self.capture,self.capture_tree
        self.write('packages/python/src/truss/code.py','dirty')
        with self.assertRaisesRegex(ValueError,'Dirty tracked'):assert_qualification_checkout(self.root,c,t)
        self.git('add','.');self.write('packages/python/src/truss/code.py','original')
        with self.assertRaisesRegex(ValueError,'Dirty tracked'):assert_qualification_checkout(self.root,c,t)
        self.git('reset','--hard',c);self.write('scripts/unreviewed.py','print("unreviewed")')
        with self.assertRaisesRegex(ValueError,'Uncommitted'):assert_qualification_checkout(self.root,c,t)
    def test_scoped_evidence_and_planner_work_are_not_input_exemptions(self):
        c,t=self.capture,self.capture_tree
        self.write('docs/helix/04-build/temporal-interface-freeze.md','intentional planner work')
        output=self.root/'docs/helix/04-build/evidence/design-audit/run-one'
        self.write(str(output.relative_to(self.root)/'log.json'),'{}')
        with self.assertRaises(ValueError):assert_qualification_checkout(self.root,c,t)
        self.assertTrue(assert_qualification_checkout(self.root,c,t,evidence_roots=[output])['qualificationInputsClean'])
        with self.assertRaises(ValueError):assert_qualification_checkout(self.root,c,t,evidence_roots=[self.root/'scripts'])
        with self.assertRaises(ValueError):assert_qualification_checkout(self.root,c,t,evidence_roots=[self.root.parent])
        with self.assertRaises(ValueError):assert_qualification_checkout(self.root,c,'0'*40,evidence_roots=[output])

    def test_final_capture_script_change_keeps_original_producer_provenance(self):
        self.baseline();self.write('scripts/capture-temporal-native-inventory.py','# later reviewed driver source\n')
        c,t=self.commit();result=self.validate(c,t)
        self.assertEqual(result['captureCommit'],self.capture)
        self.assertEqual(self.receipt['producerSha256'],sha256(b'# original capture producer\n').hexdigest())
    def test_ignored_executable_input_is_not_a_clean_tree(self):
        self.write('.gitignore','scripts/ignored.py\n');c,t=self.commit()
        self.write('scripts/ignored.py','unreviewed input')
        with self.assertRaisesRegex(ValueError,'Uncommitted'):assert_qualification_checkout(self.root,c,t)

    def executable_evidence_symlink_refuses(self,*,ignored):
        link_name='scripts/evidence-input.py'
        c,t=self.capture,self.capture_tree
        if ignored:
            self.write('.gitignore',link_name+'\n');c,t=self.commit()
        for external in (False,True):
            with self.subTest(ignored=ignored,externalEvidence=external),tempfile.TemporaryDirectory() as directory:
                evidence=Path(directory).resolve() if external else self.root/'docs/helix/04-build/evidence/design-audit/symlink-run'
                evidence.mkdir(parents=True,exist_ok=True)
                payload=evidence/'generated.py';payload.write_text('# generated evidence, not executable input\n')
                self.assertTrue(assert_qualification_checkout(self.root,c,t,evidence_roots=[evidence])['qualificationInputsClean'])
                link=self.root/link_name;link.symlink_to(payload)
                try:
                    with self.assertRaisesRegex(ValueError,'scripts/evidence-input.py'):
                        assert_qualification_checkout(self.root,c,t,evidence_roots=[evidence])
                finally:
                    link.unlink();payload.unlink()
                    if not external:evidence.rmdir()

    def test_untracked_executable_symlink_to_approved_evidence_refuses(self):
        self.executable_evidence_symlink_refuses(ignored=False)

    def test_ignored_executable_symlink_to_approved_evidence_refuses(self):
        self.executable_evidence_symlink_refuses(ignored=True)

    def test_lexical_evidence_file_cannot_resolve_outside_approved_root(self):
        with tempfile.TemporaryDirectory() as directory:
            external=Path(directory)/'external.py';external.write_text('# external\n')
            evidence=self.root/'docs/helix/04-build/evidence/design-audit/escape-run';evidence.mkdir(parents=True)
            (evidence/'escaped.py').symlink_to(external)
            with self.assertRaises(ValueError):
                assert_qualification_checkout(self.root,self.capture,self.capture_tree,evidence_roots=[evidence])

    def prepare_journal_inputs(self):
        for name in _JH_INPUTS:
            if not (self.root/name).exists():self.write(name,'original custody input\n')
        self.capture,self.capture_tree=self.commit()
        self.receipt.update(sourceCommit=self.capture,sourceTree=self.capture_tree,
            sourceIdentity={'commit':self.capture,'tree':self.capture_tree,'qualificationInputsClean':True},
            journalCustodyInputs=journal_custody_inputs(self.root,self.capture))

    def test_journal_governing_inputs_cannot_use_planner_or_missing_receipt_exemption(self):
        self.prepare_journal_inputs()
        self.assertEqual(len(journal_custody_inputs(self.root,self.capture)),len(_JH_INPUTS))
        self.baseline();c,t=self.commit()
        self.assertEqual(self.validate(c,t)['captureCommit'],self.capture)
        missing=dict(self.receipt);missing.pop('journalCustodyInputs')
        with self.assertRaisesRegex(ValueError,'Custody code/schema/plan'):self.validate(c,t,missing)
        self.write('docs/helix/04-build/temporal-native-qualification-plan.md','dirty governance')
        with self.assertRaises(ValueError):assert_qualification_checkout(self.root,c,t)
        with self.assertRaises(ValueError):self.validate(c,t)

    def test_changed_then_reverted_journal_governance_requires_fresh_capture(self):
        self.prepare_journal_inputs();name='docs/helix/04-build/temporal-native-qualification-plan.md'
        self.write(name,'intervening changed governance');self.commit()
        self.write(name,'original custody input\n');self.commit()
        self.baseline();c,t=self.commit()
        with self.assertRaisesRegex(ValueError,'requires a new source capture'):self.validate(c,t)
