"""Independent fixture meaning check; does not invoke a Truss/native encoder."""
import codecs
from hashlib import sha256
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
SOURCE = ROOT / 'docs/helix/03-test/report-scalar-stream-v0.1.proposal.vectors.json'
original = SOURCE.read_bytes()
fixture = json.loads(original)
maximum = 131072
if fixture['expansionMaximumBytes'] != str(maximum):
    raise ValueError('Original fixture expansion profile required')


def expand(parts):
    result = bytearray()
    for part in parts:
        if set(part) != {'hex', 'repeat'} or not re.fullmatch(r'(?:[0-9a-f]{2})+', part['hex']):
            raise ValueError('Exact fixture part required')
        if not re.fullmatch(r'0|[1-9][0-9]{0,5}', part['repeat']):
            raise ValueError('Bounded canonical repeat required')
        block = bytes.fromhex(part['hex']); count = int(part['repeat'])
        if len(result) + len(block) * count > maximum:
            raise ValueError('Whole expanded fixture capacity exceeded')
        result.extend(block * count)
    return bytes(result)


results = []
names = set()
for vector in fixture['vectors']:
    if vector['name'] in names: raise ValueError('Duplicate original vector')
    names.add(vector['name'])
    source = expand(vector['sourceParts'])
    if len(source) != int(vector['sourceByteLength']): raise ValueError('Source length mismatch')
    offsets = [int(value) for value in vector['splitOffsets']]
    if offsets != sorted(set(offsets)) or any(not 0 < value < len(source) for value in offsets):
        raise ValueError('Original interior split offsets required')
    schedules = [[value] for value in offsets] + [offsets]
    for schedule in schedules:
        decoder = codecs.getincrementaldecoder('utf-8')('strict')
        start = 0; strings = []; valid = True
        try:
            for end in schedule:
                strings.append(decoder.decode(source[start:end], final=False)); start = end
            strings.append(decoder.decode(source[start:], final=True))
        except UnicodeError:
            valid = False
        if valid != vector['expectedUtf8Valid']: raise ValueError('Independent UTF-8 expectation mismatch')
        if valid and ''.join(strings).encode('utf8') != source: raise ValueError('Original bytes lost')
    if vector['expectedUtf8Valid']:
        expected = expand(vector['expectedCanonicalParts'])
        if len(expected) != int(vector['expectedCanonicalByteLength']) or sha256(expected).hexdigest() != vector['expectedCanonicalSha256']:
            raise ValueError('Original canonical expected bytes mismatch')
        if json.loads(expected.decode('utf8')).encode('utf8') != source:
            raise ValueError('Expected canonical literal changes original meaning')
    elif any(key.startswith('expectedCanonical') for key in vector):
        raise ValueError('Invalid UTF-8 cannot supply successful expected output')
    results.append({'name': vector['name'], 'sourceSha256': sha256(source).hexdigest(),
                    'sourceBytes': len(source), 'splitSchedules': len(schedules),
                    'expectedUtf8Valid': vector['expectedUtf8Valid']})

receipt = {'status': 'passed_independent_fixture_meaning', 'vectors': len(results),
           'fixtureSha256': sha256(original).hexdigest(),
           'checkerSha256': sha256(Path(__file__).read_bytes()).hexdigest(), 'results': results,
           'scope': 'Python strict incremental UTF-8 and expected JSON literal meaning/hash checks only. No production/native encoder, scalar resource admission, whole report or acceptance qualification.'}
(HERE / 'report-scalar-stream-vectors.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(str(len(results)) + ' independent scalar byte vectors passed; native encoder not_run')
