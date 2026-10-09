from copy import deepcopy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from python_report_wire_candidate import PINS, ReportWireCandidate

HELIX = Path(__file__).resolve().parents[3]
CONTRACTS = HELIX / '02-design/contracts'


def candidate():
    report = json.loads((HELIX / '03-test/report-wire-untrusted.fixture.json').read_bytes())['report']
    report.update(interfaceVersion='truss-acceptance-report/0.3.0-proposal',
                  lifecycleProfile={'identity': 'synthetic', 'version': '0.1.0', 'sha256': 'a'*64},
                  reactivations=[], rebinds=[])
    return report


def wire(report):
    return json.dumps(report, ensure_ascii=False, separators=(',', ':')).encode('utf8')


class ReportCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.codec = ReportWireCandidate(CONTRACTS)

    def test_original_nineteen_fields_and_mutable_source_custody(self):
        original = bytearray(wire(candidate()))
        result = self.codec.prepare(original)
        self.assertEqual(len(result.original.value.entries), 19)
        self.assertEqual(result.original.source_bytes, bytes(original))
        original[:] = b'changed'
        self.assertNotEqual(result.original.source_bytes, bytes(original))
        self.assertEqual(result.scope, 'original_composed_report_schema_bytes_only')

    def test_all_fields_versions_and_numeric_nodes_refuse(self):
        for field in candidate():
            with self.subTest(field=field), self.assertRaises(Exception):
                changed = candidate(); del changed[field]; self.codec.prepare(wire(changed))
        for version in ['truss-acceptance-report/0.1.0', 'unknown']:
            changed = candidate(); changed['interfaceVersion'] = version
            with self.assertRaises(Exception): self.codec.prepare(wire(changed))
        changed = candidate(); changed['counts']['typesAdded'] = 9007199254740993
        with self.assertRaisesRegex(ValueError, 'numeric node'): self.codec.prepare(wire(changed))
        changed = candidate(); changed['accepted'] = True
        with self.assertRaises(Exception): self.codec.prepare(wire(changed))

    def test_nested_reactivation_schema_and_codec_only_forgeries(self):
        changed = candidate()
        artifact = {'identity': 'synthetic', 'bytesBase64': 'e30=', 'sha256': 'a'*64}
        changed['reactivations'] = [{'identity': {'kind': 'key', 'typeId': '1', 'keyNumber': '1'},
            'owner': {'documentId': 'doc', 'moduleId': 'module'}, 'lineage': artifact,
            'beforeRetiredRevision': '1', 'beforeDefinition': artifact, 'afterDefinition': artifact}]
        self.codec.prepare(wire(changed))  # Structural validity does not verify artifact digest/effects.
        del changed['reactivations'][0]['identity']['typeId']
        with self.assertRaises(Exception): self.codec.prepare(wire(changed))
        forged = candidate(); forged['documents'] = []
        forged['originalExecution']['origin']['databaseRole'] = 'invented'
        self.assertEqual(self.codec.prepare(wire(forged)).scope, 'original_composed_report_schema_bytes_only')

    def test_complete_history_rebind_and_version_operation_refusal(self):
        present = {'present': True, 'value': {'kind': 'null'}}
        absent = {'present': False}
        event = {'interfaceVersion': 'truss-history-event/0.2.0-proposal',
            'sourceEpoch': 'epoch', 'historyProfile': 'synthetic', 'xid': '1', 'seq': '1',
            'identity': {'id': '1', 'typeId': '1', 'definitionPin': 'synthetic',
                         'owner': {'documentId': 'doc', 'moduleId': 'module'}},
            'eventVersion': '2', 'eventCatalogRevision': '1',
            'mutationGroup': {'profile': 'truss-history-group/0.1.0', 'eventCount': '1',
                              'orderedEventDigest': '0'*64},
            'origin': {'asserted': {'kind': 'null'}, 'databaseRole': 'role'},
            'operation': 'rebind', 'retainedName': 'a', 'propertyId': '1',
            'beforeDefinitionContext': 'before', 'afterDefinitionPin': 'after',
            'retainedBefore': present, 'retainedAfter': absent,
            'propertyBefore': absent, 'propertyAfter': present}
        report = candidate(); report['rebinds'] = [event]
        self.codec.prepare(wire(report))
        for field, value in [('interfaceVersion', 'truss-history-event/0.1.0'),
                             ('operation', 'retain')]:
            changed = deepcopy(report); changed['rebinds'][0][field] = value
            with self.assertRaises(Exception): self.codec.prepare(wire(changed))
        changed = deepcopy(report); del changed['rebinds'][0]['retainedBefore']
        with self.assertRaises(Exception): self.codec.prepare(wire(changed))

    def test_original_schema_substitution_and_wire_capacity(self):
        with tempfile.TemporaryDirectory() as target:
            for name in PINS: shutil.copyfile(CONTRACTS/name, Path(target)/name)
            name = 'acceptance-report-v0.3.proposal.schema.json'
            with (Path(target)/name).open('ab') as output: output.write(b' ')
            with self.assertRaisesRegex(ValueError, 'pin mismatch'): ReportWireCandidate(Path(target))
        with self.assertRaises(ValueError): self.codec.prepare(b' '*1048577)


if __name__ == '__main__': unittest.main()
