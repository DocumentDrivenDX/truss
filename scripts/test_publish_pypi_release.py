from __future__ import annotations

import hashlib
import io
import json
import sys
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
import publish_pypi_release as publisher


def wheel(metadata: bytes) -> bytes:
    result = io.BytesIO()
    with zipfile.ZipFile(result, "w") as archive:
        archive.writestr("truss_toolkit-0.0.50.dist-info/METADATA", metadata)
    return result.getvalue()


def sdist(metadata: bytes) -> bytes:
    result = io.BytesIO()
    with tarfile.open(fileobj=result, mode="w:gz") as archive:
        for name in (
            "truss_toolkit-0.0.50/PKG-INFO",
            "truss_toolkit-0.0.50/src/truss_toolkit.egg-info/PKG-INFO",
        ):
            info = tarfile.TarInfo(name)
            info.size = len(metadata)
            archive.addfile(info, io.BytesIO(metadata))
    return result.getvalue()


class PublishPypiReleaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.assets = self.root / "assets"
        self.assets.mkdir()
        self.output = self.root / "dist"
        self.whl_name = "truss_toolkit-0.0.50-py3-none-any.whl"
        self.sdist_name = "truss_toolkit-0.0.50.tar.gz"
        metadata = b"Metadata-Version: 2.4\nName: truss-toolkit\nVersion: 0.0.50\nRequires-Dist: jsonschema==4.26.0\n\n"
        self.payloads = {
            self.whl_name: wheel(metadata),
            self.sdist_name: sdist(metadata),
        }
        for name, payload in self.payloads.items():
            (self.assets / name).write_bytes(payload)
        self.sums = "".join(
            f"{hashlib.sha256(data).hexdigest()}  {name}\n"
            for name, data in self.payloads.items()
        ).encode()
        self.pins = json.dumps(
            {
                "tag": "v0.0.50",
                "commit": "a" * 40,
                "version": "0.0.50",
                "distribution": "truss-toolkit",
            }
        ).encode()
        (self.assets / "SHA256SUMS").write_bytes(self.sums)
        (self.assets / "release-pins.json").write_bytes(self.pins)
        self.release = {
            "tag_name": "v0.0.50",
            "draft": False,
            "prerelease": False,
            "created_at": "2026-10-26T00:01:00Z",
            "published_at": "2026-10-26T00:02:00Z",
            "assets": [
                {"name": name, "digest": "sha256:" + hashlib.sha256(data).hexdigest()}
                for name, data in {
                    "SHA256SUMS": self.sums,
                    "release-pins.json": self.pins,
                    **self.payloads,
                }.items()
            ],
        }
        self.ref = {
            "ref": "refs/tags/v0.0.50",
            "object": {"sha": "a" * 40, "type": "commit"},
        }

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_distribution_transition_is_versioned_and_preserves_old_cohort(self) -> None:
        self.assertEqual(publisher.distribution_for_version("0.0.50"), "truss-toolkit")
        self.assertEqual(publisher.wheel_prefix_for_version("0.0.50"), "truss_toolkit-0.0.50-")
        self.assertEqual(publisher.distribution_for_version("0.0.51"), "umf-truss")
        self.assertEqual(publisher.wheel_prefix_for_version("0.0.51"), "umf_truss-0.0.51-")
        self.assertEqual(publisher.distribution_for_version("0.0.52"), "umf-truss")
        self.assertEqual(publisher.wheel_prefix_for_version("0.0.52"), "umf_truss-0.0.52-")
        self.assertEqual(publisher.distribution_for_version("0.1.0"), "umf-truss")
        with self.assertRaisesRegex(publisher.ReleaseError, "version must be numeric"):
            publisher.distribution_for_version("v0.0.51")

    def test_temporal_exact_tag_proof_requires_successful_fixed_job_graph(self):
        release={"id": 12, "tag_name": "v0.0.56", "draft": False, "prerelease": False}
        tag_ref={"ref":"refs/tags/v0.0.56", "object":{"type":"commit","sha":"a"*40}}
        run={"id":77,"run_attempt":2,"path":".github/workflows/release.yml",
             "event":"workflow_dispatch","head_branch":"v0.0.56","head_sha":"a"*40,
             "conclusion":"success","referenced_workflows":[],
             "repository":{"full_name":"DocumentDrivenDX/truss"}}
        required_steps={
            "package":["Check active HF release cohort bindings","Verify reproducible embedded owner delivery assets",
                       "Verify complete source payload in wheel and sdist"],
            "native (ubuntu-24.04)":["Install exact released compiler and verify its checksum",
                "Qualify the installed standalone local carrier and retained refusals",
                "Qualify the installed fresh baseline and refusal controls",
                "Qualify the installed final package with independent HF assertions",
                "Qualify installed managed platform grants and contained refusals",
                "Verify installed embedded owners with every subprocess forbidden",
                "Run the installed public adopter workflow","Run installed original public workload",
                "Run installed current-policy query and activation workflows",
                "Run exact installed compiler cohort and asset-cache unit module"],
            "publish":["Record exact assets and publish"]}
        jobs={"jobs":[{"name":name,"run_id":77,"run_attempt":2,"head_sha":"a"*40,
                        "conclusion":"success","steps":[{"name":step,"conclusion":"success"}
                            for step in required_steps[name]]}
                       for name in ("package","native (ubuntu-24.04)","publish")]}
        proof=publisher._exact_tag_proof(release,tag_ref,None,run,jobs,
            repository="DocumentDrivenDX/truss",source_sha="a"*40,tag="v0.0.56")
        self.assertEqual(proof["jobs"],("native","package","publish"))
        self.assertEqual(proof["nestedReusableWorkflows"],())
        self.assertEqual(set(proof["jobStepEvidence"]),set(required_steps))
        for bad_run,bad_jobs in (
            (None,jobs),(run,None),
            ({**run,"conclusion":"cancelled"},jobs),
            ({**run,"referenced_workflows":[{"path":".github/workflows/reusable.yml"}]},jobs),
            (run,{"jobs":jobs["jobs"][:-1]}),
            (run,{"jobs":[*jobs["jobs"],jobs["jobs"][0]]}),
            (run,{"jobs":[{**job,"conclusion":"skipped"} if job["name"]=="native (ubuntu-24.04)" else job
                            for job in jobs["jobs"]]}),
            (run,{"jobs":[{**job,"run_attempt":1} if job["name"]=="publish" else job
                            for job in jobs["jobs"]]}),
            (run,{"jobs":[{**job,"steps":[]} if job["name"]=="native (ubuntu-24.04)" else job
                            for job in jobs["jobs"]]}),
            (run,{"jobs":[{**job,"steps":[{**step,"conclusion":"skipped"}
                                  if step["name"]=="Run the installed public adopter workflow" else step
                                  for step in job["steps"]]}
                            if job["name"]=="native (ubuntu-24.04)" else job for job in jobs["jobs"]]}),
        ):
            with self.subTest(run=bad_run,jobs=bad_jobs),self.assertRaises(publisher.ReleaseError):
                publisher._exact_tag_proof(release,tag_ref,None,bad_run,bad_jobs,
                    repository="DocumentDrivenDX/truss",source_sha="a"*40,tag="v0.0.56")

    def test_new_distribution_archive_metadata_is_exact(self) -> None:
        wheel_path = self.root / "umf_truss-0.0.51-py3-none-any.whl"
        sdist_path = self.root / "umf_truss-0.0.51.tar.gz"
        metadata = b"Metadata-Version: 2.4\nName: umf-truss\nVersion: 0.0.51\nRequires-Dist: jsonschema==4.26.0\n\n"
        wheel_path.write_bytes(wheel(metadata))
        sdist_path.write_bytes(sdist(metadata))
        publisher.validate_archive(wheel_path, "umf-truss", "0.0.51")
        publisher.validate_archive(sdist_path, "umf-truss", "0.0.51")
        with self.assertRaisesRegex(publisher.ReleaseError, "distribution name differs"):
            publisher.validate_archive(wheel_path, "truss-toolkit", "0.0.51")
        with self.assertRaisesRegex(publisher.ReleaseError, "version differs"):
            publisher.validate_archive(sdist_path, "umf-truss", "0.0.50")

    def test_prepare_refuses_name_that_does_not_match_historical_version(self) -> None:
        with self.assertRaisesRegex(publisher.ReleaseError, "versioned release cohort"):
            self.prepare(distribution="umf-truss", wheel_prefix="umf_truss-0.0.50-")

    def test_renamed_publication_refuses_mutable_or_unconfirmed_release(self) -> None:
        release = {**self.release, "tag_name": "v0.0.51"}
        ref = {"ref": "refs/tags/v0.0.51", "object": self.ref["object"]}
        for value in (None, False):
            with self.subTest(immutable=value), self.assertRaisesRegex(
                publisher.ReleaseError, "renamed release must be immutable"
            ):
                self.prepare(release={**release, "immutable": value}, tag_ref=ref,
                    tag="v0.0.51", distribution="umf-truss", wheel_prefix="umf_truss-0.0.51-")

    def prepare(self, **overrides: object) -> dict[str, object]:
        values: dict[str, object] = {
            "repository": "DocumentDrivenDX/truss",
            "release": self.release,
            "tag_ref": self.ref,
            "tag_object": None,
            "assets_dir": self.assets,
            "output_dir": self.output,
            "tag": "v0.0.50",
            "source_sha": "a" * 40,
            "expected_sums_sha256": hashlib.sha256(self.sums).hexdigest(),
            "distribution": "truss-toolkit",
            "wheel_prefix": "truss_toolkit-0.0.50-",
            "wheel_count": 1,
            "require_sdist": True,
        }
        values.update(overrides)
        return publisher.prepare_release(**values)  # type: ignore[arg-type]

    def test_prepare_binds_public_assets_tag_source_and_package_metadata(self) -> None:
        receipt = self.prepare()
        self.assertEqual(receipt["status"], "verified")
        self.assertEqual(receipt["source_sha"], "a" * 40)
        self.assertEqual(set(receipt["files"]), set(self.payloads))  # type: ignore[arg-type]
        self.assertEqual(
            (self.output / self.whl_name).read_bytes(), self.payloads[self.whl_name]
        )

    def test_prepare_refuses_source_movement_and_github_digest_mismatch(self) -> None:
        with self.assertRaisesRegex(publisher.ReleaseError, "pinned source"):
            self.prepare(source_sha="b" * 40)
        self.output = self.root / "dist2"
        changed = dict(self.release)
        changed["assets"] = list(self.release["assets"])
        changed["assets"][0] = {**changed["assets"][0], "digest": "sha256:" + "0" * 64}
        with self.assertRaisesRegex(publisher.ReleaseError, "GitHub asset digest"):
            self.prepare(release=changed, output_dir=self.output)

    def test_producer_run_must_be_successful_and_from_allowed_release_workflow(
        self,
    ) -> None:
        producer = {
            "id": 123,
            "path": ".github/workflows/release-selected-publish-0.0.50.yml",
            "conclusion": "success",
            "event": "workflow_dispatch",
            "head_sha": "a" * 40,
            "created_at": "2026-10-26T00:00:00Z",
            "updated_at": "2026-10-26T00:10:00Z",
            "repository": {"full_name": "DocumentDrivenDX/truss"},
        }
        receipt = self.prepare(
            producer_run=producer,
            allowed_workflow_prefixes=(".github/workflows/release-selected-publish-",),
        )
        self.assertEqual(receipt["producer_run_id"], 123)
        self.output = self.root / "dist2"
        with self.assertRaisesRegex(publisher.ReleaseError, "not allowed"):
            self.prepare(
                output_dir=self.output,
                producer_run={**producer, "path": ".github/workflows/other.yml"},
                allowed_workflow_prefixes=(
                    ".github/workflows/release-selected-publish-",
                ),
            )
        self.output = self.root / "dist3"
        with self.assertRaisesRegex(publisher.ReleaseError, "did not succeed"):
            self.prepare(
                output_dir=self.output,
                producer_run={**producer, "conclusion": "failure"},
            )
        self.output = self.root / "dist4"
        with self.assertRaisesRegex(publisher.ReleaseError, "repository differs"):
            self.prepare(
                output_dir=self.output,
                producer_run={**producer, "repository": {"full_name": "other/repo"}},
            )
        self.output = self.root / "dist5"
        with self.assertRaisesRegex(publisher.ReleaseError, "source commit differs"):
            self.prepare(
                output_dir=self.output, producer_run={**producer, "head_sha": "b" * 40}
            )
        self.output = self.root / "dist6"
        with self.assertRaisesRegex(
            publisher.ReleaseError, "outside its successful workflow run"
        ):
            self.prepare(
                output_dir=self.output,
                producer_run={**producer, "created_at": "2026-10-26T00:03:00Z"},
                allowed_workflow_prefixes=(
                    ".github/workflows/release-selected-publish-",
                ),
            )

    def test_prepare_refuses_direct_url_metadata_and_wrong_distribution(self) -> None:
        self.output = self.root / "dist3"
        raw = wheel(
            b"Metadata-Version: 2.4\nName: truss-toolkit\nVersion: 0.0.50\nRequires-Dist: umf-core @ https://example.invalid/core.whl\n\n"
        )
        (self.assets / self.whl_name).write_bytes(raw)
        changed = dict(self.release)
        changed["assets"] = [
            {**item, "digest": "sha256:" + hashlib.sha256(raw).hexdigest()}
            if item["name"] == self.whl_name
            else item
            for item in self.release["assets"]
        ]
        sums = "".join(
            f"{hashlib.sha256(raw if name == self.whl_name else data).hexdigest()}  {name}\n"
            for name, data in self.payloads.items()
        ).encode()
        (self.assets / "SHA256SUMS").write_bytes(sums)
        changed["assets"] = [
            {**item, "digest": "sha256:" + hashlib.sha256(sums).hexdigest()}
            if item["name"] == "SHA256SUMS"
            else item
            for item in changed["assets"]
        ]
        with self.assertRaisesRegex(publisher.ReleaseError, "direct URL"):
            self.prepare(
                release=changed,
                output_dir=self.output,
                expected_sums_sha256=hashlib.sha256(sums).hexdigest(),
            )
        self.output = self.root / "dist4"
        with self.assertRaisesRegex(
            publisher.ReleaseError, "distribution name differs"
        ):
            publisher.validate_archive(
                self.assets / self.sdist_name, "other-package", "0.0.50"
            )

    def test_sdist_validates_nested_package_metadata_as_well_as_root(self) -> None:
        bad_metadata = b"Metadata-Version: 2.4\nName: truss-toolkit\nVersion: 0.0.50\nRequires-Dist: umf-core @ file:///tmp/core.whl\n\n"
        path = self.root / self.sdist_name
        path.write_bytes(sdist(bad_metadata))
        with self.assertRaisesRegex(publisher.ReleaseError, "direct URL"):
            publisher.validate_archive(path, "truss-toolkit", "0.0.50")

    def test_registry_check_accepts_only_exact_public_file_bytes(self) -> None:
        payload = self.payloads[self.whl_name]
        digest = hashlib.sha256(payload).hexdigest()
        metadata = json.dumps(
            {
                "info": {"name": "truss-toolkit", "version": "0.0.50"},
                "urls": [
                    {
                        "filename": self.whl_name,
                        "digests": {"sha256": digest},
                        "url": "https://files.pythonhosted.org/packages/truss.whl",
                    }
                ],
            }
        ).encode()

        class Response:
            def __init__(self, body: bytes):
                self.body = body

            def __enter__(self) -> "Response":
                return self

            def __exit__(self, *_args: object) -> None:
                return None

            def read(self) -> bytes:
                return self.body

        with patch.object(
            publisher.urllib.request,
            "urlopen",
            side_effect=[Response(metadata), Response(payload)],
        ):
            self.assertEqual(
                publisher.check_pypi(
                    "truss-toolkit", "0.0.50", {self.whl_name: digest}
                ),
                "matching",
            )

        conflict = json.loads(metadata)
        conflict["urls"][0]["digests"]["sha256"] = "0" * 64
        with patch.object(
            publisher.urllib.request,
            "urlopen",
            return_value=Response(json.dumps(conflict).encode()),
        ):
            with self.assertRaisesRegex(publisher.ReleaseError, "version collision"):
                publisher.check_pypi("truss-toolkit", "0.0.50", {self.whl_name: digest})

    def test_visibility_wait_retries_absence_but_propagates_errors(self) -> None:
        with (
            patch.object(publisher, "check_pypi", side_effect=["absent", "matching"]),
            patch.object(publisher.time, "monotonic", side_effect=[0.0, 0.0, 0.0]),
            patch.object(publisher.time, "sleep") as sleep,
        ):
            self.assertEqual(
                publisher.wait_for_pypi("truss-toolkit", "0.0.50", {}, timeout=300),
                "matching",
            )
            sleep.assert_called_once()
        with patch.object(
            publisher, "check_pypi", side_effect=publisher.ReleaseError("HTTP 401")
        ):
            with self.assertRaisesRegex(publisher.ReleaseError, "HTTP 401"):
                publisher.wait_for_pypi("truss-toolkit", "0.0.50", {}, timeout=300)



class SelectedCoreOwnerCallerTests(unittest.TestCase):
    def contexts(self):
        selected={'sourceCommit':'1'*40,'version':'0.10.10','wheelSha256':'4'*64,
                  'nativeSha256':'5'*64,'qualification':{'authorityCommit':'3'*40,
                  'authorityTree':'a'*40,'registrySha256':'b'*64,'admissionId':'synthetic'}}
        verified={'sourceCommit':'8'*40,'selectedCore':selected,'weftOwnerSource':{
            'sourceCommit':'6'*40,'sourceTree':'7'*40,'canonicalCoreSourceCommit':'9'*40,'cargoLockSha256':'c'*64}}
        return verified

    def test_final_caller_joins_core_and_weft_separate_from_truss_tag(self):
        import component_prerequisite_validators as validators
        verified=self.contexts();core_bundle=object();weft_bundle={'synthetic':'original bytes'}
        with patch.object(validators,'validate_core_selected_owner_proofs',return_value={'core':'summary'}) as core, patch.object(validators,'validate_weft_published_owner_proofs',return_value={'weft':'summary'}) as weft:
            result=publisher._temporal_owner_readiness(verified,weft_bundle,core_bundle)
        self.assertEqual(result,{'core':{'core':'summary'},'weft':{'weft':'summary'}})
        core.assert_called_once_with(core_bundle,selected=verified['selectedCore'])
        weft.assert_called_once_with(weft_bundle,source_commit='6'*40,source_tree='7'*40,canonical_umf='9'*40,cargo_lock_sha256='c'*64)

    def test_final_caller_missing_future_selected_core_proof_refuses(self):
        import component_prerequisite_validators as validators
        verified=self.contexts();verified['selectedCore']['qualification']=None
        with patch.object(validators,'validate_weft_published_owner_proofs') as weft:
            with self.assertRaisesRegex(ValueError,'Missing trusted selected Core owner admission'):
                publisher._temporal_owner_readiness(verified,{'synthetic':'bytes'},None)
        weft.assert_not_called()

    def test_prepublication_owner_summaries_bind_their_separate_contexts(self):
        import copy
        import component_prerequisite_validators as validators
        import release_cohort
        verified=self.contexts();selected=verified['selectedCore'];ws=verified['weftOwnerSource']
        core={'profile':'core-selected-owner-readiness/1','sourceCommit':selected['sourceCommit'],
              'version':selected['version'],'wheelSha256':selected['wheelSha256'],'nativeSha256':selected['nativeSha256'],
              'authorityCommit':selected['qualification']['authorityCommit'],'platforms':validators.CORE_PLATFORMS,
              'sdkChecks':validators.CORE_SDK_CHECKS,'cells':validators.CORE_CELLS}
        weft={'profile':'weft-0457-published-owner-proof/1','sourceCommit':ws['sourceCommit'],
              'sourceTree':ws['sourceTree'],'platforms':('linux-aarch64','linux-x86_64','macos-arm64'),
              'nodeCases':14,'chromiumCases':14,'browserCases':9,'sourceDependencyClosure':'cargo-package-lists-and-local-dependency-bound'}
        proof={'runId':'123','attempt':'1','sourceCommit':'8'*40,'tag':'v0.0.56','jobs':('native','package','publish'),
               'jobStepEvidence':{name:('synthetic existing job step',) for name in ('native (ubuntu-24.04)','package','publish')},
               'nestedReusableWorkflows':(),'releaseId':'456','ownerReadiness':{'core':core,'weft':weft}}
        component={'coreC1':dict.fromkeys(validators.REQUIRED,{'synthetic':'validated'}),
                   'weftSDK42':validators.WEFT_ORIGINAL_CHECK_CALLS,
                   'stagePrerequisites':{'historyDisposition':{'synthetic':'historical'},'lifecycle2':{'synthetic':'validated'},'weftOwnerSource':ws}}
        records={name:{'synthetic':'existing validated record'} for name in release_cohort._STAGE_RECORDS['prepublication']}
        records.update(exactTagProofs=proof,selectedCore=selected)
        result=release_cohort.require_stage_admission('prepublication',component=component,records=records)
        self.assertEqual(result['stage'],'prepublication')
        for owner,key,value in [('core','sourceCommit','8'*40),('core','version','0.10.8'),('core','wheelSha256','e'*64),('weft','sourceCommit','1'*40)]:
            bad=copy.deepcopy(records);bad['exactTagProofs']['ownerReadiness'][owner][key]=value
            with self.subTest(owner=owner,key=key),self.assertRaises(ValueError):
                release_cohort.require_stage_admission('prepublication',component=component,records=bad)


if __name__ == "__main__":
    unittest.main()
