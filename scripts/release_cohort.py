# SPDX-License-Identifier: MIT OR Apache-2.0
"""Selected packaging identities; absent qualified bytes always refuse admission."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import tomllib
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
COHORT = Path(__file__).with_name('truss-release-cohort.json')

CORE_SOURCE_ROLES = {
    'census': 'tests/qualification/fixtures/inspector-construction-batch.json',
    'resourceFixture': 'tests/qualification/fixtures/inspector-installed-candidate-01010-resources.json',
    'inspectionCorpus': 'tests/rust-core/fixtures/access-inspection/cases.json',
    'sagaCorpus': 'fixtures/saga/portable.json',
    'sagaCustody': 'scripts/saga-portable/custody.ts',
}
CORE_PRODUCERS = {
    'tools/probe_inspector_installed_factory.py',
    'tools/qualify_inspector_construction_batch.py',
    'tools/run_inspector_cost_gate.py',
    'tools/run_inspector_attribution_lanes.py',
}
WEFT_SOURCE_ROLES = {
    'sdkProducer': 'tests/engine-catalog/wheel-smoke.py',
    'qualificationProducer': 'scripts/release/qualify_current_sdk_0457.py',
    'temporalBoundary': 'tests/engine-catalog/temporal-boundary.py',
    'temporalCorpus': 'tests/engine-catalog/temporal-native-495-corpus.json',
    'routingBoundary': 'tests/engine-catalog/temporal-routing-boundary.py',
}
_HEX64 = re.compile(r'[0-9a-f]{64}\Z')
_HEX40 = re.compile(r'[0-9a-f]{40}\Z')


def _closed_ref(row, path, label):
    if type(row) is not dict or set(row) != {'path', 'sha256'} or row.get('path') != path:
        raise ValueError('Malformed trusted component source reference: ' + label)
    digest = row.get('sha256')
    if type(digest) is not str or _HEX64.fullmatch(digest) is None or set(digest) == {'0'}:
        raise ValueError('Malformed trusted component source digest: ' + label)
    return digest


def component_source_refs(cohort_bytes):
    """Parse the source-controlled C1 configuration without reading result claims."""
    value = json.loads(cohort_bytes)
    section = value.get('componentPrerequisiteSourceRefs')
    if section is None:
        raise ValueError('Missing trusted component source refs: core')
    if type(section) is dict:
        for role in ('core','weft'):
            if section.get(role) is None:
                raise ValueError('Missing trusted component source refs: '+role)
    if type(section) is not dict or set(section) != {'core', 'weft', 'validatorSourceRefs'}:
        raise ValueError('Malformed closed componentPrerequisiteSourceRefs section')
    core, weft, validators = section['core'], section['weft'], section['validatorSourceRefs']
    core_fields = {'sourceCommit', 'controllerSourceCommit', 'sourceRefs', 'producerSourceRefs',
                   'sagaSourceRefs', 'originalMetadataRefs'}
    if type(core) is not dict or set(core) != core_fields:
        raise ValueError('Malformed trusted Core C1 source refs')
    for key in ('sourceCommit', 'controllerSourceCommit'):
        if type(core[key]) is not str or _HEX40.fullmatch(core[key]) is None or set(core[key]) == {'0'}:
            raise ValueError('Malformed trusted Core C1 ' + key)
    if type(core['sourceRefs']) is not dict or set(core['sourceRefs']) != set(CORE_SOURCE_ROLES):
        raise ValueError('Malformed trusted Core C1 source role roster')
    for role, path in CORE_SOURCE_ROLES.items():
        _closed_ref(core['sourceRefs'][role], path, 'core.' + role)
    if type(core['producerSourceRefs']) is not dict or set(core['producerSourceRefs']) != CORE_PRODUCERS:
        raise ValueError('Malformed trusted Core producer source roster')
    for path, ref in core['producerSourceRefs'].items():
        _closed_ref(ref, path, 'core.producer.' + path)
    if type(core['sagaSourceRefs']) is not list or not core['sagaSourceRefs']:
        raise ValueError('Missing trusted Saga source refs')
    saga_seen = set()
    for row in core['sagaSourceRefs']:
        if type(row) is not dict or set(row) != {'path', 'sha256'}:
            raise ValueError('Malformed trusted Saga source ref')
        path = row['path']
        if type(path) is not str or not path or path.startswith('/') or '..' in path.split('/') or path in saga_seen:
            raise ValueError('Unsafe or duplicate trusted Saga source path')
        _closed_ref(row, path, 'core.saga')
        saga_seen.add(path)
    metadata_roles = {'run', 'job', 'artifact', 'sourceAndPayload', 'producer'}
    if type(core['originalMetadataRefs']) is not dict or set(core['originalMetadataRefs']) != metadata_roles:
        raise ValueError('Malformed original Core metadata refs')
    for role, ref in core['originalMetadataRefs'].items():
        if type(ref) is not dict or set(ref) != {'path', 'sha256'}:
            raise ValueError('Malformed original Core metadata ref: ' + role)
        path = ref['path']
        if type(path) is not str or not path or path.startswith('/') or '..' in path.split('/'):
            raise ValueError('Unsafe original Core metadata path: ' + role)
        _closed_ref(ref, path, 'core.metadata.' + role)
    weft_fields = {'sourceCommit', 'sourceTree', 'canonicalCoreSourceCommit', 'cargoLockSha256',
                   'handoff', 'originalMetadataRefs', 'sourceRefs'}
    if type(weft) is not dict or set(weft) != weft_fields:
        raise ValueError('Malformed trusted Weft source refs')
    for key in ('sourceCommit', 'sourceTree', 'canonicalCoreSourceCommit'):
        if type(weft[key]) is not str or _HEX40.fullmatch(weft[key]) is None or set(weft[key]) == {'0'}:
            raise ValueError('Malformed trusted Weft ' + key)
    if type(weft['cargoLockSha256']) is not str or _HEX64.fullmatch(weft['cargoLockSha256']) is None:
        raise ValueError('Malformed trusted Weft Cargo.lock digest')
    for role, ref in [('handoff', weft['handoff'])]:
        if type(ref) is not dict or set(ref) != {'path', 'sha256'}:
            raise ValueError('Malformed trusted Weft handoff ref')
        _closed_ref(ref, ref['path'], 'weft.' + role)
    if type(weft['originalMetadataRefs']) is not dict or set(weft['originalMetadataRefs']) != {'run', 'job', 'artifact'}:
        raise ValueError('Malformed original Weft metadata refs')
    for role, ref in weft['originalMetadataRefs'].items():
        if type(ref) is not dict or set(ref) != {'path', 'sha256'}:
            raise ValueError('Malformed original Weft metadata ref: ' + role)
        _closed_ref(ref, ref['path'], 'weft.metadata.' + role)
    if type(weft['sourceRefs']) is not dict or set(weft['sourceRefs']) != set(WEFT_SOURCE_ROLES):
        raise ValueError('Malformed trusted Weft source role roster')
    for role, path in WEFT_SOURCE_ROLES.items():
        _closed_ref(weft['sourceRefs'][role], path, 'weft.' + role)
    if type(validators) is not dict or set(validators) != {'coreRegistry', 'weftHandoff'}:
        raise ValueError('Malformed trusted component validator source roster')
    _closed_ref(validators['coreRegistry'], 'scripts/component_prerequisite_validators.py', 'validator.coreRegistry')
    _closed_ref(validators['weftHandoff'], 'scripts/prepare-temporal-binary-enrollment.py', 'validator.weftHandoff')
    return section


def _read_source_refs(section, members):
    """Resolve only source paths fixed by the reviewed carrier role tables."""
    refs = []
    core = section['core']
    refs.extend(core['sourceRefs'].values())
    refs.extend(core['producerSourceRefs'].values())
    refs.extend(core['sagaSourceRefs'])
    refs.extend(core['originalMetadataRefs'].values())
    weft = section['weft']
    refs.append(weft['handoff']); refs.extend(weft['originalMetadataRefs'].values())
    refs.extend(weft['sourceRefs'].values()); refs.extend(section['validatorSourceRefs'].values())
    resolved = {}
    for ref in refs:
        path, expected = ref['path'], ref['sha256']
        raw = members.get(path)
        if raw is None:
            raw = members.get('source/' + path)
        if raw is None:
            raw = members.get('inputs/' + path)
        if type(raw) is not bytes or hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError('Missing trusted component source reference/bytes: ' + path)
        resolved[path] = raw
    return resolved


def _require_weft_overall_outcome(run_id, attempt, job_id, conclusion):
    if conclusion == 'success':
        return
    if (conclusion == 'cancelled' and str(run_id) == '41686658658'
            and str(attempt) == '1' and str(job_id) == '126094501575'):
        return
    raise ValueError('Only successful Weft runs or the pinned cancelled overall run with its selected successful job are accepted')


def derive_component_expected(cohort_bytes, members, *, owner_identities, admitted_wheels):
    """Derive Core registry expectations solely from pinned source/config bytes.

    ``members`` is the already-authenticated immutable archive-member mapping.
    It is never used as an authority for a hash: each selected byte string is
    checked against the committed cohort's exact path/SHA reference first.
    """
    section = component_source_refs(cohort_bytes)
    source_bytes = _read_source_refs(section, members)
    core = section['core']
    selected_cohort=json.loads(cohort_bytes)
    owner = owner_identities.get('core') if type(owner_identities) is dict else None
    weft_owner = owner_identities.get('weft') if type(owner_identities) is dict else None
    wheel = admitted_wheels.get('core') if type(admitted_wheels) is dict else None
    weft_wheel = admitted_wheels.get('weft') if type(admitted_wheels) is dict else None
    if type(owner) is not dict or type(wheel) is not dict or type(weft_owner) is not dict or type(weft_wheel) is not dict:
        raise ValueError('Missing independently admitted Core/Weft owner/wheel identity')
    if core['controllerSourceCommit'] != core['sourceCommit']:
        raise ValueError('Current Core C1 producer/controller source must be the same authenticated source')
    if (owner.get('sourceCommit') != core['sourceCommit']
            or wheel.get('sha256') != owner.get('wheelSha256')):
        raise ValueError('Trusted Core C1 source/wheel differs from admitted owner closure')
    if type(owner.get('moduleSha256')) is not str or _HEX64.fullmatch(owner['moduleSha256']) is None:
        raise ValueError('Missing admitted Core native module identity')
    wheel_path=owner.get('wheelPath')
    if type(wheel_path) is not str or wheel_path != wheel.get('path'):
        raise ValueError('Admitted Core wheel path differs from owner closure')
    wheel_raw=members.get(wheel_path, members.get('inputs/'+wheel_path))
    if type(wheel_raw) is not bytes or hashlib.sha256(wheel_raw).hexdigest()!=wheel['sha256']:
        raise ValueError('Admitted Core wheel bytes/hash are missing or differ')
    with ZipFile(__import__('io').BytesIO(wheel_raw)) as archive:
        names=archive.namelist()
        metadata_paths=[name for name in names if name.endswith('.dist-info/METADATA')]
        module_path='umf/'+owner.get('modulePath','')
        if len(metadata_paths)!=1 or module_path not in names:
            raise ValueError('Admitted Core wheel lacks unique metadata/native module')
        from email.parser import BytesParser
        metadata=BytesParser().parsebytes(archive.read(metadata_paths[0]))
        selected_core=selected_cohort.get('core',{})
        if (metadata.get('Name','').lower().replace('_','-')!=selected_core.get('distribution')
                or metadata.get('Version')!=selected_core.get('version')
                or hashlib.sha256(archive.read(module_path)).hexdigest()!=owner['moduleSha256']):
            raise ValueError('Admitted Core wheel metadata/native bytes differ from selected closure')

    weft_config=section['weft']
    if weft_owner.get('sourceCommit')!=weft_config['sourceCommit'] or weft_wheel.get('sha256')!=weft_owner.get('wheelSha256'):
        raise ValueError('Trusted Weft source/wheel differs from admitted owner closure')
    weft_wheel_path=weft_owner.get('wheelPath')
    if type(weft_wheel_path) is not str or weft_wheel_path!=weft_wheel.get('path'):
        raise ValueError('Admitted Weft wheel path differs from owner closure')
    weft_raw=members.get(weft_wheel_path,members.get('inputs/'+weft_wheel_path))
    if type(weft_raw) is not bytes or hashlib.sha256(weft_raw).hexdigest()!=weft_wheel['sha256']:
        raise ValueError('Admitted Weft wheel bytes/hash are missing or differ')
    with ZipFile(__import__('io').BytesIO(weft_raw)) as archive:
        names=archive.namelist();metadata_paths=[name for name in names if name.endswith('.dist-info/METADATA')]
        module_path='weft/'+weft_owner.get('modulePath','')
        if len(metadata_paths)!=1 or module_path not in names or 'weft/__init__.py' not in names:
            raise ValueError('Admitted Weft wheel lacks unique metadata/native/shim members')
        from email.parser import BytesParser
        metadata=BytesParser().parsebytes(archive.read(metadata_paths[0]))
        if (metadata.get('Name','').lower().replace('_','-')!=selected_cohort.get('weft',{}).get('distribution')
                or metadata.get('Version')!=selected_cohort.get('weft',{}).get('version')
                or hashlib.sha256(archive.read(module_path)).hexdigest()!=weft_owner.get('moduleSha256')
                or hashlib.sha256(archive.read('weft/__init__.py')).hexdigest()!=weft_owner.get('shimSha256')):
            raise ValueError('Admitted Weft wheel metadata/native/shim bytes differ from selected closure')

    get = lambda role: source_bytes[core['sourceRefs'][role]['path']]
    census = json.loads(get('census'))
    fixture = json.loads(get('resourceFixture'))
    corpus = json.loads(get('inspectionCorpus'))
    if type(census.get('installedFactory')) is not dict:
        raise ValueError('Missing source-controlled installed-factory census')
    selected = census['installedFactory']
    if selected.get('status') != 'source-frozen' or selected.get('inputProfile') != 'installed-canonical/1':
        raise ValueError('Current source-controlled C1 census is not installed-canonical')
    if selected.get('currentInputs') != {'fixturePath': core['sourceRefs']['resourceFixture']['path'],
            'fixtureSHA256': core['sourceRefs']['resourceFixture']['sha256'], 'metadataVersion': '0.10.10'}:
        raise ValueError('Current C1 source census/fixture binding differs')
    if fixture.get('bindingStatus') != 'source-bound' or fixture.get('candidateArtifactVersion') != '0.10.10':
        raise ValueError('Current source-bound C1 resource fixture is absent')
    generation=fixture.get('generation')
    if (type(generation) is not dict or type(generation.get('sourceCommit')) is not str
            or _HEX40.fullmatch(generation['sourceCommit']) is None
            or type(generation.get('sourceTree')) is not str or _HEX40.fullmatch(generation['sourceTree']) is None
            or any(type(generation.get(key)) is not str or not generation[key]
                   for key in ('runId','attempt','jobId','artifactId'))):
        raise ValueError('Current source-bound resource fixture G0 generation bindings are malformed')

    resources = fixture.get('resources')
    resource_names = ('coreSchema', 'referenceSchema', 'packageSchema', 'constraints', 'domainPolicy',
                      'tablesPackage', 'actionsPackage', 'bindingPackage', 'stableBindingPackage')
    if type(resources) is not dict or set(resources) != set(resource_names):
        raise ValueError('Source-controlled C1 resource fixture has incomplete nine-resource roster')
    resource_manifest = {'profile': 'umf.codegen.installed-source-manifest/1',
        'inputProfile': 'installed-canonical/1',
        'resources': [{'name': name, **resources[name]} for name in resource_names]}
    for row in resource_manifest['resources']:
        raw=members.get(row['path'],members.get('owner/core/'+row['path'],
            members.get('inputs/owner/core/'+row['path'])))
        if type(raw) is not bytes or len(raw)!=row['bytes'] or hashlib.sha256(raw).hexdigest()!=row['sha256']:
            raise ValueError('Missing/mismatched trusted Core C1 resource bytes: '+row['path'])
    identity = {'resourceFixture': core['sourceRefs']['resourceFixture']['path'],
        'resourceFixtureSHA256': core['sourceRefs']['resourceFixture']['sha256'],
        'candidateArtifactVersion': fixture['candidateArtifactVersion'],
        'literalDataSHA256': fixture['literalData']['sha256'],
        'generation': fixture['generation'],
        'scope': 'private-candidate-component-only-not-release-proof'}

    rows = selected.get('rust'); groups = selected.get('python'); controls = selected.get('publicControls')
    if type(rows) is not list or type(groups) is not list or type(controls) is not list:
        raise ValueError('Source-controlled C1 census lacks named installed-factory cases')
    rust_cases = []
    for group in rows:
        for case in group.get('cases', ()):
            rust_cases.append({'package': group.get('package'), 'target': group.get('target'), 'name': case.get('name')})
    python_groups = [{'group': group.get('group'), 'cases': group.get('cases')} for group in groups]
    cases = corpus.get('cases')
    if type(cases) is not list or len(cases) != 17:
        raise ValueError('Original source-controlled 17-case factory oracle corpus required')
    factory_pairs = []
    for case in cases:
        for carrier in ('dispatcher', 'list', 'tuple'):
            result = {'ok': True, 'result': case['expected']} if carrier == 'dispatcher' else case['expected']
            raw = json.dumps(result, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()
            factory_pairs.append({'case': case['id'], 'carrier': carrier,
                                  'resultSHA256': hashlib.sha256(raw).hexdigest()})

    custody = source_bytes[core['sourceRefs']['sagaCustody']['path']].decode('utf-8')
    match = re.search(r'SAGA_QUALIFICATION_INPUTS\s*=\s*\[(.*?)\]\s*as const', custody, re.S)
    if match is None:
        raise ValueError('Original Saga custody source roster is not statically readable')
    saga_paths = re.findall(r"'([^']+)'", match.group(1))
    saga_refs = {row['path']: row['sha256'] for row in core['sagaSourceRefs']}
    if len(saga_paths) != len(set(saga_paths)) or set(saga_paths) != set(saga_refs):
        raise ValueError('Trusted Saga source refs do not exactly match original custody roster')
    for path, digest in saga_refs.items():
        if hashlib.sha256(source_bytes[path]).hexdigest() != digest:
            raise ValueError('Trusted Saga input source hash differs: ' + path)

    metadata = core['originalMetadataRefs']
    raw_objects = {role: json.loads(members.get(ref['path'], members.get('inputs/' + ref['path'], b'')))
                   for role, ref in metadata.items() if role in ('run', 'job', 'artifact')}
    run, job, artifact = raw_objects['run'], raw_objects['job'], raw_objects['artifact']
    run_id = str(run.get('id', '')); attempt = str(run.get('run_attempt', ''))
    if (not run_id.isdecimal() or int(run_id) <= 0 or not attempt.isdecimal() or int(attempt) <= 0
            or run.get('conclusion') not in ('success','cancelled') or job.get('conclusion')!='success'
            or str(job.get('run_id')) != run_id or str(job.get('run_attempt')) != attempt
            or str(artifact.get('workflow_run', {}).get('id', run_id)) != run_id
            or run.get('head_sha') != core['controllerSourceCommit']):
        raise ValueError('Authenticated original Core run/job/artifact/source metadata does not join')
    repository=run.get('repository',{}).get('full_name') if type(run.get('repository')) is dict else None
    if (not repository or job.get('repository',{}).get('full_name',repository)!=repository
            or artifact.get('expired') is True):
        raise ValueError('Authenticated original Core repository/artifact metadata differs')
    weft_meta={role:json.loads(source_bytes[ref['path']])
               for role,ref in weft_config['originalMetadataRefs'].items()}
    wrun,wjob,wartifact=weft_meta['run'],weft_meta['job'],weft_meta['artifact']
    weft_run_id=str(wrun.get('id',''));weft_attempt=str(wrun.get('run_attempt',''))
    weft_repo=wrun.get('repository',{}).get('full_name') if type(wrun.get('repository')) is dict else None
    run_conclusion=wrun.get('conclusion')
    if (not weft_run_id.isdecimal() or int(weft_run_id)<=0 or not weft_attempt.isdecimal()
            or int(weft_attempt)<=0 or run_conclusion not in ('success','cancelled')
            or wrun.get('head_sha')!=weft_config['sourceCommit'] or not weft_repo
            or str(wjob.get('run_id'))!=weft_run_id or str(wjob.get('run_attempt'))!=weft_attempt
            or wjob.get('conclusion')!='success'
            or wjob.get('repository',{}).get('full_name',weft_repo)!=weft_repo
            or str(wartifact.get('workflow_run',{}).get('id',weft_run_id))!=weft_run_id
            or wartifact.get('expired') is True):
        raise ValueError('Authenticated original Weft run/job/artifact metadata does not join')
    _require_weft_overall_outcome(weft_run_id,weft_attempt,wjob.get('id'),run_conclusion)
    for role in ('sourceAndPayload','producer'):
        ref=metadata[role]
        raw=members.get(ref['path'],members.get('inputs/'+ref['path']))
        if type(raw) is not bytes or hashlib.sha256(raw).hexdigest()!=ref['sha256']:
            raise ValueError('Missing trusted Core original '+role+' metadata bytes')
        try: value=json.loads(raw)
        except (UnicodeDecodeError,json.JSONDecodeError) as error:
            raise ValueError('Malformed trusted Core original '+role+' metadata') from error
        if type(value) is not dict:
            raise ValueError('Original Core '+role+' metadata object required')
        if role=='sourceAndPayload':
            source=value.get('sourceCommit',value.get('source'))
            if source!=core['sourceCommit']:
                raise ValueError('Original Core source/payload source identity differs')
        else:
            if value.get('source')!=core['sourceCommit']:
                raise ValueError('Original Core producer source identity differs')
            # Original producer.json has no controllerSource field. The
            # producer source joins the authenticated raw run/head/job above.
    return {'source': core['sourceCommit'], 'controllerSource': core['controllerSourceCommit'],
        'wheelSha256': wheel['sha256'], 'nativeSha256': owner['moduleSha256'],
        'censusSha256': core['sourceRefs']['census']['sha256'], 'run': run_id, 'attempt': attempt,
        'currentInputIdentity': identity, 'resourceManifest': resource_manifest,
        'factoryPairs': factory_pairs, 'earlyControls': controls, 'rustCases': rust_cases,
        'pythonGroups': python_groups, 'sagaCorpusSha256': core['sourceRefs']['sagaCorpus']['sha256'],
        'sagaInputs': saga_refs}


_STAGE_RECORDS = {
    'inventory-observation': ('sourceIdentity','ownerClosure','resourceClosure',
                              'historyDisposition','lifecycle2','weftClosure'),
    'native-campaign': ('sourceIdentity','ownerClosure','resourceClosure',
                        'historyDisposition','lifecycle2','weftClosure','inventories',
                        'freshBaseline','campaignInputs'),
    'prepublication': ('sourceIdentity','ownerClosure','resourceClosure',
                       'historyDisposition','lifecycle2','weftClosure','inventories',
                       'freshBaseline','campaignInputs','campaign130','exactTagProofs'),
}


def require_stage_admission(stage, *, component, records):
    """Require typed validated inputs for one stage; stage outputs are excluded.

    Callers supply records returned by the existing fixed source/receipt
    validators. This boundary rejects readiness booleans and arbitrary scope
    strings. It does not use ``remainingGates`` as an admission predicate.
    """
    if stage not in _STAGE_RECORDS:
        raise ValueError('Unknown temporal admission stage')
    from component_prerequisite_validators import REQUIRED, WEFT_ORIGINAL_CHECK_CALLS
    if (type(component) is not dict or set(component) != {'coreC1','weftSDK42','stagePrerequisites'}
            or type(component['coreC1']) is not dict or set(component['coreC1']) != REQUIRED
            or type(component['weftSDK42']) is not dict
            or component['weftSDK42'] != WEFT_ORIGINAL_CHECK_CALLS
            or type(component['stagePrerequisites']) is not dict
            or set(component['stagePrerequisites']) != {'historyDisposition','lifecycle2','weftOwnerSource'}):
        raise ValueError('Validated original Core/Weft component prerequisite records required')
    if type(records) is not dict:
        raise ValueError('Validated original temporal stage records required')
    records={**component['stagePrerequisites'],**records}
    missing=[]
    for key in _STAGE_RECORDS[stage]:
        value=records.get(key)
        if value is None or type(value) is bool or (type(value) in (dict,list,tuple) and not value):
            missing.append(key)
    if missing:
        raise ValueError('Missing applicable '+stage+' evidence: '+', '.join(missing))
    if stage == 'prepublication':
        proof = records['exactTagProofs']
        readiness = proof.get('ownerReadiness') if type(proof) is dict else None
        if type(readiness) is not dict or set(readiness) != {'core','weft'}:
            raise ValueError('Missing separately validated Core and Weft owner readiness')
        core_ready, weft_ready = readiness['core'], readiness['weft']
        selected_core = records.get('selectedCore')
        if (type(selected_core) is not dict or type(selected_core.get('qualification')) is not dict
                or type(core_ready) is not dict
                or core_ready.get('profile') != 'core-selected-owner-readiness/1'
                or core_ready.get('sourceCommit') != selected_core.get('sourceCommit')
                or core_ready.get('version') != selected_core.get('version')
                or core_ready.get('wheelSha256') != selected_core.get('wheelSha256')
                or core_ready.get('nativeSha256') != selected_core.get('nativeSha256')
                or core_ready.get('authorityCommit') != selected_core['qualification'].get('authorityCommit')
                or core_ready.get('platforms') != ('linux-x86_64','macos-arm64')
                or core_ready.get('sdkChecks') != ('build','package','browser-setup','bun-full','node-native','node-browser','bun-saga','chromium-saga')
                or core_ready.get('cells') != ('direct-3.11.17','direct-3.13.16','rebuilt-3.11.17','rebuilt-3.13.16')):
            raise ValueError('Core owner readiness differs from trusted selected Core source/wheel/context')
        if (type(proof) is not dict
                or set(proof) != {'runId','attempt','sourceCommit','tag','jobs','jobStepEvidence','nestedReusableWorkflows','releaseId','ownerReadiness'}
                or type(proof.get('runId')) is not str or not proof['runId'].isdecimal()
                or int(proof['runId']) <= 0
                or type(proof.get('attempt')) is not str or not proof['attempt'].isdecimal()
                or int(proof['attempt']) <= 0
                or type(proof.get('sourceCommit')) is not str
                or _HEX40.fullmatch(proof['sourceCommit']) is None
                or type(proof.get('tag')) is not str
                or re.fullmatch(r'v(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)',proof['tag']) is None
                or proof.get('jobs') != ('native','package','publish')
                or type(proof.get('jobStepEvidence')) is not dict
                or set(proof['jobStepEvidence']) != {'native (ubuntu-24.04)','package','publish'}
                or any(type(rows) is not tuple or not rows or any(type(row) is not str for row in rows)
                       for rows in proof['jobStepEvidence'].values())
                or proof.get('nestedReusableWorkflows') != ()
                or type(proof.get('releaseId')) is not str or not proof['releaseId'].isdecimal()
                or int(proof['releaseId']) <= 0
                or type(weft_ready) is not dict
                or set(weft_ready) != {'profile','sourceCommit','sourceTree','platforms',
                    'nodeCases','chromiumCases','browserCases','sourceDependencyClosure'}
                or weft_ready.get('profile') != 'weft-0457-published-owner-proof/1'
                or type(weft_ready.get('sourceCommit')) is not str
                or type(weft_ready.get('sourceTree')) is not str
                or weft_ready.get('platforms') != ('linux-aarch64','linux-x86_64','macos-arm64')
                or weft_ready.get('nodeCases') != 14
                or weft_ready.get('chromiumCases') != 14
                or weft_ready.get('browserCases') != 9
                or weft_ready.get('sourceDependencyClosure') != 'cargo-package-lists-and-local-dependency-bound'):
            raise ValueError('Missing validated exact-tag package/native/release job proof')
        owner_source=component['stagePrerequisites']['weftOwnerSource']
        if (weft_ready['sourceCommit'] != owner_source['sourceCommit']
                or weft_ready['sourceTree'] != owner_source['sourceTree']):
            raise ValueError('Weft owner readiness source/tree differs from authenticated Weft owner source')
    return {'stage':stage,'componentPrerequisites':component,
            'evidenceKeys':tuple(_STAGE_RECORDS[stage]),
            'scope':'Prerequisites validated; this stage and downstream outputs remain pending'}


def load_cohort(path=COHORT, *, require_qualified=False):
    cohort = json.loads(Path(path).read_text())
    expected = {
        'truss': ('umf-truss', '0.0.56'),
        'weft': ('umf-weft', '0.4.57'),
        'access': ('umf_access', '0.1.0.dev10'),
        'core': ('umf-core', '0.10.8'),
    }
    if cohort.get('schema') != 'truss-release-cohort/1':
        raise ValueError('Unknown release cohort schema')
    for key, (distribution, version) in expected.items():
        if cohort.get(key) != dict(distribution=distribution, version=version):
            raise ValueError('Selected package identity differs: ' + key)
    qualified = cohort.get('qualified')
    if require_qualified or qualified is not None:
        if not isinstance(qualified, dict):
            raise ValueError('Qualified artifact identities deferred: coherent source/bytes not frozen')
        for field, length in (('coreSourceRevision', 40), ('weftSourceRevision', 40),
                              ('nativeManifestSha256', 64)):
            value = qualified.get(field)
            if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{%d}' % length, value) or set(value) == {'0'}:
                raise ValueError('Exact qualified identity required: ' + field)
        rows = qualified.get('compilerCohorts')
        if not isinstance(rows, list) or not rows:
            raise ValueError('Actual qualified compiler cohorts required')
        for row in rows:
            if row.get('platform') != 'linux-x86_64' or row.get('sourceRevision') != qualified['weftSourceRevision']:
                raise ValueError('Qualified Linux compiler source required')
            filename = row.get('wheelFilename')
            if not isinstance(filename, str) or not re.fullmatch(r'umf_weft-0\.4\.57-[A-Za-z0-9_.+-]+\.whl', filename):
                raise ValueError('Exact qualified compiler wheel filename required')
            for field in ('wheelSha256', 'nativeModuleSha256'):
                value = row.get(field)
                if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value) or set(value) == {'0'}:
                    raise ValueError('Exact qualified compiler digest required: ' + field)
        for field in ('wheelSha256', 'nativeModuleSha256', 'platform', 'wheelFilename'):
            if len({row[field] for row in rows}) != len(rows):
                raise ValueError('Ambiguous qualified compiler cohort')
    return cohort


def check_project(root=ROOT):
    cohort = load_cohort()
    project = tomllib.loads((root / 'packages/python/pyproject.toml').read_text())['project']
    if (project['name'], project['version']) != (cohort['truss']['distribution'], cohort['truss']['version']):
        raise ValueError('Truss project identity differs')
    for extra, owner in (('query', 'weft'), ('typed-sdk', 'access')):
        selected = cohort[owner]
        if project['optional-dependencies'][extra] != [selected['distribution'] + '==' + selected['version']]:
            raise ValueError('Exact selected extra required: ' + extra)
    return cohort


def refuse_legacy_weft():
    try:
        importlib.metadata.distribution('weft-sql')
    except importlib.metadata.PackageNotFoundError:
        return
    raise ValueError('Legacy weft-sql conflicts with selected umf-weft import weft')


def verify_installed():
    cohort = load_cohort()
    refuse_legacy_weft()
    for owner in ('truss', 'weft', 'access', 'core'):
        row = cohort[owner]
        if importlib.metadata.version(row['distribution']) != row['version']:
            raise ValueError('Installed selected package version differs: ' + owner)
    import weft
    import umf_access
    for module, owner in ((weft, 'weft'), (umf_access, 'access')):
        distribution = importlib.metadata.distribution(cohort[owner]['distribution'])
        package = 'weft' if owner == 'weft' else 'umf_access'
        expected = Path(distribution.locate_file(package)).resolve()
        if not Path(module.__file__).resolve().is_relative_to(expected):
            raise ValueError('Selected package import origin differs: ' + owner)
    if weft.__version__ != cohort['weft']['version']:
        raise ValueError('Weft runtime version differs')
    return cohort


def hf_profile(root=ROOT, *, installed=False):
    """Overlay only producer identity; never rewrite the frozen HF assertions."""
    cohort = load_cohort(require_qualified=True)
    profile = json.loads((root / 'docs/helix/03-test/fixtures/hohfeld-followup-0.1.json').read_bytes())
    qualified = cohort['qualified']
    if installed:
        from importlib.resources import files
        native_bytes = files('truss').joinpath('_catalog_runtime/manifest.json').read_bytes()
    else:
        native_bytes = (root / 'packages/python/src/truss/_catalog_runtime/manifest.json').read_bytes()
    actual = hashlib.sha256(native_bytes).hexdigest()
    if actual != qualified['nativeManifestSha256']:
        raise ValueError('Qualified native manifest differs from actual source')
    # Any producer change requires separate owner review and a real new producer
    # receipt. This overlay never regenerates or silently accepts changed hashes.
    for name, digest in profile['producers'].items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest:
            raise ValueError('Original HF producer changed: ' + name)
    profile.update(toolkitVersion=cohort['truss']['version'],
                   compilerVersion=cohort['weft']['version'],
                   nativeManifestSha256=qualified['nativeManifestSha256'],
                   compilerCohorts=qualified['compilerCohorts'])
    return profile


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--qualified', action='store_true')
    args = parser.parse_args()
    check_project()
    print(json.dumps(load_cohort(require_qualified=args.qualified), indent=2))
