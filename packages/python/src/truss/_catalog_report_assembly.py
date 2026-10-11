"""Original v0.3 field assembly. Missing authority never becomes report bytes."""
from hashlib import sha256
from importlib.resources import files
import json
from .preparation import _require_original_preparation
from ._catalog_support import evaluate_catalog_support
from ._catalog_report_semantics import compose_catalog_report_semantics, canonical_numeric_free
from ._canonical_wire_tree import prepare_canonical_wire_tree
from ._report_schema import validate_complete_report
from ._acceptance_json import decode_acceptance_json

FIELDS=('interfaceVersion','reportProfile','rev','originalExecution','acceptedInput',
    'umf','documents','diagnostics','documentInterpretations','counts','provisional',
    'rebinds','assertions','pending_indexes','losses','extensions',
    'transformRegistrations','lifecycleProfile','reactivations')
REQUIRED_SOURCES=('originalInstalledExecution','admittedLayout',
    'registeredEnforcementReportProfile','registeredAcceptanceReportProfile')
ENFORCEMENT_SHA256='678e52ea00fa984b19162441a33b33ab3d822b58f8ae2c69195dc1d5d658c4b1'
PROFILE_SHA256='ef0a39be769d74037a54f62a138fec47bb3a4fbe46e5e96c2891f70e18227ff5'


def assemble_catalog_report_sources(prepared, native, semantics):
    _require_original_preparation(prepared)
    if type(native) is not dict or type(semantics) is not dict:
        raise ValueError('Exact validated source projection required')
    expected=compose_catalog_report_semantics(prepared,evaluate_catalog_support(prepared),native['revision'])
    if canonical_numeric_free(semantics)!=canonical_numeric_free(expected):
        raise ValueError('Original semantic source correspondence required')
    policy=files('truss').joinpath('_profiles/catalog-report-assembly.json').read_bytes()
    if sha256(policy).hexdigest()!=PROFILE_SHA256:
        raise ValueError('Original report assembly projection required')
    if semantics.get('state')!='source_fields_ready':
        return {'state':'unavailable','reason':'complete_closed_source_inventory_required',
                'requiredSources':list(REQUIRED_SOURCES),'completeReportBytes':None}
    # Only the original closed source inventory supplies this absence. Broader
    # opaque extensions must keep their unavailable classification.
    if semantics['extensions']!=[] or any(entry['enforcement']!='none'
            or entry['reason']!='unqualified' for entry in semantics['assertionEntries']):
        raise ValueError('Original unqualified assertion projection required')
    evidence=json.loads(prepared.report_evidence_bytes)
    sources=native['reportSources']
    lifecycle=sources['lifecycle'];indexes=sources['indexDeclarations']
    count_names={'typesAdded':'types_added','propertiesAdded':'properties_added',
        'keysAdded':'keys_added','relationshipsAdded':'relationships_added',
        'endpointsAdded':'endpoints_added','elementsRetired':'elements_retired'}
    produced={'interfaceVersion':'truss-acceptance-report/0.3.0-proposal',
        'rev':native['revision'],'acceptedInput':prepared.input(),'umf':semantics['umf'],
        'documents':native['documents'],'diagnostics':evidence['validation']['diagnostics'],
        'documentInterpretations':evidence['validation']['documentInterpretations'],
        'counts':{name:native['counts'][source] for name,source in count_names.items()},
        'provisional':[],'rebinds':[],'pending_indexes':indexes['declaredJobs'],
        'losses':evidence['ingress']['basis']['losses'],'extensions':semantics['extensions'],
        'transformRegistrations':evidence['ingress']['basis']['transformRegistrations'],
        'lifecycleProfile':lifecycle['lifecycleProfile'],'reactivations':lifecycle['reactivations']}
    # This internal projection is called after same-call cut, policies,
    # counts/document correspondence and native empty-provisional verification.
    handoff=prepare_canonical_wire_tree(canonical_numeric_free(produced))
    # Neither the captured NativeCall nor a context artifact supplies installed
    # execution or registered layout/report meanings. There is no fallback.
    return {'state':'required_sources_missing','projectionProfile':{
        'identity':'truss-catalog-report-assembly','version':'0.1.0','sha256':PROFILE_SHA256},
        'requiredReportFields':list(FIELDS),'producedFields':produced,
        'sourceFieldCodecHandoff':{'scope':handoff.scope,
            'originalUtf8Hex':handoff.original_utf8_hex,
            'nativeTreeText':handoff.native_tree_text,'nativeTaskCount':handoff.native_task_count},
        'enforcementSourceFields':{'catalogRevision':native['revision'],
            'assertionInventorySha256':semantics['assertionInventorySha256'],
            'entries':semantics['assertionEntries']},
        'requiredSources':list(REQUIRED_SOURCES),
        'missingReportFields':[field for field in FIELDS if field not in produced],
        'completeReportBytes':None,'acceptedReportQualified':False}


def encode_unissued_complete_report_wire(source_projection, required_sources):
    """Pure complete-wire algorithm, never source registration or permission.

    Independent vectors may exercise it. The issued runtime cannot call this
    branch until the four original authority producers have been composed.
    Caller-supplied dictionaries cannot establish that authority.
    """
    if (type(source_projection) is not dict or type(required_sources) is not dict
            or set(required_sources)!=set(REQUIRED_SOURCES)):
        raise ValueError('Complete explicit wire sources required')
    produced=source_projection['producedFields']
    expected=set(FIELDS)-{'reportProfile','originalExecution','assertions'}
    if type(produced) is not dict or set(produced)!=expected:
        raise ValueError('Closed original source field map required')
    execution=required_sources['originalInstalledExecution']
    execution_keys={'installationId','sourceEpoch','origin','journalOrigin',
                    'originMappingProfile','captureProfile','contextEvidence'}
    if type(execution) is not dict or set(execution)!=execution_keys:
        raise ValueError('Complete installed execution wire required')
    if any(type(execution[key]) is not str or not execution[key]
           for key in ('installationId','sourceEpoch')):
        raise ValueError('Explicit installed execution identities required')
    policy=files('truss').joinpath('_profiles/catalog-enforcement-projection.json').read_bytes()
    if sha256(policy).hexdigest()!=ENFORCEMENT_SHA256:
        raise ValueError('Original enforcement projection policy required')
    enforcement_profile={'identity':'truss-catalog-enforcement-projection',
                         'version':'0.1.0','sha256':ENFORCEMENT_SHA256}
    if required_sources['registeredEnforcementReportProfile']!=enforcement_profile:
        raise ValueError('Selected original enforcement projection required')
    report_profile=required_sources['registeredAcceptanceReportProfile']
    layout=required_sources['admittedLayout']
    for pin in (report_profile,layout):
        if (type(pin) is not dict or set(pin)!={'identity','version','sha256'}
                or any(type(value) is not str or not value for value in pin.values())
                or len(pin['sha256'])!=64 or any(c not in '0123456789abcdef' for c in pin['sha256'])):
            raise ValueError('Exact profile wire pin required')
    if layout!=produced['acceptedInput']['layoutProfile']:
        raise ValueError('Original selected profile wire correspondence required')
    enforcement=source_projection['enforcementSourceFields']
    if (type(enforcement) is not dict or set(enforcement)!=
            {'catalogRevision','assertionInventorySha256','entries'}
            or type(enforcement['entries']) is not list):
        raise ValueError('Closed enforcement source fields required')
    inventory_digest=sha256(
        b'truss-canonical/0.1.0\ntruss-catalog-assertion-inventory/0.1.0\n'
        +canonical_numeric_free(enforcement['entries'])).hexdigest()
    if enforcement['assertionInventorySha256']!=inventory_digest:
        raise ValueError('Original assertion inventory digest correspondence required')
    assertions={'interfaceVersion':'truss-enforcement-report/0.1.0',
        'catalogRevision':produced['rev'],'reportProfile':enforcement_profile,
        'layoutProfile':layout,'scope':{'kind':'complete'},
        'assertionInventorySha256':enforcement['assertionInventorySha256'],
        'entries':enforcement['entries']}
    if enforcement['catalogRevision']!=produced['rev'] or any(
        entry['enforcement']!='none' or entry['reason']!='unqualified' for entry in assertions['entries']):
        raise ValueError('Original unqualified enforcement wire correspondence required')
    report={**produced,'reportProfile':report_profile,'originalExecution':execution,'assertions':assertions}
    if set(report)!=set(FIELDS):raise ValueError('Complete nineteen-field wire required')
    wire=canonical_numeric_free(report)
    validate_complete_report(decode_acceptance_json(wire))
    # This is the same handoff as TypeScript; the native codec is its sole SQL encoder.
    return prepare_canonical_wire_tree(wire)
