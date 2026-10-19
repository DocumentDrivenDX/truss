# SPDX-License-Identifier: MIT OR Apache-2.0
"""Package original installation inputs; incomplete sources grant no authority.

This is the first release-definition input to the integrated installer workstream,
not a BootstrapGenerationResult or an executable statement inventory.
"""
from hashlib import sha256
import io
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / 'packages/python/src/truss/_installation'
SOURCES = (
    ('model', 'docs/helix/02-design/models/truss-layout-source-epoch-0.16.proposal.umf.json'),
    ('owner_export', 'docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql'),
    ('owner_generation_evidence', 'docs/helix/04-build/evidence/design-audit/source-epoch-layout-source.json'),
    *tuple(('issued_admission', 'packages/postgresql/native/issued-operation-admission/' + name + '.sql')
           for name in ('operation-admission', 'operation-asserted-origin-admission',
                        'operation-epoch-context-admission', 'operation-configuration-context-admission')),
    ('pending_writer','packages/postgresql/native/existing-string-writer/pending-effects.sql'),
    ('operation_commit_barrier','packages/postgresql/native/operation-commit-barrier.sql'),
    *tuple(('row_image', 'packages/postgresql/native/row-image/' + name + '.sql')
           for name in ('codec', 'prestate', 'snapshot-prestate', 'state-owner', 'dependent-owner', 'string-candidate', 'existing-string-scope')),
)
REQUIRED_BODIES = (
    'row_touch_observe', 'row_touch_commit_check', 'edge_limit_observe',
    'edge_limit_catalog_observe', 'feed_current_union_check',
    'edge_limit_verify_current_scope', 'feed_union_validate_current_scope',
)


def build():
    originals = [(role, path, (ROOT / path).read_bytes()) for role, path in SOURCES]
    # Correspondence uses the retained original owner output evidence, not new
    # serialization of the UMF document or a newly inferred generator identity.
    evidence = json.loads(originals[2][2])
    for position, key in ((0, 'modelSha256'), (1, 'ddlSha256')):
        if sha256(originals[position][2]).hexdigest() != evidence[key]:
            raise ValueError('Original owner generation correspondence changed')
    entries = [dict(role=role, path=path, byteLength=len(original),
                    sha256=sha256(original).hexdigest()) for role, path, original in originals]
    manifest = dict(
        interfaceVersion='truss-installation-source-definition/0.1.0',
        scope='original_development_sources_only', qualified=False,
        executable=False, resources=entries,
        requiredNativeBodies=list(REQUIRED_BODIES),
        unresolved=['complete_native_bodies', 'complete_resource_and_dependency_inventory',
                    'original_installer_attempt_and_authority', 'full_operation_context_producer',
                    'security_and_initialization_composition', 'ordered_statement_inventory',
                    'target_native_correspondence_and_settlement'],
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for _, path, original in originals:
            info = zipfile.ZipInfo(path, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, original)
    payload = buffer.getvalue()
    manifest['archive'] = dict(path='sources.zip', byteLength=len(payload), sha256=sha256(payload).hexdigest())
    DESTINATION.mkdir(parents=True, exist_ok=True)
    (DESTINATION / 'sources.zip').write_bytes(payload)
    (DESTINATION / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(dict(resources=len(entries), archiveBytes=len(payload), qualified=False)))


if __name__ == '__main__':
    build()
