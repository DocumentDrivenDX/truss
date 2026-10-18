#!/usr/bin/env python3
"""Assemble owner sources for the native72 owned graph runtime."""
from pathlib import Path
import argparse
import hashlib
import json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    arguments = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    target = root / 'packages/python/src/truss/_catalog_runtime'
    owner = root / 'packages/postgresql/owned-groups'
    manifest = json.loads((target / 'manifest.json').read_bytes())
    if manifest['releaseId'] != 'truss-catalog-runtime/0.72-candidate':
        raise ValueError('Select the original native72 runtime manifest')
    parts = [(owner / 'operation-storage.generated.sql').read_text() + ';\n', '''CREATE TRIGGER runtime_owned_operation_immutable AFTER UPDATE ON truss.runtime_owned_operation FOR EACH ROW
WHEN (OLD.result IS NOT NULL OR NEW.result IS NULL OR
 ROW(OLD.attempt_id,OLD.operation_index,OLD.writer_xid,OLD.plan) IS DISTINCT FROM
 ROW(NEW.attempt_id,NEW.operation_index,NEW.writer_xid,NEW.plan)) EXECUTE FUNCTION truss.catalog_immutable();
CREATE TRIGGER runtime_owned_operation_no_delete BEFORE DELETE ON truss.runtime_owned_operation FOR EACH ROW EXECUTE FUNCTION truss.catalog_immutable();
CREATE TRIGGER runtime_owned_operation_no_truncate BEFORE TRUNCATE ON truss.runtime_owned_operation FOR EACH STATEMENT EXECUTE FUNCTION truss.catalog_immutable();
REVOKE ALL ON TABLE truss.runtime_owned_operation FROM PUBLIC;
''']
    parts.extend((owner / name).read_text() for name in (
        'values.sql', 'forest.sql', 'scope.sql', 'delete.sql', 'execute.sql', 'bulk-create.sql', 'bulk-edge.sql', 'bulk-update.sql', 'finalize.sql'))
    parts.append((owner / 'history.sql').read_text().split('CREATE OR REPLACE FUNCTION', 1)[0])
    assembled = ('\n'.join(parts).rstrip() + '\n').encode('utf8')
    if arguments.check:
        if (target / 'owned.sql').read_bytes() != assembled:
            raise ValueError('Regenerate the original owned runtime sources')
        for name, digest in manifest['files'].items():
            if hashlib.sha256((target / name).read_bytes()).hexdigest() != digest:
                raise ValueError('Runtime source hash differs: ' + name)
    else:
        (target / 'owned.sql').write_bytes(assembled)
        for name in manifest['files']:
            manifest['files'][name] = hashlib.sha256((target / name).read_bytes()).hexdigest()
        (target / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
