# SPDX-License-Identifier: MIT OR Apache-2.0
"""Exact packaged forward recipes; no historical runtime imports or SQL inference."""
from hashlib import sha256
from importlib.resources import files
import json
from .catalog_preparation import _configuration


def load_recipe():
    root=files('truss').joinpath('_migrations')
    original=root.joinpath('manifest.json').read_bytes()
    manifest=json.loads(original)
    if manifest['interfaceVersion']!='truss-runtime-migration/0.1':raise ValueError('Migration interface required')
    artifacts={}
    for name,digest in manifest['files'].items():
        if '/' in name or '..' in name:raise ValueError('Packaged artifact name required')
        raw=root.joinpath(name).read_bytes()
        if sha256(raw).hexdigest()!=digest:raise ValueError('Migration artifact integrity failure: '+name)
        artifacts[name]=raw
    current=files('truss').joinpath('_catalog_runtime','manifest.json').read_bytes()
    if sha256(current).hexdigest()!=manifest['target']:raise ValueError('Migration target cohort changed')
    target=json.loads(current)
    for name,digest in target['files'].items():
        if sha256(files('truss').joinpath('_catalog_runtime',name).read_bytes()).hexdigest()!=digest:
            raise ValueError('Target runtime artifact changed: '+name)
    if _configuration(target)!=json.loads(artifacts[manifest['target']+'.json'])['configuration']:
        raise ValueError('Current metadata-owner configuration requires a new qualified target')
    selected=manifest['receiptModel']
    model=artifacts[selected['artifact']]
    evidence=json.loads(artifacts[selected['evidence']])
    if (json.loads(model)['umf']!='0.10.0' or evidence['modelSha256']!=sha256(model).hexdigest()
            or evidence['sourceSha256']!=target['files'][selected['sourceFile']] or evidence['passed'] is not True):
        raise ValueError('Migration storage model/deployment correspondence failed')
    equivalence=json.loads(artifacts[manifest['definitionEquivalence']])
    if equivalence['passed'] is not True or equivalence['backend']!='@libpg-query/parser@17.6.10':
        raise ValueError('Qualified native deparse equivalence required')
    for endpoint in [manifest['target'],*manifest['sources']]:
        if json.loads(artifacts[endpoint+'.json'])['definitionAlternatives']!=equivalence['rules']:
            raise ValueError('Unqualified native definition alternative')
    for edge in manifest['edges']:
        candidate=json.loads(artifacts[edge['artifact']])
        if candidate['source']!=edge['source'] or candidate['target']!=edge['target']:
            raise ValueError('Declared migration edge changed')
        for field in ('steps','ownership','moduleGrants'):
            if type(candidate[field]) is not list or any(type(s) is not str or not s for s in candidate[field]):
                raise ValueError('Exact ordered migration statements required')
        for endpoint in (edge['source'],edge['target']):
            if json.loads(artifacts[endpoint+'.json'])['sha256']!=endpoint:
                raise ValueError('Exact endpoint inventory required')
    for source in manifest['sources']:plan_route(manifest,source)
    return manifest,artifacts,sha256(original).hexdigest()


def plan_route(manifest,source):
    """Select a declared forward path; intermediate application runtimes never run."""
    edges=manifest.get('edges',[])
    if len(edges)>4096:raise ValueError('Migration graph exceeds bounded profile')
    graph={}
    for edge in edges:
        if edge.get('direction')!='forward' or edge['source']==edge['target']:
            raise ValueError('Explicit forward edge required')
        graph.setdefault(edge['source'],[]).append(edge)
    # Validate all routes, even unselected ones, so a hidden cycle cannot ship.
    visiting=set();visited=set()
    def visit(node):
        if node in visiting:raise ValueError('Migration cycle')
        if node in visited:return
        visiting.add(node)
        for edge in graph.get(node,[]):visit(edge['target'])
        visiting.remove(node);visited.add(node)
    for node in graph:visit(node)
    queue=[(source,[])];seen=set()
    while queue:
        node,path=queue.pop(0)
        if node==manifest['target']:return path
        if node in seen:continue
        seen.add(node)
        queue.extend((edge['target'],path+[edge]) for edge in graph.get(node,[]))
    raise ValueError('No declared forward path to latest')
