#!/usr/bin/env python3
"""Enforce the current Python source map; does not execute inspected source.

TypeScript, native SQL, reflection and runtime object visibility require separate
checks/review. A pass is explicitly Python-only, not architecture qualification.
"""
import argparse
import ast
import json
from pathlib import Path
import sys

# Imports are owned by the source module, including inside functions. New modules
# require a reviewed map entry; there is no directory-wide exception or baseline.
ALLOWED = {
    '_startup_custody': {'dataclasses','threading','importlib.metadata','io','socket','pg8000','truss._native_driver_profile','truss._native_deadline'},
    '_native_bootstrap': {'dataclasses', 'threading', 'importlib.metadata', 'io', 'socket', 'pg8000', 'truss._native_pg8000', 'truss._host_control_custody', 'truss._native_result_custody', 'truss._native_deadline', 'truss._startup_custody','truss._native_driver_profile'},
    '_adoption_cancellation': {'threading'},
    'contracts': {'dataclasses', 'enum', 'types', 'typing'},
    'groups': {'dataclasses', 'typing', 'truss.contracts', 'truss.execution'},
    'imports': {'dataclasses', 'typing', 'truss.contracts', 'truss.execution'},
    '_installed_admission_inventory': {'dataclasses', 'hashlib', 'json', 'importlib.resources', 'typing'},
    '_host_call_recovery': {'dataclasses', 'threading', 'truss.execution'},
    '_host_control_custody': {'truss._native_ingress_deadline', 'truss._native_outbound', 'dataclasses', 'threading', 'pg8000.core', 'truss._native_pg8000', 'truss._native_transactions', 'truss._native_result_custody', 'truss._native_driver_profile', 'truss._host_execution', 'truss.execution'},
    '_host_session': {'truss._native_deadline', 'truss._host_call_recovery', 'dataclasses', 'threading', 'truss._host_execution', 'truss._native_transactions', 'truss._native_arbitration', 'truss._native_pg8000', 'truss._host_control_custody', 'truss.execution'},
    '_host_contracts': {'dataclasses', 'truss.execution'},
    '_host_execution': {'truss._adoption_cancellation', 'truss._host_call_recovery', 'dataclasses', 'threading', 'truss._host_contracts', 'truss._native_adoption', 'truss._native_transactions', 'truss.execution', 'uuid'},
    '_native_adoption': {'contextlib', 'dataclasses', 'truss._host_contracts', 'truss._native_pg8000', 'truss.execution', 'uuid'},
    '_native_arbitration': {'dataclasses', 'threading', 'truss._host_execution', 'truss._native_adoption', 'truss._native_pg8000', 'truss._native_transactions', 'truss._operation_arbitration', 'uuid'},
    '_native_driver_profile': {'pg8000.converters', 'pg8000.core', 'pg8000.native'},
    '_native_outbound': {'truss._startup_custody','truss._native_driver_profile', 'dataclasses', 'truss._native_pg8000', 'truss._resource_account'},
    '_native_ingress_deadline': {'io', 'socket', 'truss._native_pg8000', 'truss._native_deadline'},
    '_native_deadline': {'time'},
    '_native_cancellation': {'socket', 'struct', 'threading', 'time'},
    '_native_operation': {'truss._native_ingress_deadline', 'truss._native_deadline', 'truss._native_cancellation', 'truss._host_control_custody', 'dataclasses', 'pg8000.converters', 'pg8000.core', 'pg8000.native', 'threading', 'truss._native_arbitration', 'truss._native_pg8000', 'truss._native_result_custody', 'truss._native_driver_profile', 'truss._native_transactions', 'truss._operation_arbitration', 'truss.execution', 'uuid'},
    '_native_pg8000': {'truss._startup_custody','truss._native_driver_profile', 'dataclasses', 'importlib.metadata', 'pg8000.native', 'threading'},
    '_native_result_custody': {'truss._native_outbound', 'truss._native_ingress_deadline', 'io', 'dataclasses', 'pg8000.converters', 're', 'struct', 'truss._accounted_receive', 'truss._native_pg8000', 'truss._resource_account'},
    '_native_transactions': {'dataclasses', 're', 'truss._native_adoption', 'truss._native_pg8000', 'truss.execution', 'uuid'},
    '_operation_arbitration': {'dataclasses', 'threading', 'truss._host_execution', 'uuid'},
    'execution': {'dataclasses', 'typing'},
    '_installation_archive': {'dataclasses', 'hashlib'},
    '__init__': {'truss.local_runtime', 'truss.execution'},
    '_acceptance_json': {'json'},
    '_security_association_binding': {'dataclasses', 'hashlib', 'json'},
    '_directory_resources': {'os', 'stat', 'threading', 'truss._installation_resources'},
    '_installation_resources': {'dataclasses', 'hashlib', 'json', 'truss._resource_account'},
    '_operation_admission': {'dataclasses', 'inspect', 'threading'},
    '_operation_registry': set(),
    '_row_image': {'dataclasses', 'struct'},
    '_row_image_capture': {'dataclasses', 'truss._row_image', 'truss._row_event_attribution'},
    '_row_image_scalar_shape': {'truss._row_image'},
    '_row_image_tree': {'truss._row_image_capture', 'truss._row_event_attribution'},
    '_row_event_attribution': {'dataclasses', 'struct', 'truss._row_image'},
    '_row_operation_custody': {'base64', 'dataclasses', 'hashlib', 're', 'truss._acceptance_json'},
    '_row_operation_address': {'dataclasses', 'json', 'truss._acceptance_json', 'truss._row_operation_custody'},
    '_row_group_custody': {'dataclasses', 'truss._acceptance_json', 'truss._row_operation_custody', 'truss._row_operation_address'},
    '_row_operation_context': {'dataclasses', 'truss._acceptance_json', 'truss._row_operation_address', 'truss._row_operation_custody', 'truss._row_group_custody'},
    '_row_touch_registry': {'dataclasses', 'truss._operation_registry', 'truss._row_operation_address', 'truss._row_operation_custody'},
    '_row_registry_correspondence': {'dataclasses', 'truss._row_touch_registry', 'truss._operation_registry', 'truss._row_operation_address', 'truss._row_operation_context', 'truss._row_group_custody', 'truss._row_operation_custody'},
    '_accounted_receive': {'struct', 'threading', 'truss._resource_account'},
    '_operation_ordinal': {'dataclasses', 'threading'},
    '_query_execution': {'dataclasses', 'inspect', 'threading', 'types', 'weakref', 'truss.weft'},
    '_resource_account': {'dataclasses', 'threading'},
    '_receipt_position': {'base64', 'binascii', 'dataclasses', 'json', 're', 'truss._acceptance_json'},
    'cli': {'argparse', 'json', 'pathlib', 'signal', 'threading', 'truss'},
    'local_runtime': {'dataclasses', 'importlib.metadata', 'importlib.resources', 'pathlib',
                      'subprocess', 'threading', 'pgserver', 'fasteners'},
    'migration_planning': {'dataclasses', 're', 'typing', 'truss._acceptance_json'},
    'numeric': {'dataclasses', 'decimal'},
    'timestamp': {'dataclasses', 'datetime', 're', 'truss.numeric'},
    'weft': {'dataclasses', 'decimal', 'hashlib', 'inspect', 'json', 'threading', 'types', 'typing'},
}


def inspect_sources(source: Path):
    errors, edges = [], []
    modules = {}
    for path in sorted(source.rglob('*.py')):
        relative = path.relative_to(source)
        name = '.'.join(relative.with_suffix('').parts)
        modules[name] = path
    if not modules:
        return ['Python source directory has no modules'], []
    for missing in sorted(set(ALLOWED) - set(modules)):
        errors.append(f'Mapped Python module missing: {missing}')
    for name, path in modules.items():
        if name not in ALLOWED:
            errors.append(f'{path.name}: unmapped module {name}')
            continue
        try:
            tree = ast.parse(path.read_text(), filename=str(path))
        except (SyntaxError, UnicodeError) as error:
            errors.append(f'{path.name}: parse failure {error}')
            continue
        # Resolve aliases for direct import mechanisms; computed/reflection
        # indirection remains a semantic review obligation, not a static proof.
        dynamic_names = {'__import__', 'eval', 'exec'}
        module_aliases = {'importlib'}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == 'importlib':
                        module_aliases.add(alias.asname or alias.name)
            if isinstance(node, ast.ImportFrom) and node.module == 'importlib':
                for alias in node.names:
                    if alias.name == 'import_module':
                        dynamic_names.add(alias.asname or alias.name)
        for node in ast.walk(tree):
            targets = []
            if isinstance(node, ast.Import):
                targets = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    if node.level != 1:
                        errors.append(f'{path.name}:{node.lineno}: import escapes package')
                        continue
                    targets = ['truss.' + node.module] if node.module else [
                        'truss.' + alias.name for alias in node.names]
                else:
                    targets = ([('truss.' + alias.name) if alias.name in modules or alias.name.startswith('_')
                                else 'truss' for alias in node.names]
                               if node.module == 'truss' else [node.module or ''])
                if any(alias.name == '*' for alias in node.names):
                    errors.append(f'{path.name}:{node.lineno}: wildcard import')
            elif isinstance(node, ast.Call):
                function = node.func
                if (isinstance(function, ast.Name) and function.id in dynamic_names) or (
                    isinstance(function, ast.Attribute) and function.attr == 'import_module'
                    and isinstance(function.value, ast.Name) and function.value.id in module_aliases):
                    errors.append(f'{path.name}:{node.lineno}: dynamic source/import execution requires review')
            for target in targets:
                edges.append({'source': name, 'target': target, 'line': node.lineno})
                if target not in ALLOWED[name]:
                    errors.append(f'{path.name}:{node.lineno}: forbidden import {target}')
                if target.startswith('truss.') and target[6:] not in modules:
                    errors.append(f'{path.name}:{node.lineno}: missing local target {target}')
    graph = {name: set() for name in modules}
    for edge in edges:
        target = edge['target']
        local = '__init__' if target == 'truss' else target[6:] if target.startswith('truss.') else None
        if local in graph:
            graph[edge['source']].add(local)
    visited, active = set(), []
    def visit(name):
        if name in active:
            errors.append('Python import cycle: ' + ' -> '.join(active[active.index(name):] + [name]))
            return
        if name in visited:
            return
        active.append(name)
        for target in sorted(graph[name]):
            visit(target)
        active.pop()
        visited.add(name)
    for name in sorted(graph):
        visit(name)
    return errors, edges


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path(__file__).resolve().parents[1] / 'packages/python/src/truss')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    errors, edges = inspect_sources(args.source)
    result = {'scope': 'python-only', 'passed': not errors, 'edgeCount': len(edges),
              'errors': errors, 'edges': edges,
              'unqualified': ['TypeScript imports', 'native SQL dependencies',
                              'reflection/indirect dynamic execution', 'runtime private-object visibility']}
    if args.json:
        print(json.dumps(result, sort_keys=True))
    elif errors:
        print('\n'.join(errors), file=sys.stderr)
    else:
        print(f'Python module boundaries passed ({len(edges)} imports); TypeScript/native gates remain open')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
