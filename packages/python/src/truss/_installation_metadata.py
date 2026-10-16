"""Rollback-only candidate metadata effects. No installed authority or commit."""
from hashlib import sha256
from importlib.resources import files
import json
import uuid
from ._installation_archive import COLUMNS,compare_archive_rows

PROFILE_SHA256='4220b0f9f0ee565dc898ba8e54d4b5488c9f5bf1686371145ef2f46c9cde9df3'

def _json(value):return json.dumps(value,ensure_ascii=False,separators=(',',':'),sort_keys=True).encode()
def _bytes(value):return "pg_catalog.decode('"+value.hex()+"','hex')"
def _text(value):return 'pg_catalog.convert_from('+_bytes(value.encode())+",'UTF8')"
def _observe(connection,sql,maximum=6291456):
    rows=connection.run(sql)
    if type(rows) is not list or len(rows)!=1 or len(rows[0])!=1 or type(rows[0][0]) is not str:
        raise ValueError('Original complete metadata observation required')
    raw=rows[0][0].encode()
    if len(raw)>maximum:raise ValueError('Metadata readback retention bound exceeded')
    return raw

def prepare_metadata(target):
    profile_bytes=files('truss').joinpath('_profiles/installation-metadata-construction.json').read_bytes()
    if sha256(profile_bytes).hexdigest()!=PROFILE_SHA256:raise ValueError('Original metadata recipe required')
    profile=json.loads(profile_bytes)
    for name,source in profile['sources'].items():
        if sha256(source.encode()).hexdigest()!=profile['sourceSha256'][name]:
            raise ValueError('Original metadata producer source required')
    recipe=_json({'profileBytesHex':profile_bytes.hex(),
        'producerSourceHex':files('truss').joinpath('_installation_metadata.py').read_bytes().hex()})
    original_input=_json({'scope':profile['scope'],'recipeSha256':sha256(recipe).hexdigest(),
        'originalTarget':json.loads(target),'ordinaryCalls':'160',
        'maximumArtifactBytes':'1048576','maximumAggregateBytes':'3145728',
        'deploymentIdentityQualified':False,'installedInventoryQualified':False})
    return recipe,original_input

def validate_metadata_preflight(original):
    recipe,input_bytes=prepare_metadata(original.target)
    if recipe!=original.metadata_recipe or input_bytes!=original.metadata_input:
        raise ValueError('Original retained metadata recipe/input required')
    known=(original.statements,original.definition_baseline,input_bytes)
    if any(not raw or len(raw)>1048576 for raw in known) or sum(map(len,known))+1048576+4096>3145728:
        raise ValueError('Complete candidate metadata artifact reservation required')
    if original.ordinary_call_limit!=160:
        raise ValueError('Original metadata call reservation required')

def execute_metadata(connection,original,definition_observed,attempt):
    validate_metadata_preflight(original)
    recipe,input_bytes=prepare_metadata(original.target)
    if recipe!=original.metadata_recipe or input_bytes!=original.metadata_input:
        raise ValueError('Original retained metadata recipe/input required')
    profile=json.loads(bytes.fromhex(json.loads(recipe)['profileBytesHex']))
    # These are complete candidate role artifacts, not a qualified BootstrapBundle.
    artifacts=[('bundle','candidate:owner-statements',original.statements),
        ('expected_inventory','candidate:definition-baseline',original.definition_baseline),
        ('installed_inventory','candidate:definition-observation',definition_observed),
        ('input','candidate:construction-input',input_bytes)]
    if any(not raw or len(raw)>1048576 for _,_,raw in artifacts) or sum(len(raw) for _,_,raw in artifacts)>3145728-4096:
        raise ValueError('Complete candidate metadata artifact bound required')
    empty=_observe(connection,"SELECT pg_catalog.jsonb_build_array((SELECT count(*)::text FROM truss.installation_marker),(SELECT count(*)::text FROM truss.installation_archive),(SELECT count(*)::text FROM truss.source_epoch_registry),(SELECT count(*)::text FROM truss.source_epoch_current))::text")
    if json.loads(empty)!=['0']*4:raise ValueError('Fresh metadata and operation scope required')
    captured=_observe(connection,"""WITH native_original AS MATERIALIZED (
 SELECT pg_catalog.gen_random_uuid()::text AS identity,pg_catalog.clock_timestamp() AS at)
 SELECT pg_catalog.jsonb_build_object('installationId',o.identity,
 'clockText',pg_catalog.to_char(o.at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
 'clockParity',o.at=pg_catalog.to_char(o.at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"')::timestamptz,
 'databaseName',pg_catalog.current_database(),'databaseOid',(SELECT oid::text FROM pg_catalog.pg_database WHERE datname=pg_catalog.current_database()),
 'schemaName',n.nspname,'schemaOid',n.oid::text)::text
 FROM native_original o CROSS JOIN pg_catalog.pg_namespace n WHERE n.nspname='truss'""",4096)
    attempt['metadata_capture']=captured
    capture=json.loads(captured)
    if uuid.UUID(capture['installationId']).version!=4 or capture['clockParity'] is not True:
        raise ValueError('Original native UUID/clock correspondence required')
    target=json.loads(original.target)
    if capture['databaseName']!=target['database'] or capture['databaseOid']!=target['databaseOid']:
        raise ValueError('Original native database observation required')
    database_identity=_json({'scope':'candidate_database_observation_only',
        'databaseName':capture['databaseName'],'databaseOid':capture['databaseOid']}).decode()
    incarnation=_json({'scope':'candidate_target_observation_only','databaseOid':capture['databaseOid'],
        'schemaOid':capture['schemaOid']}).decode()
    marker={'interfaceVersion':'truss-bootstrap-marker/0.1.0','installationId':capture['installationId'],
        'layoutVersion':'candidate-owner-statements','bundleSha256':sha256(original.statements).hexdigest(),
        'inventoryProfile':'candidate-definition-observation','inventorySha256':sha256(definition_observed).hexdigest(),
        'namespace':{'databaseIdentity':database_identity,'schemaName':capture['schemaName']},'installedAt':capture['clockText']}
    marker_bytes=_json(marker);attempt['metadata_marker_original']=marker_bytes
    artifacts.append(('marker','candidate:original-marker',marker_bytes))
    attempt['metadata_artifacts']=tuple(artifacts)
    installation=capture['installationId']
    for role,identity,raw in artifacts:
        sql=profile['sources']['archive']
        parameters=(_text(installation),_text(role),_text(identity),_text(raw.hex()))
        for index,value in enumerate(parameters,1):sql=sql.replace('$'+str(index),value)
        connection.run(sql)
    connection.run("INSERT INTO truss.installation_marker VALUES (1,'truss-bootstrap-marker/0.1.0',"+
        ','.join((_text(installation),_text(marker['layoutVersion']),_bytes(bytes.fromhex(marker['bundleSha256'])),
            _text(marker['inventoryProfile']),_bytes(bytes.fromhex(marker['inventorySha256'])),
            _text(database_identity),_text(capture['schemaName']),_text(capture['clockText'])+'::timestamptz',_text(capture['clockText'])))+')')
    connection.run(profile['sources']['epoch'])
    body=profile['sources']['epoch'].split('AS $$',1)[1].split('$$;',1)[0]
    helper=_observe(connection,"SELECT pg_catalog.jsonb_build_object('body',p.prosrc,'securityDefiner',p.prosecdef,'volatile',p.provolatile,'configuration',p.proconfig,'owner',p.proowner=(SELECT oid FROM pg_catalog.pg_roles WHERE rolname=current_user),'language',l.lanname,'result',p.prorettype::regtype::text,'arguments',pg_catalog.oidvectortypes(p.proargtypes))::text FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace JOIN pg_catalog.pg_language l ON l.oid=p.prolang WHERE n.nspname='truss' AND p.proname='runtime_issue_source_epoch'",65536)
    attempt['metadata_epoch_definition']=helper
    if json.loads(helper)!={'body':body,'securityDefiner':False,'volatile':'v','configuration':['search_path=pg_catalog, pg_temp'],'owner':True,'language':'plpgsql','result':'text','arguments':'text, text, text, bytea, bytea'}:
        raise ValueError('Separate original epoch helper definition required')
    epoch_profile=_json({'scope':'unqualified_candidate_epoch_construction','recipeSha256':PROFILE_SHA256})
    evidence=_json({'scope':'candidate_native_target_observation','originalCapture':capture,'constructionInputSha256':sha256(input_bytes).hexdigest()})
    epoch_raw=_observe(connection,'SELECT truss.runtime_issue_source_epoch('+','.join((_text(installation),'NULL',_text(incarnation),_bytes(epoch_profile),_bytes(evidence)))+')',256)
    attempt['metadata_epoch_original']=epoch_raw
    epoch=epoch_raw.decode()
    if uuid.UUID(epoch).version!=4:raise ValueError('Original native epoch UUID required')
    connection.run('SET CONSTRAINTS ALL IMMEDIATE')
    archive_raw=_observe(connection,"SELECT COALESCE(pg_catalog.jsonb_agg(pg_catalog.jsonb_build_array(archive_row_id::text,installation_id,artifact_role,artifact_identity,pg_catalog.encode(artifact_bytes,'hex'),pg_catalog.encode(artifact_sha256,'hex'),pg_catalog.encode(artifact_identity_sha256,'hex')) ORDER BY archive_row_id),'[]'::jsonb)::text FROM truss.installation_archive")
    attempt['metadata_archive_readback']=archive_raw
    rows=[(*row[:4],*(bytes.fromhex(cell) for cell in row[4:])) for row in json.loads(archive_raw)]
    if not compare_archive_rows(COLUMNS,rows,installation,tuple(artifacts),5,3145728).matches:
        raise ValueError('Complete original archive correspondence required')
    marker_raw=_observe(connection,"SELECT pg_catalog.jsonb_build_object('interfaceVersion',marker_interface_version,'installationId',installation_id,'layoutVersion',layout_version,'bundleSha256',pg_catalog.encode(bundle_sha256,'hex'),'inventoryProfile',inventory_profile,'inventorySha256',pg_catalog.encode(inventory_sha256,'hex'),'databaseIdentity',database_identity,'schemaName',schema_name,'installedAt',installed_at_text,'clockParity',installed_at=installed_at_text::timestamptz)::text FROM truss.installation_marker WHERE singleton_id=1",4096)
    attempt['metadata_marker_readback']=marker_raw
    projected=dict(marker);namespace=projected.pop('namespace')
    if json.loads(marker_raw)!={**projected,**namespace,'clockParity':True}:raise ValueError('Original marker/clock correspondence required')
    epoch_readback=_observe(connection,"SELECT pg_catalog.jsonb_build_object('registry',(SELECT pg_catalog.jsonb_agg(pg_catalog.jsonb_build_array(installation_id,source_epoch,target_incarnation,predecessor_epoch,transition_reason,pg_catalog.encode(profile_bytes,'hex'),pg_catalog.encode(evidence_bytes,'hex'),pg_catalog.encode(evidence_sha256,'hex'))) FROM truss.source_epoch_registry),'current',(SELECT pg_catalog.jsonb_agg(pg_catalog.jsonb_build_array(singleton_id::text,installation_id,source_epoch)) FROM truss.source_epoch_current))::text",16384)
    attempt['metadata_epoch_readback']=epoch_readback
    if json.loads(epoch_readback)!={'registry':[[installation,epoch,incarnation,None,'initial',epoch_profile.hex(),evidence.hex(),sha256(evidence).hexdigest()]],'current':[['1',installation,epoch]]}:
        raise ValueError('Original complete epoch correspondence required')
    return _json({'scope':'rollback_only_unqualified_metadata_round_trip','capture':capture,
        'marker':marker,'epoch':epoch,'archiveReadbackSha256':sha256(archive_raw).hexdigest(),
        'installationReady':False,'deploymentIdentityQualified':False})
