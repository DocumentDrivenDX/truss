#!/usr/bin/env python3
"""Read-only frozen consumer revision comparison; no compiler/native adoption."""
from datetime import datetime, timezone
import copy
from decimal import Decimal
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / 'docs/helix/04-build/evidence/consumer-revision-2026-10-09'
AUDIT = ROOT / 'docs/helix/04-build/evidence/design-audit'


def decode(raw):
    def object_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate source member')
            result[key] = value
        return result
    def constant(value):
        raise ValueError('Non-JSON numeric constant')
    return json.loads(raw, parse_float=Decimal, object_pairs_hook=object_pairs,
                      parse_constant=constant)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    previous = (AUDIT / 'consumer-logical-frontend-inputs.json').read_bytes()
    pin = decode((AUDIT / 'consumer-logical-frontend.json').read_bytes())
    assert sha(previous) == pin['inputsSha256']
    saved = decode(previous)
    model_results = []
    for filename, suffix in [('module.umf.json', '/src/hohfeld/conformance/module.umf.json'),
                             ('example.umf.json', '/examples/catalog/catalog.umf.json')]:
        raw = (SNAPSHOT / filename).read_bytes()
        updated = decode(raw)
        original = next(row for row in saved if row['source'].endswith(suffix) and row['variant'] == 'original')
        proposed = next(row for row in saved if row['source'].endswith(suffix) and row['variant'] == 'proposed')
        old = decode(original['request']['modules'][0]['documentJson'])
        proposal = decode(proposed['request']['modules'][0]['documentJson'])
        assert updated == proposal, 'Owner-authored source differs from prior named semantic proposal'
        changed = []
        stripped = copy.deepcopy(updated)
        for module in updated['modules']:
            prior = next(m for m in old['modules'] if m['id'] == module['id'])
            for element in module['elements']:
                earlier = next(e for e in prior['elements'] if e['id'] == element['id'])
                if element.get('kind') in ('record', 'field'):
                    assert type(element.get('name')) is str and element['name']
                if element != earlier:
                    assert 'name' not in earlier and element.get('kind') in ('record', 'field')
                    assert {key:value for key,value in element.items() if key != 'name'} == earlier
                    changed.append({'module':module['id'],'element':element['id'],'name':element['name']})
                    copied_module = next(m for m in stripped['modules'] if m['id'] == module['id'])
                    next(e for e in copied_module['elements'] if e['id'] == element['id']).pop('name')
        assert changed and stripped == old, 'Non-name semantic changes in original document'
        model_results.append({'snapshot': filename, 'sha256': sha(raw), 'authoredNameChanges': changed,
                              'equalsPriorNamedProposalSemantically': True,
                              'limitation': 'Semantic comparison, not byte identity with prior proposal or compiler/native execution'})
    corpus_raw = (SNAPSHOT / 'corpus.json').read_bytes()
    corpus = decode(corpus_raw)
    invalid = next(case for case in corpus['cases'] if case['id'] == 'freshness.unissued-token-is-invalid')
    reached = [step for step in invalid['steps'] if step['op'] == 'reached']
    assert len(reached) == 2 and all(step['expect'] == {'error':'Invalid'} for step in reached)
    counts = {op:sum(step['op']==op for case in corpus['cases'] for step in case['steps'])
              for op in sorted({step['op'] for case in corpus['cases'] for step in case['steps']})}
    receipt = {'observedAt':datetime.now(timezone.utc).isoformat(),
               'scope':'Frozen consumer-authored revision; input correspondence only',
               'producerSha256':sha(Path(__file__).read_bytes()),'previousInputsSha256':sha(previous),
               'sources':{path.name:sha(path.read_bytes()) for path in sorted(SNAPSHOT.iterdir()) if path.is_file()},
               'models':model_results,'consumerCorpusVersion':corpus['version'],
               'caseCount':len(corpus['cases']),'operationCounts':counts,
               'unissuedMalformedReachedExpectsInvalid':True,
               'compilerExecuted':False,'nativeExecuted':False,'consumerReady':False}
    (AUDIT/'consumer-revision-2026-10-09.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'models':len(model_results),'authoredNames':sum(len(m['authoredNameChanges']) for m in model_results),
                      'caseCount':len(corpus['cases']),'querySteps':counts.get('query',0),'invalidReachedCases':2}))


if __name__ == '__main__':
    main()
