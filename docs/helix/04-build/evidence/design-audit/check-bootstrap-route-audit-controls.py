"""Isolated corruption controls for source/route inventory audit; no native proof."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile

repo = Path(__file__).resolve().parents[5]
audit = repo / 'docs/helix/04-build/evidence/design-audit'
bindings = repo / 'docs/helix/02-design/contracts/bindings'
results = []
with tempfile.TemporaryDirectory(prefix='truss-route-audit-controls-') as directory:
    isolated = Path(directory)
    for source_dir in [audit, bindings]:
        target_dir = isolated / source_dir.relative_to(repo)
        target_dir.mkdir(parents=True, exist_ok=True)
        for source in source_dir.iterdir():
            if not source.is_file():
                continue
            target = target_dir / source.name
            if source.name == 'check-bootstrap-route-inventory.py' or '-route-v0.1.proposal.json' in source.name:
                shutil.copyfile(source, target)
            else:
                target.symlink_to(source)
    local_audit = isolated / audit.relative_to(repo)
    local_bindings = isolated / bindings.relative_to(repo)
    checker = local_audit / 'check-bootstrap-route-inventory.py'
    # Output must never follow a symlink to the authoritative receipt.
    (local_audit / 'bootstrap-route-inventory.json').unlink()
    field_output = local_audit / 'bootstrap-field-handoffs.json'
    if field_output.exists() or field_output.is_symlink():
        field_output.unlink()
    route = local_bindings / 'bootstrap-cast-route-v0.1.proposal.json'
    original = route.read_bytes()
    def run(name, expected_pass):
        result = subprocess.run([sys.executable, str(checker)], cwd=isolated, capture_output=True, text=True)
        passed = result.returncode == 0
        if passed != expected_pass:
            raise ValueError(name + ': unexpected audit outcome')
        results.append({'case': name, 'expectedPass': expected_pass, 'observedPass': passed})
    run('unchanged isolated inventory', True)
    route.unlink()
    run('missing original route', False)
    route.write_bytes(original)
    item = json.loads(original)
    item['orderedColumns'] = item['orderedColumns'][::-1]
    route.write_text(json.dumps(item))
    run('wrong original positional descriptor', False)
    route.write_bytes(original)
    other = local_bindings / 'bootstrap-collation-route-v0.1.proposal.json'
    other_original = other.read_bytes()
    item = json.loads(original)
    item['routeIdentity'] = json.loads(other_original)['routeIdentity']
    other.write_text(json.dumps(item))
    run('duplicate original query route', False)
    other.write_bytes(other_original)
    extra = local_bindings / 'bootstrap-unreviewed-route-v0.1.proposal.json' 
    extra.write_bytes(original)
    run('unreviewed extra route', False)
    extra.unlink()
    item = json.loads(original)
    item['artifacts'][0]['sha256'] = '0' * 64
    route.write_text(json.dumps(item))
    run('stale original source pin', False)
    route.write_bytes(original)
    receipt = local_audit / 'bootstrap-cast-source.json'
    receipt.unlink()
    receipt.write_text('{}')
    run('changed aggregate receipt', False)
    receipt.unlink()
    receipt.symlink_to(audit / receipt.name)
    specification = local_bindings / 'bootstrap-sequence-definition-v0.1.proposal.json'
    specification.unlink()
    original_specification = (bindings / specification.name).read_bytes()
    specification.write_bytes(original_specification + b' ')
    run('stale field specification pin', False)
    altered = json.loads(original_specification)
    altered['fields'] = altered['fields'][:-1]
    specification.write_text(json.dumps(altered))
    saved_routes = {}
    for name in ['sequence', 'external-sequence']:
        target = local_bindings / ('bootstrap-' + name + '-route-v0.1.proposal.json')
        saved_routes[name] = target.read_bytes()
        item = json.loads(saved_routes[name])
        item['dependencyExtraction']['definitionSpecification']['sha256'] = hashlib.sha256(specification.read_bytes()).hexdigest()
        target.write_text(json.dumps(item))
    run('rehashed specification with missing classified field', False)
    def rehash_profile(value):
        specification.write_text(json.dumps(value))
        for name, raw in saved_routes.items():
            target = local_bindings / ('bootstrap-' + name + '-route-v0.1.proposal.json')
            item = json.loads(raw)
            item['dependencyExtraction']['definitionSpecification']['sha256'] = hashlib.sha256(specification.read_bytes()).hexdigest()
            target.write_text(json.dumps(item))
    altered['requiredRawFieldInventory'] = altered['requiredRawFieldInventory'][:-1]
    rehash_profile(altered)
    run('coordinated missing field and inventory still disagrees with route', False)
    altered = json.loads(original_specification)
    altered['fields'][0]['domain'] = ' '
    rehash_profile(altered)
    run('rehashed empty field domain', False)
    altered = json.loads(original_specification)
    altered['fields'][0]['meaning'] = ''
    rehash_profile(altered)
    run('rehashed empty field meaning', False)
    altered = json.loads(original_specification)
    altered['interfaceVersion'] = 'truss-bootstrap-sequence-definition-profile/99.0.0'
    rehash_profile(altered)
    run('rehashed unsupported definition version', False)
    altered = json.loads(original_specification)
    altered['unknownFields'] = ''
    rehash_profile(altered)
    run('rehashed missing unknown-field policy', False)
    for name, raw in saved_routes.items():
        (local_bindings / ('bootstrap-' + name + '-route-v0.1.proposal.json')).write_bytes(raw)
    specification.write_bytes(original_specification)
    inline_route = local_bindings / 'bootstrap-description-route-v0.1.proposal.json'
    inline_original = inline_route.read_bytes()
    item = json.loads(inline_original)
    del item['dependencyExtraction']['fieldClassification']
    inline_route.write_text(json.dumps(item))
    run('removed entire required inline classification', False)
    item = json.loads(inline_original)
    del item['dependencyExtraction']['fieldClassification']['description']
    inline_route.write_text(json.dumps(item))
    run('missing inline native field', False)
    item = json.loads(inline_original)
    item['dependencyExtraction']['fieldClassification']['description'] = ' '
    inline_route.write_text(json.dumps(item))
    run('blank inline meaning', False)
    item = json.loads(inline_original)
    item['dependencyExtraction']['canonicalProcedure'] = ''
    inline_route.write_text(json.dumps(item))
    run('blank inline canonical procedure', False)
    inline_route.write_bytes(inline_original)
    run('restored isolated inventory', True)
output = {'scope': 'Nineteen isolated inventory/descriptor/pin/field-admission corruption controls only; no semantic route or native PostgreSQL qualification', 'status': 'pass', 'cases': results, 'checkerSha256': hashlib.sha256((audit / 'check-bootstrap-route-inventory.py').read_bytes()).hexdigest(), 'controlsSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
Path(__file__).with_name('bootstrap-route-audit-controls.json').write_text(json.dumps(output, indent=2) + '\n')
print(json.dumps({'cases': len(results), 'status': 'pass'}))
