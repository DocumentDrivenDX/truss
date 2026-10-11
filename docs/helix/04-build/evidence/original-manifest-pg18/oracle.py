"""Independent test oracle for a selected catalog-only v0.2 manifest.

Inputs are original required facts/artifacts, never registered feed rows. This
module is not a Truss public API, installation producer or native validator.
"""
import base64
import hashlib
import json
import re
from truss._catalog_report_semantics import canonical_numeric_free


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def profile_pin(raw):
    import json
    definition=json.loads(raw)
    return {'identity':definition['identity'],'version':definition['version'],'sha256':digest(raw)}


def exact_artifact(value):
    if type(value) is not dict or set(value)!={'identity','bytesBase64','sha256'}:
        raise ValueError('closed original artifact required')
    if type(value['identity']) is not str or not value['identity']:
        raise ValueError('original artifact identity required')
    raw=base64.b64decode(value['bytesBase64'],validate=True)
    if base64.b64encode(raw).decode()!=value['bytesBase64'] or digest(raw)!=value['sha256']:
        raise ValueError('original artifact bytes and digest correspondence required')
    return dict(value)


def native_decimal(value,maximum,positive=False):
    if type(value) is not str or re.fullmatch(r'0|[1-9][0-9]*',value) is None:
        raise ValueError('canonical native decimal required')
    number=int(value)
    if number>maximum or positive and number==0:
        raise ValueError('native decimal range')
    return value


def expected_manifest(*, original_input, revision, xid, feed_context,
                      manifest_definition_bytes, payload_profile_bytes,
                      original_payload_bytes, original_configuration, original_configuration_profile_bytes):
    revision=native_decimal(revision,2147483647,True)
    xid=native_decimal(xid,18446744073709551615,True)
    if set(feed_context)!={'sourceEpoch','feedProfile','scopeIdentity'} or any(type(v) is not str or not v for v in feed_context.values()):
        raise ValueError('closed original feed context required')
    required=[];seen={}
    for document in original_input['documents']:
        artifact=exact_artifact(document['artifact'])
        association=(artifact,canonical_numeric_free(document['umfProfile']))
        identity=artifact['identity']
        if identity in seen:
            if seen[identity]!=association:raise ValueError('conflicting original document artifact identity')
            continue
        seen[identity]=association
        required.append({'revision':revision,'artifact':artifact})
    if not required:raise ValueError('complete original document closure required')
    required.sort(key=lambda p:p['artifact']['identity'].encode('utf8'))
    definition=json.loads(manifest_definition_bytes)
    rule=definition['configurationArtifactIdentity']
    if (rule['prefix']!='truss.candidate.generation-configuration/0.1.0'
        or rule['coordinates']!=['sourceEpochUtf8LowerHex','installationIdUtf8LowerHex','canonicalNonnegativeInt8Generation']
        or rule['separator']!='/'):
        raise ValueError('selected configuration identity rule required')
    cfg=original_configuration
    generation=native_decimal(cfg['generation'],9223372036854775807)
    if cfg['sourceEpoch']!=feed_context['sourceEpoch']:
        raise ValueError('original configuration epoch correspondence required')
    def chunks(raw):
        return [raw[i:i+32768].hex() for i in range(0,len(raw),32768)]
    artifact_bytes=canonical_numeric_free({
        'installation':cfg['installationId'],'sourceEpoch':cfg['sourceEpoch'],
        'targetIncarnation':cfg['targetIncarnation'],'generation':generation,
        'keyReuse':cfg['keyReuse'],'journalMode':cfg['journalMode'],
        'admissionProfileHexChunks':chunks(cfg['admissionProfileBytes']),
        'configurationHexChunks':chunks(cfg['configurationBytes']),
        'bindingHexChunks':chunks(cfg['bindingBytes']),
        'inventoryHexChunks':chunks(cfg['inventoryBytes'])})
    identity=rule['prefix']+'/'+cfg['sourceEpoch'].encode('utf8').hex()+'/'+cfg['installationId'].encode('utf8').hex()+'/'+generation
    configuration_artifact={'identity':identity,'bytesBase64':base64.b64encode(artifact_bytes).decode(),'sha256':digest(artifact_bytes)}
    selected={'generation':generation,'keyReuse':cfg['keyReuse'],'journalMode':cfg['journalMode'],
        'configurationProfile':profile_pin(original_configuration_profile_bytes),
        'installedProducerInventorySha256':digest(cfg['inventoryBytes']),
        'sourceEpoch':cfg['sourceEpoch'],'installationId':cfg['installationId']}
    tree={'interfaceVersion':'truss-feed-transaction/0.2.0','context':dict(feed_context),'xid':xid,
          'manifestProfile':profile_pin(manifest_definition_bytes),
          'configurationPrerequisites':[{'configuration':selected,'artifact':exact_artifact(configuration_artifact)}],
          'members':[{'ordinal':'0','key':{'kind':'revision','revision':revision},
                      'payloadProfile':profile_pin(payload_profile_bytes),'payloadSha256':digest(original_payload_bytes)}],
          'prerequisites':required}
    original_tree=canonical_numeric_free(tree)
    preimage=b'truss-canonical/0.1.0\ntruss-feed-manifest/0.2.0\n'+original_tree
    semantic_digest=digest(preimage)
    complete=dict(tree,manifestSha256=semantic_digest)
    return {'tree':tree,'treeBytes':original_tree,'semanticPreimage':preimage,
            'semanticSha256':semantic_digest,'wireBytes':canonical_numeric_free(complete)}
