"""Per-use private native staging and actual statement/result custody."""
from hashlib import sha256
import json
import re
from uuid import uuid4
from psycopg import sql, RawCursor
from psycopg.rows import tuple_row
from ._current_query_evaluation import wire, ref, identity, CurrentQueryLimit
from ._owner_evidence_json import decode_owner_evidence_json
from .query import QueryRows


def _domain(modules,field):
    found=[]
    for module in modules:
        if module['pin']['documentId']!=field['documentId']:continue
        document=json.loads(module['documentJson'])
        for selected in document['modules']:
            if selected['id']!=field['moduleId']:continue
            found.extend((module['pin'],e) for e in selected['elements'] if e['id']==field['elementId'] and e['kind']=='field')
    if len(found)!=1:raise ValueError('Exact effective Field domain required')
    pin,element=found[0]
    facets=element.get('facets',{})
    if element['scalarType']=='string' and facets=={}:family='string'
    elif element['scalarType']=='integer' and facets=={'integerWidth':{'bits':64,'signed':True}}:family='integer'
    else:raise ValueError('Initial native query domain requires String or explicit signed64')
    if element['cardinality']!='one' or element['nullability']!='required':
        raise ValueError('Initial native query domain requires present singular values')
    return ({'documentId':field['documentId'],'revision':pin['revision'],'module':field['moduleId'],'element':field['elementId']},family)


def _literal(value,family):
    name='string' if family=='string' else 'integerToken'
    if type(value) is not dict or set(value)!={name} or type(value[name]) is not str:
        raise ValueError('Exact effective native query value required')
    raw=value[name]
    if '\0' in raw or len(raw.encode())>1048576:raise ValueError('Bounded native query scalar required')
    if family=='string':return raw
    if re.fullmatch('-?(0|[1-9][0-9]*)',raw) is None or not -(2**63)<=int(raw)<2**63:
        raise ValueError('Exact signed64 native query value required')
    return int(raw)


def _empty_projection(packet,evaluated,scan,field):
    """Use original projection metadata only from genuine compiled uses."""
    projections=[]
    for index,route in enumerate(packet['routes']):
        if route['scan']!=scan or route['field']!=field:continue
        result=evaluated['routeResults'][index]['result']
        if result['status']!='evaluated' or result['authority'] is not False or result['plan']['use']!=route:
            raise ValueError('Original empty projection route correspondence required')
        branches=result['plan']['branches']
        if not branches:raise ValueError('Nonempty possible projection branches required')
        for branch in branches:
            projection=branch['projection']
            if projection['kind'] not in ('original','transformed') or 'field' not in projection:
                raise ValueError('Exact admitted empty projection domain required')
            projections.append((projection['field'],projection['kind']))
    if not projections or len({identity(p) for p in projections})!=1:
        raise ValueError('Uniform genuine empty projection metadata required')
    return projections[0]


def stage_and_execute(cursor,captured,evaluation,*,maximum_rows,maximum_scan_rows,maximum_bytes):
    native,current,packet,designation,evaluated,owner,modules=evaluation
    facts=json.loads(captured.facts_bytes)
    outcomes={op['id']:op['outcome'] for op in evaluated['batch']['operations']}
    tables=[];scans=[];bindings=[];stage_maps={};total=0;private_bytes=0;admitted_count=0
    for scan in packet['scans']:
        scan_id=scan['scan'];population=[f for f in facts if f['type']==scan['type']]
        rules=outcomes[scan_id+'-rules'];cells=outcomes[scan_id+'-cells']
        expected=[{'type':f['type'],'key':f['key']} for f in population]
        if (rules['status']!='evaluated' or rules['authority'] is not False or cells['status']!='rendered'
                or cells['authority'] is not False or [r['resource'] for r in rules['rows']]!=expected
                or any(r['decision'] not in ('permit','deny') for r in rules['rows'])):
            raise ValueError('Complete determinate original read decisions required')
        eligible=[(n,f) for n,(f,r) in enumerate(zip(population,rules['rows'],strict=True)) if r['decision']=='permit']
        if len(cells['rows'])!=len(eligible):raise ValueError('Exact rendered/eligible population required')
        admitted_count+=len(eligible)
        if admitted_count>maximum_scan_rows:raise CurrentQueryLimit('Admitted source scan limit exceeded')
        rendered={n:{identity(c['field']):c for c in row} for (n,_),row in zip(eligible,cells['rows'],strict=True)}
        if any(len(rendered[n])!=len(row) for (n,_),row in zip(eligible,cells['rows'],strict=True)):
            raise ValueError('Distinct original rendered Fields required')
        selected=[]
        for projection in packet['projections']:
            if projection['scan']==scan_id:selected.append((projection['path'],ref(projection['field']),None,None))
        for n,route in enumerate(packet['routes']):
            if route['scan']!=scan_id:continue
            result=evaluated['routeResults'][n]['result']
            if (result['status']!='evaluated' or result['authority'] is not False or result['plan']['use']!=route
                    or [r['resource'] for r in result['rows']]!=expected):
                raise ValueError('Complete original route/resource correspondence required')
            use=next(u for u in designation['uses'] if (u['scan'],u['path'])==(scan_id,route['path']))
            signatures=[]
            for index,(rule,row) in enumerate(zip(rules['rows'],result['rows'],strict=True)):
                if row['readDecision']!=rule['decision']:raise ValueError('Original route/read correspondence required')
                if rule['decision']=='deny':
                    if row['selection']!='read-denied' or row['activeBranches']:raise ValueError('Denied route must remain inactive')
                    continue
                if row['selection']!='selected' or not row['activeBranches']:raise ValueError('Determinate original route selection required')
                branches=[b for b in result['plan']['branches'] if b['index'] in row['activeBranches']]
                if len(branches)!=len(row['activeBranches']):raise ValueError('Complete active route branches required')
                for branch in branches:
                    if branch['status'] not in ('requires-original-action','compatible-disclosed-properties'):
                        raise ValueError('Original route properties refused')
                    signatures.append((branch['status'],identity(branch['queryValue']),identity(branch['constraints'])))
            if not eligible:
                for branch in result['plan']['branches']:
                    if branch['status'] not in ('requires-original-action','compatible-disclosed-properties'):
                        raise ValueError('Original possible route properties refused')
                    signatures.append((branch['status'],identity(branch['queryValue']),identity(branch['constraints'])))
            if not signatures or len(set(signatures))!=1:raise ValueError('Uniform effective per-use route domain required')
            mode='original-authorized' if signatures[0][0]=='requires-original-action' else 'disclosed'
            storage=[s for s in owner['storage'] if s['type']==scan['type'] and s['field']==route['field']]
            if len(storage)!=1 or storage[0]['storageEffect']!='canonical':
                raise ValueError('Stored-transformed query uses require genuine paired runtime provenance')
            if mode=='original-authorized':
                if use['originalAction'] is None:raise ValueError('Original separate action designation required')
                action=outcomes['action'+str(n)]
                if (action['status']!='evaluated' or action['authority'] is not False or len(action['rows'])!=len(population)
                        or any(r['decision'] not in ('permit','deny') for r in action['rows'])
                        or any(action['rows'][index]['decision']!='permit' for index,_ in eligible)):
                    raise ValueError('Separate current original-value action refused')
            else:
                # No keyed/vault/opaque comparison scope is invented from a
                # domain hash. The initial disclosed transform is a pure
                # constant mask; other transformations await real scope input.
                for branch in result['plan']['branches']:
                    if eligible and branch['index'] not in {i for row in result['rows'] for i in row['activeBranches']}:continue
                    disposition=branch['representativeDisposition']
                    if disposition['kind']=='transformed':
                        transforms=[t['declaration'] for t in result['plan']['transforms'] if
                            t['declaration']['id']==disposition.get('transform') and t['declaration']['version']==disposition.get('version')]
                        if len(transforms)!=1 or transforms[0].get('function')!='constant' or transforms[0].get('kind')!='mask':
                            raise ValueError('Disclosed transform requires qualified runtime comparison scope')
            selected.append((route['path'],route['field'],mode,use['originalAction'] if mode=='original-authorized' else None))
        columns=[];values_by_row={n:{} for n,_ in eligible}
        for path,field,mode,action in selected:
            observations=[]
            for index,fact in eligible:
                if mode=='original-authorized':
                    values=[v['value'] for v in fact['fields'] if v['field']==field]
                    if len(values)!=1:raise ValueError('Present original per-use value required')
                    effective=field;value=values[0];exposure=None
                else:
                    cell=rendered[index].get(identity(field))
                    if cell is None or cell['disposition'] not in ('original','transformed'):
                        raise ValueError('Present admitted disclosure required')
                    effective=cell.get('outputType',field);value=cell['value'];exposure=cell['disposition']
                domain,family=_domain(modules,effective)
                observations.append((domain,family,exposure,_literal(value,family)))
            if not eligible:
                if mode=='original-authorized':
                    effective=field;exposure=None
                else:
                    effective,exposure=_empty_projection(packet,evaluated,scan_id,field)
                if mode=='disclosed':
                    routes=[evaluated['routeResults'][i]['result']['plan'] for i,r in enumerate(packet['routes'])
                            if r['scan']==scan_id and r['path']==path]
                    if len(routes)!=1 or any(b['queryValue']['field']!=effective or
                            b['queryValue']['origin'] not in ('live-field','read-transform-output') for b in routes[0]['branches']):
                        raise ValueError('Exact empty disclosed operand domain required')
                domain,family=_domain(modules,effective)
                observations=[(domain,family,None if mode=='original-authorized' else exposure,None)]
            if len({identity([d,f,e]) for d,f,e,_ in observations})!=1:
                raise ValueError('Uniform effective native query domain required')
            domain,family,exposure,_=observations[0];column='value_'+str(len(columns));columns.append((column,family))
            scope=sha256(wire({'inventory':captured.sources.inventory_digest,'domain':domain})).hexdigest()
            bindings.append({'path':path,'scan':scan_id,'field':next(p['field'] for p in packet['projections'] if p['path']==path) if mode is None else next(x['input']['identity'] for op in packet['operations'] for x in op['operands'] if x['path']==path),
                             'column':column,'domain':domain,'comparisonScope':scope,'mode':mode,
                             'originalAction':action,'exposure':exposure if mode is None else None})
            for (index,_),(_,_,_,value) in zip(eligible,observations if eligible else (),strict=True):values_by_row[index][column]=value
        name='truss_current_'+uuid4().hex
        definitions=[sql.SQL('eligible boolean NOT NULL'),sql.SQL('private_key text COLLATE "C" NOT NULL UNIQUE')]
        definitions.extend(sql.SQL('{} {} NOT NULL').format(sql.Identifier(c),sql.SQL('text COLLATE "C"' if f=='string' else 'bigint')) for c,f in columns)
        cursor.execute(sql.SQL('CREATE TEMP TABLE {} ({}) ON COMMIT DROP').format(sql.Identifier(name),sql.SQL(',').join(definitions)),prepare=False)
        table=cursor.execute('SELECT n.nspname::text,c.oid::text,c.relowner::text FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace WHERE c.oid=pg_catalog.to_regclass(%s)',('pg_temp.'+name,),prepare=False).fetchone()
        if table is None:raise ValueError('Actual private staging relation required')
        properties=cursor.execute("SELECT c.relkind::text,c.relpersistence::text,c.relrowsecurity,c.relforcerowsecurity,c.relowner=(SELECT oid FROM pg_catalog.pg_roles WHERE rolname=CURRENT_USER),NOT EXISTS(SELECT 1 FROM pg_catalog.aclexplode(coalesce(c.relacl,pg_catalog.acldefault('r',c.relowner))) a WHERE a.grantee<>c.relowner OR a.grantor<>c.relowner OR a.is_grantable),NOT EXISTS(SELECT 1 FROM pg_catalog.pg_inherits i WHERE i.inhrelid=c.oid OR i.inhparent=c.oid) FROM pg_catalog.pg_class c WHERE c.oid=%s::oid",(table[1],),prepare=False).fetchone()
        if properties!=('r','t',False,False,True,True,True):raise ValueError('Private ordinary native staging home required')
        attributes=cursor.execute("SELECT attname::text,atttypid::int,attnotnull,attcollation::int,attidentity::text,attgenerated::text,atthasdef,attacl IS NULL FROM pg_catalog.pg_attribute WHERE attrelid=%s::oid AND attnum>0 AND NOT attisdropped ORDER BY attnum",(table[1],),prepare=False).fetchall()
        collation=cursor.execute("SELECT 'pg_catalog.\"C\"'::pg_catalog.regcollation::oid::int",prepare=False).fetchone()[0]
        expected_attributes=[('eligible',16,True,0,'','',False,True),('private_key',25,True,collation,'','',False,True)]
        expected_attributes.extend((column,25 if family=='string' else 20,True,collation if family=='string' else 0,'','',False,True) for column,family in columns)
        if attributes!=expected_attributes:raise ValueError('Exact private scalar staging descriptors required')
        schema=table[0];tables.append((schema,name,table))
        stage_maps[scan_id]={}
        for index,fact in eligible:
            key=uuid4().hex
            values=values_by_row[index];stage_maps[scan_id][key]=values
            cursor.execute(sql.SQL('INSERT INTO {}.{} VALUES ({})').format(sql.Identifier(schema),sql.Identifier(name),sql.SQL(',').join(sql.Placeholder() for _ in range(2+len(columns)))),
                           (True,key,*(values[c] for c,_ in columns)),prepare=False)
        scans.append({'scan':scan_id,'target':scan['record'],'relation':{'schema':schema,'table':name,'eligibleColumn':'eligible','rowKeyColumn':'private_key'}})
    binding={'version':'weft.postgresql.current-values/0.2-candidate','sourceRequestSha256':packet['sourceRequestSha256'],
             'designationSha256':packet['designationSha256'],'sourceBindingSha256':packet['binding']['sha256'],'scans':scans,'values':bindings}
    cursor._deadline.check()
    compiled=decode_owner_evidence_json(native.CurrentQueryPreparation.lower_postgresql_current_rows_candidate_json(current,wire(binding).decode()).encode())
    cursor._deadline.check()
    if (compiled['securityReady'] is not False or compiled['authority'] is not False or compiled['nativeAdmission']!='required'
            or compiled['sourceRequestSha256']!=packet['sourceRequestSha256']
            or compiled['designationSha256']!=packet['designationSha256']
            or compiled['materializationBindingSha256']!=sha256(wire(binding)).hexdigest()):
        raise ValueError('Original native statement/binding correspondence required')
    descriptors=compiled['resultColumns'];width=len(descriptors);scan_ids=[s['scan'] for s in packet['scans']]
    private=compiled['privateResultColumns']
    if (len(private)!=1 or private[0]['position']!=width or private[0]['scans']!=scan_ids
            or private[0]['name']!='__weft_source_rows' or private[0]['purpose']!='source-row-contribution'
            or private[0]['encoding']!='jsonb-text:weft.stage-row-tuple/0.1-candidate' or private[0]['maxKeyUtf8Bytes']!=256):
        raise ValueError('Complete original private contribution descriptor required')
    for ordinal,parameter in enumerate(compiled['parameters'],1):
        logical=parameter['logicalType'];family=logical['family']
        if (parameter['ordinal']!=ordinal or family not in ('string','integer')
                or parameter['nativeType']!=('text' if family=='string' else 'int8')
                or logical!={'family':family,'nullable':False,'facets':{} if family=='string' else {'integerWidth':{'bits':64,'signed':True}}}):
            raise ValueError('Exact original native parameter descriptor required')
        _literal({'string' if family=='string' else 'integerToken':parameter['value']},family)
    output_bindings=[]
    if len(compiled['publicCellSources'])!=width:raise ValueError('Complete public cell correspondence required')
    for position,(descriptor,cell) in enumerate(zip(descriptors,compiled['publicCellSources'],strict=True)):
        candidates=[v for v in bindings if v['path']==cell['sourcePath'] and v['scan']==cell['scan'] and v['mode'] is None]
        if (len(candidates)!=1 or cell['position']!=position or descriptor['position']!=position
                or candidates[0]['field']!=cell['field'] or candidates[0]['domain']!=descriptor['effectiveDomain']):
            raise ValueError('Original output cell/domain correspondence required')
        candidate=candidates[0]
        domain=candidate['domain']
        _,family=_domain(modules,{'documentId':domain['documentId'],'moduleId':domain['module'],'elementId':domain['element']})
        if (descriptor['encoding']!='native-text-exact-required' or descriptor['exposure']!=candidate['exposure']
                or descriptor['logicalType']!={'family':family,'nullable':False,'facets':{} if family=='string' else {'integerWidth':{'bits':64,'signed':True}}}):
            raise ValueError('Exact effective output scalar descriptor required')
        output_bindings.append((cell,candidate))
    rows=[]
    with RawCursor(cursor.connection,row_factory=tuple_row) as raw:
        from .catalog_runtime import _pin_cursor
        _pin_cursor(raw)
        cursor._deadline.check()
        raw.execute(compiled['sql'],[p['value'] for p in compiled['parameters']] or None,prepare=False)
        cursor._deadline.check()
        if (raw.description is None or [d.type_code for d in raw.description]!=[25]*(width+1)
                or [d.name for d in raw.description]!=['output_'+str(n) for n in range(width)]+['__weft_source_rows']):
            raise ValueError('Exact text statement result descriptors required')
        result=raw.fetchmany(maximum_rows+1)
        cursor._deadline.check()
        if len(result)>maximum_rows:raise CurrentQueryLimit('Complete guarded query row limit exceeded')
        for row in result:
            if len(row)!=width+1 or any(type(v) is not str for v in row):raise ValueError('Exact nonnull native query carriers required')
            # The caller's public budget must not depend on private contributor
            # identities or a denied object's position in the native census.
            total+=sum(len(v.encode()) for v in row[:width])
            if total>maximum_bytes:raise CurrentQueryLimit('Complete guarded query byte limit exceeded')
            private_bytes+=len(row[-1].encode())
            if private_bytes>16777216:raise CurrentQueryLimit('Private contribution carrier limit exceeded')
            carrier=decode_owner_evidence_json(row[-1].encode())
            if (type(carrier) is not dict or set(carrier)!={'version','rows'} or carrier['version']!='weft.stage-row-tuple/0.1-candidate'
                    or [r['scan'] for r in carrier['rows']]!=scan_ids):
                raise ValueError('Complete private source-row contribution required')
            keys={}
            for contribution in carrier['rows']:
                if set(contribution)!={'scan','key'} or type(contribution['key']) is not str or len(contribution['key'].encode())>256:
                    raise ValueError('Exact private source-row identity required')
                keys[contribution['scan']]=contribution['key']
                if contribution['key'] not in stage_maps[contribution['scan']]:raise ValueError('Unknown private contributor')
            decoded=[]
            for value,(cell,candidate) in zip(row[:width],output_bindings,strict=True):
                expected=stage_maps[cell['scan']][keys[cell['scan']]][candidate['column']]
                if value!=str(expected):raise ValueError('Native output cell differs from held disclosed value')
                decoded.append(expected)
            rows.append(tuple(decoded))
    for schema,name,table in tables:
        observed=cursor.execute('SELECT n.nspname::text,c.oid::text,c.relowner::text FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace WHERE c.oid=pg_catalog.to_regclass(%s)',(schema+'.'+name,),prepare=False).fetchone()
        if observed!=table:raise ValueError('Original private relation changed')
        cursor.execute(sql.SQL('DROP TABLE {}.{}').format(sql.Identifier(schema),sql.Identifier(name)),prepare=False)
    return QueryRows(tuple(d['name'] for d in descriptors),tuple(rows),int(captured.sources.accepted_revision))
