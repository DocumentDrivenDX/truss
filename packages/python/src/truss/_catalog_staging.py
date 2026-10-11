"""Private new-catalog staging and native correspondence; never acceptance.

Requires an already admitted original native catalog operation. No transaction
admission, commit, accepted report/head publication or ordinary-role grant.
"""
from dataclasses import dataclass
import json
from uuid import uuid4
from ._acceptance_json import decode_acceptance_json
from .preparation import PreparedAcceptance, _require_original_preparation

@dataclass(frozen=True, slots=True)
class ProvisionalCatalog:
    revision: str
    # Exact complete native inventories remain bytes, not mutable driver rows.
    inventory_bytes: bytes
    documents_bytes: bytes
    counts_bytes: bytes
    scope: str = 'verified_provisional_new_catalog_only'
    storage_interpretation: str = 'ADR-002-D4-absent-binding-json-default'

class CatalogStagingCleanupFailure(RuntimeError):
    """Primary failure retained; caller transaction containment is unconfirmed."""
    def __init__(self, primary, cleanup):
        super().__init__('Catalog staging failed; savepoint containment unconfirmed')
        self.primary_failure=primary
        self.cleanup_failure=cleanup
        self.containment_confirmed=False

def _json(value):
    return json.dumps(value,ensure_ascii=True,separators=(',',':'))

def _id(value):
    if type(value) is not str or not value.isascii() or not value.isdecimal() or not 1 <= int(value) <= 2147483647 or str(int(value)) != value:
        raise ValueError('Original native catalog ID required')
    return value

def stage_new_catalog(connection, prepared: PreparedAcceptance, *, origin_bytes: bytes):
    """Administrative native component on a caller transaction; binding absent only.

    The caller supplies a trusted pg8000 native-style port; host registration
    and connection coordination are external and are not verified by this helper.
    No caller-supplied identities or property-home overrides are accepted.
    ADR-002 D4 and the original catalog-default-homes route select JSON for
    every Field only when binding is explicitly absent; present binding refuses.
    This private origin carrier is strict numeric-free JSON; original UTF-8
    is passed unchanged. Numeric origin extensions require a later exact profile.
    """
    _require_original_preparation(prepared)
    choices=prepared.input()
    if choices['transforms'] or choices['binding'] != {'state':'absent'}:
        raise ValueError('Registered transform/binding interpretation required')
    if type(origin_bytes) is not bytes or len(origin_bytes)>1048576:
        raise ValueError('Bounded original origin bytes required')
    origin=decode_acceptance_json(origin_bytes)
    if type(origin) is not dict:
        raise ValueError('Original origin object required')
    declarations=json.loads(prepared.declarations_bytes)
    records=[r for d in declarations for r in d['records']]
    def rows(sql, **parameters):
        values=connection.run(sql,**parameters)
        names=[c['name'] for c in connection.columns]
        if len(names)!=len(set(names)):
            raise ValueError('Unique native result columns required')
        return [dict(zip(names,row,strict=True)) for row in values]
    savepoint='truss_catalog_'+uuid4().hex
    connection.run('SAVEPOINT '+savepoint)
    try:
        connection.run("SELECT truss.runtime_require_catalog_input(pg_catalog.decode(:input,'hex'))",input=prepared.input_bytes.hex())
        connection.run('SELECT truss.runtime_require_catalog_document_carrier(CAST(:documents AS pg_catalog.jsonb))',documents=prepared.archive_documents_bytes.decode())
        staged=rows('SELECT * FROM truss.runtime_stage_catalog_documents(CAST(:documents AS pg_catalog.jsonb),CAST(:origin AS pg_catalog.jsonb))',documents=prepared.archive_documents_bytes.decode(),origin=origin_bytes.decode("utf8"))
        if len(staged)!=1:raise ValueError('Original staged revision required')
        revision=_id(staged[0]['provisional_revision'])
        types=rows('SELECT * FROM truss.runtime_stage_new_types(CAST(:rev AS pg_catalog.int4),CAST(:records AS pg_catalog.jsonb))',rev=revision,records=_json([{k:r[k] for k in ('documentId','moduleId','elementId')} for r in records])) if records else []
        def type_id(record):
            matches=[r for r in types if (r['document_id'],r['module_id'],r['element_id'])==(record['documentId'],record['moduleId'],record['elementId'])]
            if len(matches)!=1:raise ValueError('Original allocated Record correspondence required')
            return _id(matches[0]['type_id'])
        fields=[{'ownerTypeId':type_id(record),'fieldModule':f['fieldModule'],'field':f['declaration'],'home':'json'} for record in records for f in record['fields']]
        properties=rows('SELECT * FROM truss.runtime_stage_new_properties(CAST(:rev AS pg_catalog.int4),CAST(:properties AS pg_catalog.jsonb))',rev=revision,properties=_json(fields)) if fields else []
        def property_id(owner,reference):
            matches=[r for r in properties if (r['owner_type_id'],r['field_module'],r['field_id'])==(owner,reference['module'],reference['element'])]
            if len(matches)!=1:raise ValueError('Original allocated Field correspondence required')
            return _id(matches[0]['property_id'])
        keys=[]
        for record in records:
            for key in record['keys']:
                if 'primary' in key and type(key['primary']) is not bool:
                    raise ValueError('Original Boolean primary marker required')
                keys.append({'ownerTypeId':type_id(record),'keyId':key['id'],'primary':key.get('primary') is True,'propertyIds':[property_id(type_id(record),ref) for ref in key['fields']]})
        if keys:rows('SELECT * FROM truss.runtime_stage_new_keys(CAST(:rev AS pg_catalog.int4),CAST(:keys AS pg_catalog.jsonb))',rev=revision,keys=_json(keys))
        for document in declarations:
            for relationship in document['relationships']:
                declaration=relationship['declaration']
                def endpoints(side):
                    return '{'+','.join(type_id({'documentId':relationship['documentId'],'moduleId':ref['module'],'elementId':ref['element']}) for ref in declaration[side])+'}'
                allocated=rows('SELECT truss.runtime_stage_new_relationship(CAST(:rev AS pg_catalog.int4),:doc,:module,CAST(:declaration AS pg_catalog.jsonb),CAST(:source AS pg_catalog.int4[]),CAST(:target AS pg_catalog.int4[])) AS relationship_id',rev=revision,doc=relationship['documentId'],module=relationship['moduleId'],declaration=_json(declaration),source=endpoints('source'),target=endpoints('target'))
                if len(allocated)!=1:raise ValueError('Original allocated relationship required')
                _id(allocated[0]['relationship_id'])
        connection.run('SELECT truss.runtime_verify_new_catalog_prestate(CAST(:rev AS pg_catalog.int4))',rev=revision)
        inventory=rows('SELECT family,identity::pg_catalog.text AS identity FROM truss.runtime_collect_new_catalog_inventory(CAST(:rev AS pg_catalog.int4))',rev=revision)
        documents=rows('SELECT * FROM truss.runtime_collect_report_documents(CAST(:rev AS pg_catalog.int4))',rev=revision)
        counts=rows('SELECT * FROM truss.runtime_collect_new_catalog_counts(CAST(:rev AS pg_catalog.int4))',rev=revision)
        if len(counts)!=1:raise ValueError('Original complete native counts required')
        homes=rows('SELECT prop_id::pg_catalog.text AS property_id,type_id::pg_catalog.text AS owner_type_id,home FROM truss.prop_def WHERE since_rev=CAST(:rev AS pg_catalog.int4)',rev=revision)
        expected={(r['property_id'],r['owner_type_id'],'json') for r in properties}
        actual=[(r['property_id'],r['owner_type_id'],r['home']) for r in homes]
        if len(actual)!=len(expected) or set(actual)!=expected:
            raise ValueError('Complete native JSON home correspondence required')
        connection.run('SELECT truss.edge_limit_verify_current_scope()')
        _require_original_preparation(prepared)
        result=ProvisionalCatalog(revision,_json(inventory).encode(),_json(documents).encode(),_json(counts[0]).encode())
        connection.run('RELEASE SAVEPOINT '+savepoint)
        return result
    except BaseException as primary:
        try:
            connection.run('ROLLBACK TO SAVEPOINT '+savepoint)
            connection.run('RELEASE SAVEPOINT '+savepoint)
        except BaseException as cleanup:
            raise CatalogStagingCleanupFailure(primary,cleanup) from primary
        raise
