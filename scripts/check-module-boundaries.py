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
    '__init__': {'truss.local_runtime'},
    '_acceptance_json': {'json'},
    '_operation_admission': {'dataclasses', 'inspect', 'threading'},
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
