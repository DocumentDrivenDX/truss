"""Exact declaration and AST transition only; no native adoption or compiler registration."""
import copy
import hashlib
import json
from pathlib import Path
R = Path(__file__).resolve().parents[5]
pins = []
def load(path):
    b = (R / path).read_bytes()
    pins.append({'path': path, 'sha256': hashlib.sha256(b).hexdigest()})
    return json.loads(b)
a = load('docs/helix/02-design/contracts/weft-review-columns-v0.11.proposal.json')
b = load('docs/helix/02-design/contracts/weft-review-columns-v0.12.proposal.json')
for key in ['tables', 'indexes', 'otherStatements']:
    if a[key] != b[key]:
        raise ValueError('declaration transition changed ' + key)
asts = []
for inv in [a, b]:
    tree = load(inv['astPath'])
    if pins[-1]['sha256'] != inv['astSha256']:
        raise ValueError('AST source drift')
    asts.append(tree)
old, new = asts
if len(old) != 106 or len(new) != 106:
    raise ValueError('statement membership')
changed = []
for i, (left, right) in enumerate(zip(old, new)):
    if left == right:
        continue
    restored = copy.deepcopy(right)
    stmt = restored['stmt']
    if 'CreateSeqStmt' in stmt:
        seq = stmt['CreateSeqStmt']
        if seq['sequence'].get('schemaname') != 'truss' or seq['sequence']['relname'] != 'journal_seq' or not seq.get('options'):
            raise ValueError('unexpected allocator evolution')
        del seq['options']
        kind = 'original journal sequence options added'
    elif 'CommentStmt' in stmt:
        if stmt['CommentStmt']['comment'] != 'truss-layout reference-history-0.12 REVIEW ONLY - unqualified':
            raise ValueError('review marker substitution')
        stmt['CommentStmt']['comment'] = 'truss-layout weft-review-0.11 REVIEW ONLY - unqualified'
        kind = 'review marker changed'
    else:
        raise ValueError('unexpected statement evolution')
    if restored != left:
        raise ValueError('additional statement delta')
    changed.append({'statementIndex': i, 'change': kind})
if len(changed) != 2:
    raise ValueError('expected exact two-statement evolution')
receipt = {'scope': __doc__, 'sourcePins': pins, 'producerSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           'statements': 106, 'tablesColumnsConstraintsAndIndexesExact': True,
           'changedStatements': changed, 'nativeQualified': False, 'weftRegistered': False}
(R / 'docs/helix/04-build/evidence/design-audit/review012-declaration-transition.json').write_text(json.dumps(receipt, indent=2) + '\n')
print('Exact declaration preservation and two-statement AST evolution verified.')
