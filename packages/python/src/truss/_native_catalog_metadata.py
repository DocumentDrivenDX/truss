"""Bound original configured response bytes; no installed-profile authority."""
import json
import re
from hashlib import sha256
from importlib.resources import files
from ._acceptance_json import decode_acceptance_json


def _closed(value, names):
    if type(value) is not dict or set(value)!=set(names.split()):
        raise ValueError('Closed original native metadata required')
    return value


def _integer(value, minimum=0, maximum=9223372036854775807):
    if type(value) is not int or not minimum<=value<=maximum:
        raise ValueError('Exact native integer domain required')


def _hex(value, maximum, prefix=''):
    if (type(value) is not str or not value.startswith(prefix)
            or not 2<=len(value)-len(prefix)<=2*maximum
            or (len(value)-len(prefix))%2
            or re.fullmatch('[0-9a-f]+',value[len(prefix):]) is None):
        raise ValueError('Bounded native hexadecimal bytes required')
    return bytes.fromhex(value[len(prefix):])


def _native_rows(raw):
    if type(raw) is not bytes or not 1<=len(raw)<=32768:
        raise ValueError('Bounded original native metadata bytes required')
    def pairs(items):
        result={}
        for key,value in items:
            if '\0' in key:raise ValueError('Native metadata text key required')
            try:key.encode('utf8')
            except UnicodeError as error:raise ValueError('Native metadata scalar key required') from error
            if key in result:raise ValueError('Duplicate native metadata key')
            result[key]=value
        return result
    def noninteger(value):raise ValueError('Native metadata fractional number unavailable')
    try:
        value=json.loads(raw.decode('utf8'),object_pairs_hook=pairs,parse_float=noninteger,parse_constant=noninteger)
    except (UnicodeError,RecursionError) as error:
        raise ValueError('Bounded scalar native metadata required') from error
    pending=[(value,0)];count=0
    while pending:
        item,depth=pending.pop();count+=1
        if depth>32 or count>4096:raise ValueError('Native metadata tree capacity')
        if type(item) in (dict,list):
            children=item.values() if type(item) is dict else item
            pending.extend((child,depth+1) for child in children)
        elif type(item) is str:
            if '\0' in item:raise ValueError('Native metadata text required')
            try:item.encode('utf8')
            except UnicodeError as error:raise ValueError('Native metadata scalar required') from error
        elif item is not None and type(item) not in (bool,int):
            raise ValueError('Native metadata scalar type')
    return value


def validate_configured_context(encoded, raw, writer, ordinal):
    if type(raw) is not bytes or not 1<=len(raw)<=4096:
        raise ValueError('Bounded original configured context bytes required')
    context=decode_acceptance_json(raw)
    _closed(context,'interfaceVersion xid ordinal sessionUser actingUser database backendPid actorRoleOid sessionRoleOid assertedOriginUtf8Hex assertedOriginCaptureProfileHex installationId sourceEpoch targetIncarnation sourceEpochProfileHex sourceEpochEvidenceHex')
    if any(type(value) is not str for value in context.values()):
        raise ValueError('Original configured string context required')
    selection=decode_acceptance_json(encoded.original_configuration)
    _closed(selection,'installation sourceEpoch incarnation captureProfileHex configurationProfileHex originHex')
    expected={'interfaceVersion':'truss-native-operation-context/0.4','xid':writer,'ordinal':ordinal,
        'installationId':selection['installation'],'sourceEpoch':selection['sourceEpoch'],
        'targetIncarnation':selection['incarnation'],'assertedOriginUtf8Hex':selection['originHex'],
        'assertedOriginCaptureProfileHex':selection['captureProfileHex']}
    if any(context[key]!=value for key,value in expected.items()):
        raise ValueError('Original configured context selection correspondence required')
    for key in ('sessionUser','actingUser','database'):
        if not context[key] or '\0' in context[key]:raise ValueError('Original native actor required')
    for key in ('backendPid','actorRoleOid','sessionRoleOid'):
        value=context[key]
        maximum=2147483647 if key=='backendPid' else 4294967295
        if re.fullmatch('[1-9][0-9]{0,9}',value) is None or int(value)>maximum:
            raise ValueError('Original native identifier domain required')
    _hex(context['sourceEpochProfileHex'],65536)
    _hex(context['sourceEpochEvidenceHex'],1048576)
    return context,selection


def validate_configured_metadata(encoded, raw_context, writer, ordinal, raw_metadata):
    context,selection=validate_configured_context(encoded,raw_context,writer,ordinal)
    value=_closed(_native_rows(raw_metadata),'interfaceVersion marker pointer epoch configuration admission releaseArchive')
    if value['interfaceVersion']!='truss-catalog-metadata-cut/0.1':raise ValueError('Selected metadata interface required')
    marker=_closed(value['marker'],'singleton_id marker_interface_version installation_id layout_version bundle_sha256 inventory_profile inventory_sha256 database_identity schema_name installed_at installed_at_text')
    _integer(marker['singleton_id'],1,1)
    if (marker['installation_id']!=selection['installation'] or marker['schema_name']!='truss'
            or marker['marker_interface_version']!='truss-bootstrap-marker/0.1.0'):
        raise ValueError('Original marker correspondence required')
    for key in ('bundle_sha256','inventory_sha256'):
        if len(_hex(marker[key],32,'\\x'))!=32:raise ValueError('Native marker digest required')
    for key in ('layout_version','inventory_profile','database_identity','installed_at','installed_at_text'):
        if type(marker[key]) is not str or not marker[key]:raise ValueError('Original marker scalar required')
    pointer=_closed(value['pointer'],'singleton_id installation_id source_epoch')
    _integer(pointer['singleton_id'],1,1)
    epoch=_closed(value['epoch'],'installation_id source_epoch target_incarnation predecessor_epoch transition_reason profile_bytes evidence_bytes evidence_sha256')
    capsule=_closed(value['configuration'],'original_writer_xid operation_ordinal installation_id source_epoch target_incarnation configuration_generation key_reuse journal_mode original_context_sha256 admission_profile_bytes configuration_bytes selected_binding_bytes installed_inventory_bytes configuration_sha256 selected_binding_sha256 installed_inventory_sha256')
    admission=_closed(value['admission'],'head_id installation_id_utf8 source_epoch_utf8 configuration_generation key_reuse journal_mode configuration_bytes selected_binding_bytes installed_inventory_bytes configuration_sha256 selected_binding_sha256 installed_inventory_sha256')
    for row in (pointer,epoch,capsule):
        if row['installation_id']!=selection['installation'] or row['source_epoch']!=selection['sourceEpoch']:
            raise ValueError('Original metadata installation/epoch correspondence required')
    for row in (epoch,capsule):
        if row['target_incarnation']!=selection['incarnation']:raise ValueError('Original incarnation correspondence required')
    if epoch['transition_reason']=='initial':
        if epoch['predecessor_epoch'] is not None:raise ValueError('Initial epoch predecessor')
    elif epoch['transition_reason']=='restore':
        if type(epoch['predecessor_epoch']) is not str or not epoch['predecessor_epoch'] or epoch['predecessor_epoch']==epoch['source_epoch']:
            raise ValueError('Restore epoch predecessor')
    else:raise ValueError('Selected epoch transition required')
    if (_hex(epoch['profile_bytes'],65536,'\\x').hex()!=context['sourceEpochProfileHex']
            or _hex(epoch['evidence_bytes'],1048576,'\\x').hex()!=context['sourceEpochEvidenceHex']
            or _hex(epoch['evidence_sha256'],32,'\\x')!=sha256(bytes.fromhex(context['sourceEpochEvidenceHex'])).digest()):
        raise ValueError('Original epoch byte correspondence required')
    _integer(capsule['operation_ordinal']);_integer(capsule['configuration_generation'])
    _integer(admission['head_id'],1,1);_integer(admission['configuration_generation'])
    if (capsule['original_writer_xid']!=writer or str(capsule['operation_ordinal'])!=ordinal
            or _hex(capsule['original_context_sha256'],32,'\\x')!=sha256(raw_context).digest()
            or _hex(capsule['admission_profile_bytes'],65536,'\\x').hex()!=selection['configurationProfileHex']
            or _hex(admission['installation_id_utf8'],1024,'\\x').decode('utf8')!=selection['installation']
            or _hex(admission['source_epoch_utf8'],256,'\\x').decode('utf8')!=selection['sourceEpoch']):
        raise ValueError('Original configuration context correspondence required')
    for key,choices in (('key_reuse',('forbid','allow')),('journal_mode',('engine','trigger'))):
        if capsule[key] not in choices or admission[key]!=capsule[key]:raise ValueError('Original configuration mode correspondence')
    if admission['configuration_generation']!=capsule['configuration_generation']:raise ValueError('Original configuration generation correspondence')
    for stem in ('configuration','selected_binding','installed_inventory'):
        original=_hex(capsule[stem+'_bytes'],16777216,'\\x')
        if (admission[stem+'_bytes']!=capsule[stem+'_bytes'] or admission[stem+'_sha256']!=capsule[stem+'_sha256']
                or _hex(capsule[stem+'_sha256'],32,'\\x')!=sha256(original).digest()):
            raise ValueError('Original configuration artifact correspondence required')
    release=files('truss').joinpath('_profiles/catalog-report-release.json').read_bytes()
    profile=files('truss').joinpath('_profiles/catalog-report-configuration.json').read_bytes()
    if bytes.fromhex(selection['configurationProfileHex'])!=profile:raise ValueError('Selected original configuration profile required')
    config=_closed(decode_acceptance_json(_hex(capsule['configuration_bytes'],16777216,'\\x')),'interfaceVersion catalogReportRelease')
    selected=_closed(config['catalogReportRelease'],'artifactIdentity sha256')
    identity='truss.catalog-report-release/0.1.0'
    if (config['interfaceVersion']!='truss-catalog-report-configuration/0.1'
            or selected!={'artifactIdentity':identity,'sha256':sha256(release).hexdigest()}):
        raise ValueError('Original release selection required')
    archive=value['releaseArchive']
    if type(archive) is not list or len(archive)!=1:raise ValueError('Sole original release archive required')
    row=_closed(archive[0],'archive_row_id installation_id artifact_role artifact_identity artifact_bytes artifact_sha256 artifact_identity_sha256')
    _integer(row['archive_row_id'],1)
    if (row['installation_id']!=selection['installation'] or row['artifact_role']!='input'
            or row['artifact_identity']!=identity or _hex(row['artifact_bytes'],16777216,'\\x')!=release
            or _hex(row['artifact_sha256'],32,'\\x')!=sha256(release).digest()
            or _hex(row['artifact_identity_sha256'],32,'\\x')!=sha256(identity.encode()).digest()):
        raise ValueError('Original release archive correspondence required')
    return raw_metadata


def require_compact_metadata_correspondence(raw_metadata, compact):
    """Compare already validated full rows to the compact configured source."""
    rows=_native_rows(raw_metadata);capsule=rows['configuration'];epoch=rows['epoch']
    if epoch['transition_reason']!='initial' or epoch['predecessor_epoch'] is not None:
        raise ValueError('Original strict first-installation epoch required')
    expected={'installationId':capsule['installation_id'],'sourceEpoch':capsule['source_epoch'],
        'targetIncarnation':capsule['target_incarnation'],
        'configurationGeneration':str(capsule['configuration_generation']),
        'contextSha256':_hex(capsule['original_context_sha256'],32,'\\x').hex(),
        'epochProfileSha256':sha256(_hex(epoch['profile_bytes'],65536,'\\x')).hexdigest(),
        'epochEvidenceSha256':sha256(_hex(epoch['evidence_bytes'],1048576,'\\x')).hexdigest()}
    for key,stem in (('configurationSha256','configuration'),('selectedBindingSha256','selected_binding'),
                     ('installedInventorySha256','installed_inventory')):
        expected[key]=_hex(capsule[stem+'_sha256'],32,'\\x').hex()
    if any(compact.get(k)!=v for k,v in expected.items()):
        raise ValueError('Original full and compact metadata correspondence required')
