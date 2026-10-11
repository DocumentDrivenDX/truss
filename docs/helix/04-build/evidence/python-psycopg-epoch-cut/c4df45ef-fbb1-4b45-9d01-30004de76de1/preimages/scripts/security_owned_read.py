"""Owned flat identity read spike within one host operation; no public authority.

UMF owns decoding, keys and policy semantics. Administrative issuer/mapping and
trusted=true remain fixture premises. This tool never exposes raw cells as output.
"""
from pathlib import Path
from dataclasses import asdict
import hashlib,json,subprocess
from truss._psycopg_dependency_fact_cut import (_epoch_dependency_recipe,_OriginalFactSources,
    _inspect_original_fact_sources,_capture_dependency_relation_cells,_run_dependency_fact_operation,_verify_native_profile_caller)
ROOT=Path(__file__).resolve().parent.parent


def run_owned_identity_read(host, transaction, epoch, requirements, sources):
    if type(sources) is not _OriginalFactSources:raise ValueError('Original fixture sources required')
    sources=_OriginalFactSources(sources.policy,sources.resolution)
    digest=hashlib.sha256(requirements).hexdigest()
    _inspect_original_fact_sources(requirements,digest,sources)
    selected,providers=_epoch_dependency_recipe(epoch,digest,sources)
    profile=json.loads(selected.profile)
    if profile['kind'] not in ('truss-flat-fact-provider-fixture/0.2','truss-flat-fact-provider-fixture/0.3'):
        raise ValueError('Original source-bound fixture profile required')
    groups={}
    for p in providers:
        group=groups.setdefault(p.relation.oid,{'relation':p.relation,'fields':[],'associations':[]})
        if p.kind=='field':
            c=p.column
            if c is None or c.type_oid not in (16,20,25) or c.generated!='':raise ValueError('Ordinary native fixture column required')
            group['fields'].append((p.reference,c))
        else:group['associations'].append(p.reference)
    if len(groups)>32 or any(len(g['fields'])>32 for g in groups.values()):raise ValueError('Bounded fixture capture required')
    tool=ROOT/'scripts/evaluate-security-captured-identity-fixture.ts'
    owner=Path('/Users/erik/.codex/worktrees/security-main-integration/umf')
    paths=[tool]+[p for p in (owner/'src').rglob('*') if p.is_file() and p.suffix in ('.ts','.json')]+[owner/'tests/security/fixture.ts']
    pins={p:hashlib.sha256(p.read_bytes()).digest() for p in paths}
    def execute(cursor):
        caller=profile.get('caller')
        _verify_native_profile_caller(cursor,selected.profile)
        cells=_capture_dependency_relation_cells(cursor,groups)
        captured=[asdict(c) for c in cells]
        payload=json.dumps(captured if caller is None else {'cells':captured,'subjectKey':caller['subjectKey']})
        if len(payload.encode('utf8'))>1048576:raise ValueError('Bounded semantic fixture input required')
        result=subprocess.run(['/opt/homebrew/bin/bun',str(tool)],cwd=ROOT,input=payload,capture_output=True,text=True,timeout=4)
        if result.returncode or len(result.stdout.encode('utf8'))>65536:raise ValueError('Original UMF fixture evaluation refused')
        if any(hashlib.sha256(p.read_bytes()).digest()!=h for p,h in pins.items()):raise ValueError('Original evaluator sources changed')
        receipt=json.loads(result.stdout)
        if type(receipt) is not dict or set(receipt)!= {'decision','identities'}:raise ValueError('Original fixture decision envelope required')
        decision=receipt['decision']
        if type(decision) is not dict or decision.get('decision') not in ('permit','deny'):raise ValueError('Determinate fixture decision required')
        # No raw cells, private fact identities or evaluator diagnostics leave
        # this owned operation. Dispositions remain original UMF output.
        return decision
    return _run_dependency_fact_operation(host,transaction,selected,requirements,digest,providers,execute)
