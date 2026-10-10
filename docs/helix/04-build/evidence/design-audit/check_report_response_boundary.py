"""Independent synthetic full-report shape/byte fixtures; no producer qualification."""
import base64
import hashlib
import json
from pathlib import Path
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from python_report_wire_candidate import PINS, ReportWireCandidate

HERE = Path(__file__).resolve().parent
HELIX = HERE.parents[2]
CONTRACTS = HELIX / '02-design/contracts'
BASE = HELIX / '03-test/report-wire-untrusted.fixture.json'
FIXTURE = HELIX / '03-test/report-response-boundary-v0.1.proposal.fixture.json'


def encode(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode('utf8')


def build(target):
    if type(target) is not int or target not in (4194304, 4194305):
        raise ValueError('Only frozen candidate boundary sizes admitted')
    report = json.loads(BASE.read_bytes())['report']
    report.update(interfaceVersion='truss-acceptance-report/0.3.0-proposal',
                  lifecycleProfile={'identity': 'synthetic', 'version': '0.1.0', 'sha256': 'a'*64},
                  reactivations=[], rebinds=[])
    report['diagnostics'] = []
    for index in range(8):
        raw = b'a' * (380000 if index < 7 else 0)
        report['diagnostics'].append({
            'source': {'kind': 'input'},
            'diagnosticProfile': {'identity': 'synthetic', 'version': '0.1.0', 'sha256': 'a'*64},
            'diagnostic': {'identity': 'diagnostic-'+str(index),
                           'bytesBase64': base64.b64encode(raw).decode('ascii'),
                           'sha256': hashlib.sha256(raw).hexdigest()},
            'classification': 'upstream_validation'})
    last = report['diagnostics'][-1]['diagnostic']
    available = target - len(encode(report))
    if available < 4:
        raise ValueError('Invalid fixture target')
    raw = b'a' * ((available // 4) * 3)
    last['bytesBase64'] = base64.b64encode(raw).decode('ascii')
    last['sha256'] = hashlib.sha256(raw).hexdigest()
    last['identity'] += 'x' * (target - len(encode(report)))
    return report, encode(report)


def check():
    expected = json.loads(FIXTURE.read_bytes())
    assert hashlib.sha256(BASE.read_bytes()).hexdigest() == expected['baseSha256']
    registry = Registry()
    schemas = {}
    for name, pin in PINS.items():
        source = (CONTRACTS / name).read_bytes()
        assert hashlib.sha256(source).hexdigest() == pin
        schema = json.loads(source)
        Draft202012Validator.check_schema(schema)
        schemas[name] = schema
        registry = registry.with_resource(schema['$id'], Resource.from_contents(schema))
    validator = Draft202012Validator(schemas['acceptance-report-v0.3.proposal.schema.json'], registry=registry)
    codec = ReportWireCandidate(CONTRACTS)
    assert [entry['sourceBytes'] for entry in expected['cases']] == [4194304, 4194305]
    for entry in expected['cases']:
        report, source = build(entry['sourceBytes'])
        assert len(report) == 19 and len(source) == entry['sourceBytes']
        assert hashlib.sha256(source).hexdigest() == entry['sourceSha256']
        assert validator.is_valid(report)
        for field in report:
            assert not validator.is_valid({key: value for key, value in report.items() if key != field})
        for diagnostic in report['diagnostics']:
            artifact = diagnostic['diagnostic']
            raw = base64.b64decode(artifact['bytesBase64'], validate=True)
            assert hashlib.sha256(raw).hexdigest() == artifact['sha256']
            assert len(artifact['bytesBase64']) < 1048576
        try:
            codec.prepare(source)
        except ValueError as error:
            assert str(error) == 'Original bytes and explicit finite candidate bounds required'
        else:
            raise AssertionError('Old input-sized codec unexpectedly admitted response')
    print('Two complete nineteen-field schema/byte fixtures pass; current one-MiB codec refuses both')


if __name__ == '__main__':
    import sys
    if len(sys.argv) != 1:
        raise SystemExit('No arguments admitted')
    check()
