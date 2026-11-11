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
    if 'baseline' in manifest:
        baseline=manifest['baseline']
        if (baseline.get('identity')!='truss-fresh-install-baseline/2026-11-02'
                or baseline.get('historicalMigrationsSupported') is not False
                or baseline.get('historicalReceiptRecoverySupported') is not False
                or manifest['sources'] or manifest['edges'] or manifest['sourceWheels']):
            raise ValueError('Explicit fresh baseline without historical migration authority required')
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
    for endpoint in [manifest['target'],*manifest['sources']]:
        profile=json.loads(artifacts[endpoint+'.json'])
        if 'initialization-custody.sql' in profile.get('manifest',{}).get('files',{}) and not profile.get('initializationPolicies'):
            raise ValueError('New custody target requires its closed dynamic initialization policy')
        if 'initializationPolicies' in profile:
            from ._initialization_custody import validate_policy
            if profile['manifest']!=target or endpoint!=manifest['target']:raise ValueError('Initialization policy belongs only to exact new target manifest')
            policies=profile['initializationPolicies']
            if type(policies) is not list or len(policies)!=1 or profile.get('initializationAlternatives') or profile.get('definitionAlternatives'):
                raise ValueError('One closed dynamic policy without finite alternatives required')
            for policy in policies:
                validate_policy(policy,profile['manifest'])
    for edge in manifest['edges']:
        candidate=json.loads(artifacts[edge['artifact']])
        if candidate['source']!=edge['source'] or candidate['target']!=edge['target']:
            raise ValueError('Declared migration edge changed')
        for field in ('steps','ownership','moduleGrants'):
            if type(candidate[field]) is not list or any(type(s) is not str or not s for s in candidate[field]):
                raise ValueError('Exact ordered migration statements required')
        feed_grants=candidate.get('feedGrants',[])
        if type(feed_grants) is not list or any(type(s) is not str or not s for s in feed_grants):
            raise ValueError('Exact feed-role grant signatures required')
        for endpoint in (edge['source'],edge['target']):
            if json.loads(artifacts[endpoint+'.json'])['sha256']!=endpoint:
                raise ValueError('Exact endpoint inventory required')
    for digest in [manifest['target'],*manifest['sources']]:
        profile=json.loads(artifacts[digest+'.json'])
        if profile.get('aclNameProfile')=='truss-native-acl-names/0.2':continue
        name=manifest.get('exactAclProfiles',{}).get(digest)
        if name not in artifacts:raise ValueError('Every admitted runtime requires exact text ACL evidence')
        exact=json.loads(artifacts[name])
        if exact.get('runtimeManifestSha256')!=digest or exact.get('aclNameProfile')!='truss-native-acl-names/0.2':
            raise ValueError('Exact original ACL evidence correspondence required')
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
