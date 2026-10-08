"""Refine diagnostic candidates using existing original parent/creator custody only."""
import collections,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[5];B=R/'docs/helix/04-build/evidence/design-audit'
def read(p):return json.loads(p.read_bytes())
exact=read(B/'review011-original-node-correspondence.json');diagnostic=read(B/'review011-unmatched-identity-diagnostics.json')
manifest=read(B/'review010-prior-identity-catalogs.json');authored={}
for c in manifest['catalogs']:
 raw=(R/c['path']).read_bytes()
 if hashlib.sha256(raw).hexdigest()!=c['sha256']:raise ValueError('stale catalog')
 for e in json.loads(raw)['entries']:authored[e.get('entryId',e.get('id'))]=e
prefix='/modules/0/elements/0/extensions/umf.postgresql/root/members/stmts'
def native_pointer(p):
 if not p.startswith(prefix+'/'):raise ValueError('foreign pointer')
 return '/'+ '/'.join(x for x in p[len(prefix)+1:].split('/') if x not in ('members','items'))
anchors={e['authoredId']:[native_pointer(p) for p in e['selectedCandidatePointers']] for e in exact['entries'] if e['state']=='unique_exact_node_candidate'}
diagnostic_anchors={e['authoredId']:e['diagnosticNativeAstPointers'] for e in diagnostic['entries'] if e['state']=='unique_ignoring_parser_locations'}
rows=[]
for e in diagnostic['entries']:
 original=authored[e['authoredId']];parent=original.get('parentId');creator=original.get('creatingConstraintId')
 parent_pointers=anchors.get(parent,diagnostic_anchors.get(parent,[]));creator_pointers=anchors.get(creator,diagnostic_anchors.get(creator,[]))
 candidates=e['diagnosticNativeAstPointers']
 restricted=[p for p in candidates if (not parent_pointers or any(p.startswith(a+'/') for a in parent_pointers)) and (not creator_pointers or p in creator_pointers)]
 bounded=bool(parent_pointers or creator_pointers)
 rows.append({'authoredId':e['authoredId'],'parentId':parent,'creatingConstraintId':creator,'originalCandidates':candidates,'parentCandidateAnchors':parent_pointers,'parentAnchorKind':'exact' if parent in anchors else 'location_insensitive_diagnostic' if parent in diagnostic_anchors else 'none','creatorCandidateAnchors':creator_pointers,'creatorAnchorKind':'exact' if creator in anchors else 'location_insensitive_diagnostic' if creator in diagnostic_anchors else 'none','restrictedDiagnosticCandidates':restricted,'state':'unique_parent_bounded_diagnostic' if bounded and len(restricted)==1 else 'ambiguous_parent_bounded_diagnostic' if bounded and len(restricted)>1 else 'no_parent_bounded_candidate' if bounded else 'no_unique_parent_or_creator_anchor'})
result={'inputSha256':{name:hashlib.sha256((B/name).read_bytes()).hexdigest() for name in ['review011-original-node-correspondence.json','review011-unmatched-identity-diagnostics.json','review010-prior-identity-catalogs.json']},'scope':'Diagnostic location-insensitive candidates constrained by unique original parent/creator candidate nodes with exact versus diagnostic anchor strength recorded; no name-derived ownership, identity adoption or native equivalence','counts':dict(collections.Counter(e['state'] for e in rows)),'entries':rows,'identityAssignmentsMade':0,'nativeQualified':False}
(B/'review011-parent-correspondence-diagnostics.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['counts']))
