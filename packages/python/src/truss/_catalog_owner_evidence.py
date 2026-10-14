from ._catalog_source_reference import compact_catalog_sources,SOURCE_REFERENCE_FORMAT
"""Original packaged owner observation correspondence; no support authority."""
import base64
import hashlib
import json
from .preparation import _require_original_preparation
from ._owner_evidence_json import decode_owner_evidence_json, same_owner_evidence


def require_catalog_owner_evidence(prepared, evidence):
    _require_original_preparation(prepared)
    if type(evidence) is not dict or not same_owner_evidence(evidence,decode_owner_evidence_json(prepared.report_evidence_bytes)):
        raise ValueError('Original retained preparation report evidence required')
    collection=evidence.get('ownerObservations')
    coverage=evidence.get('observationCoverage')
    core=evidence.get('coreAssertionIdentities')
    if not all(type(value) is dict for value in (collection,coverage,core)):
        raise ValueError('Complete original owner report observations required')
    compact=compact_catalog_sources(prepared)
    if (collection.get('sourceFormat')==SOURCE_REFERENCE_FORMAT) is not compact:
        raise ValueError('Explicit observation source format required')
    documents={d['documentId']:d['artifact']['sha256'] for d in prepared.input()['documents']}
    profiles={'schema_properties':'profile','relationships':'profile','keys':'profile',
              'kind':'fieldProfile','nullability':'fieldProfile','cardinality':'fieldProfile','facets':'fieldProfile',
              'scalarType':'scalarProfile','members':'membersProfile','referenceLinks':'referenceLinksProfile'}
    owners={'profile':('declarations','umf-declaration-inspection'),
            'fieldProfile':('assertion-fields','umf-field-assertion-inspection'),
            'scalarProfile':('scalar-types','umf-scalar-type-inspection'),
            'membersProfile':('record-members','umf-record-members-inspection'),
            'referenceLinksProfile':('reference-links','umf-reference-links-inspection')}
    from .preparation import _release_for_prepared
    root,manifest=_release_for_prepared(prepared)
    for name,(mode,identity) in owners.items():
        owner=manifest['owner'] if root.name=='_umf_core08' else json.loads((root/'owners'/mode/'producer-manifest.json').read_bytes())
        if collection.get(name)!={'identity':identity,'version':owner['revision'],'sha256':owner['bundleSha256']}:
            raise ValueError('Exact packaged owner observation profile required')
    observations=collection.get('observations')
    if type(observations) is not list or len(observations)>4096:
        raise ValueError('Bounded complete original observations required')
    schedule=[]
    for document in prepared.documents:
        observation=document.observation()
        source=observation['source']
        basis='reversible_target' if observation['transition'] else 'original'
        def add(operation,identity,selected_basis='original'):
            if len(schedule)>=4096:
                raise ValueError('Original observation schedule capacity exceeded')
            schedule.append((document.document.document_id,operation,identity,selected_basis))
        add('schema_properties',{'scope':'document'},basis)
        for module in source['modules']:
            add('schema_properties',{'scope':'module','module':module['id']},basis)
            add('relationships',{'module':module['id']})
            for element in module['elements']:
                add('schema_properties',{'scope':'element','module':module['id'],'element':element['id']},basis)
                identity={'module':module['id'],'element':element['id']}
                for operation in ('kind','nullability','cardinality','facets','scalarType','members','referenceLinks'):
                    add(operation,identity)
                if element.get('kind')=='record':add('keys',identity)
    if len(observations)!=len(schedule):
        raise ValueError('Complete original observation schedule required')
    unavailable=[]
    for index,observed in enumerate(observations):
        operation=observed['operation'];document=observed['documentId']
        if (document,operation,observed['identity'],observed['basis'])!=schedule[index]:
            raise ValueError('Original ordered observation schedule required')
        if operation not in profiles or document not in documents:
            raise ValueError('Original qualified observation source required')
        artifact=observed['evidence']
        raw=base64.b64decode(artifact['bytesBase64'],validate=True)
        if base64.b64encode(raw).decode()!=artifact['bytesBase64'] or hashlib.sha256(raw).hexdigest()!=artifact['sha256']:
            raise ValueError('Original observation bytes required')
        payload=decode_owner_evidence_json(raw)
        expected={'profile':collection[profiles[operation]],'documentId':document,
                  'contentSha256':documents[document],'basis':observed['basis'],
                  'operation':operation,'identity':observed['identity'],'result':observed['result']}
        if compact:expected['sourceFormat']=SOURCE_REFERENCE_FORMAT
        if not same_owner_evidence(payload,expected):
            raise ValueError('Original document and observation correspondence required')
        document_index=list(documents).index(document)
        prefix='truss.owner-declaration-observation-references/0.1' if compact else 'truss.owner-declaration-observation'
        if artifact['identity']!=f'{prefix}/{document_index}/{index}':
            raise ValueError('Original ordered observation identity required')
        result=observed['result']
        if result['state']=='unavailable':
            unavailable.append({'documentId':document,'operation':operation,'identity':observed['identity'],'code':result['code'],'path':result['path']})
        elif result['state']!='observed':
            raise ValueError('Explicit original observation state required')
    if (coverage.get('observationsRequired')!=str(len(observations))
        or coverage.get('observationsAvailable')!=str(len(observations)-len(unavailable))
        or coverage.get('unavailable')!=unavailable
        or coverage.get('availability')!=('incomplete' if unavailable else 'available')):
        raise ValueError('Complete original observation coverage required')
    if core.get('complete') is not False or core.get('scope')!='original_inspected_core_source_identity_subset_only':
        raise ValueError('Original core subset scope required')
    return collection,coverage,core
