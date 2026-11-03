#!/usr/bin/env python3
"""Verify the local .55 qualification bundle without network or native effects."""
import argparse
import hashlib
import json
import pathlib
import tarfile
import zipfile


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: pathlib.Path):
    return json.loads(path.read_bytes())


def verify_sums(directory: pathlib.Path, sums_path: pathlib.Path):
    for line in sums_path.read_text().splitlines():
        digest, rel = line.split("  ", 1)
        path = directory / rel
        if not path.is_file() or sha(path.read_bytes()) != digest:
            raise ValueError(f"checksum mismatch: {rel}")


def zip_files(path: pathlib.Path):
    with zipfile.ZipFile(path) as archive:
        return {name: archive.read(name) for name in archive.namelist() if not name.endswith("/")}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=pathlib.Path, required=True)
    parser.add_argument("--bundle-root", type=pathlib.Path, required=True)
    args = parser.parse_args()
    source = args.source_root.resolve()
    bundle = args.bundle_root.resolve()
    verify_sums(bundle, bundle / "SHA256SUMS")
    prior = bundle / "prior-0.0.54"
    verify_sums(prior, prior / "SHA256SUMS")

    binding = read_json(bundle / "component-reuse-binding.json")
    prior_pins = read_json(prior / "release-pins.json")
    wheel54 = prior / "umf_truss-0.0.54-py3-none-any.whl"
    wheel55 = bundle / "assets/umf_truss-0.0.55-py3-none-any.whl"
    if sha(wheel54.read_bytes()) != binding["priorRelease"]["wheelSha256"]:
        raise ValueError("previous wheel pin mismatch")
    if sha(wheel55.read_bytes()) != binding["candidate"]["wheelSha256"]:
        raise ValueError("candidate wheel pin mismatch")
    if prior_pins["commit"] != binding["priorRelease"]["sourceCommit"]:
        raise ValueError("previous receipt/source binding mismatch")
    if prior_pins["version"] != "0.0.54":
        raise ValueError("previous pin version mismatch")

    old, new = zip_files(wheel54), zip_files(wheel55)
    runtime_diffs = [name for name in sorted(set(old) & set(new))
                     if name.startswith("truss/") and old[name] != new[name]]
    expected = ["truss/catalog_runtime.py", "truss/psycopg_host.py"]
    if runtime_diffs != expected:
        raise ValueError(f"unexpected runtime package delta: {runtime_diffs}")
    for name, content in new.items():
        if name.startswith("truss/"):
            source_path = source / "packages/python/src" / name
            if not source_path.is_file() or source_path.read_bytes() != content:
                raise ValueError(f"candidate wheel/source mismatch: {name}")

    sdist = bundle / "assets/umf_truss-0.0.55.tar.gz"
    with tarfile.open(sdist, "r:gz") as archive:
        for member in archive.getmembers():
            prefix = "umf_truss-0.0.55/src/truss/"
            if member.isfile() and member.name.startswith(prefix):
                rel = member.name.removeprefix(prefix)
                source_path = source / "packages/python/src/truss" / rel
                if not source_path.is_file() or archive.extractfile(member).read() != source_path.read_bytes():
                    raise ValueError(f"candidate sdist/source mismatch: {rel}")

    for rel in ("packages/python/src/truss/_catalog_runtime/manifest.json",
                "packages/python/src/truss/_migrations/manifest.json"):
        current_sha = sha((source / rel).read_bytes())
        if current_sha != binding["priorRelease"]["nativeRuntimeManifestSha256"] \
                and rel.endswith("_catalog_runtime/manifest.json"):
            raise ValueError("native runtime manifest changed")
        if current_sha != binding["priorRelease"]["migrationManifestSha256"] \
                and rel.endswith("_migrations/manifest.json"):
            raise ValueError("migration manifest changed")

    old_hf = zip_files(prior / "truss-hf-conformance-0.0.54.zip")
    new_hf = zip_files(bundle / "assets/truss-hf-conformance-0.0.55.zip")
    hf_diffs = [name for name in sorted(set(old_hf) | set(new_hf))
                if old_hf.get(name) != new_hf.get(name)]
    expected_hf_diffs = ["README.md", "conformance-manifest.json",
                         "docs/helix/03-test/fixtures/hohfeld-followup-0.1.json"]
    if hf_diffs != expected_hf_diffs:
        raise ValueError(f"unexpected HF archive delta: {hf_diffs}")
    fixture = source / "docs/helix/03-test/fixtures/hohfeld-followup-0.1.json"
    archived_fixture = new_hf[expected_hf_diffs[-1]]
    if fixture.read_bytes() != archived_fixture:
        raise ValueError("HF archive fixture does not match current source")
    corpus = json.loads(archived_fixture)
    if corpus.get("toolkitVersion") != "0.0.55" or len(corpus.get("cases", [])) != 62:
        raise ValueError("HF archive is not aligned to the current .55 corpus metadata")

    grants = read_json(prior / "managed-grants-qualification.json")
    closure = read_json(bundle / "qualification/managed-grants-input-basis-current-hashes.json")
    if len(closure) != len(grants["inputBasis"]):
        raise ValueError("managed-grants input closure count mismatch")
    for rel, old_sha in grants["inputBasis"].items():
        current_sha = sha((source / rel).read_bytes())
        if current_sha != old_sha or closure.get(rel) != current_sha:
            raise ValueError(f"managed-grants closure changed: {rel}")

    carrier = read_json(bundle / "qualification/standalone-carrier-qualification-macos.json")
    timeout = read_json(bundle / "qualification/install-timeout-qualification-macos.json")
    if carrier["wheelSha256"] != sha(wheel55.read_bytes()) or not carrier["passed"]:
        raise ValueError("current carrier receipt mismatch")
    if timeout["wheelSha256"] != sha(wheel55.read_bytes()) or timeout["status"] != "passed":
        raise ValueError("current timeout receipt mismatch")
    if timeout["target"] != {"os": "macOS", "architecture": "arm64", "python": "3.12.14"}:
        raise ValueError("current timeout platform mismatch")
    closeout = read_json(bundle / "qualification/ashlar-r61-qualification-closeout.json")
    if closeout["artifacts"]["truss_wheel_sha256"] != sha(wheel55.read_bytes()):
        raise ValueError("Ashlar qualification did not use this Truss wheel")
    if closeout["qualification_scope"]["authority"] != "local development only; fresh baseline, no historical migration/recovery or production authority":
        raise ValueError("Ashlar authority scope mismatch")

    print(json.dumps({"status": "verified_local_qualification_bundle",
                      "publication": "not_performed",
                      "runtime_package_diffs": runtime_diffs,
                      "hf_archive_changed_members": hf_diffs,
                      "managed_grants_input_paths_compared": len(closure),
                      "current_target": timeout["target"],
                      "candidate_wheel_sha256": sha(wheel55.read_bytes()),
                      "prior_release_commit": prior_pins["commit"]}, indent=2))


if __name__ == "__main__":
    main()
