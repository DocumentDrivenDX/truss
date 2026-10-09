"""Same independent counter/custody corpus as TypeScript; no native authority."""
import json
from pathlib import Path
import unittest
from truss._operation_ordinal import OperationOrdinalIssuer


class OperationOrdinalTests(unittest.TestCase):
    def test_shared_custody_corpus(self):
        corpus=json.loads((Path(__file__).resolve().parents[3]/'tests/fixtures/operation-ordinal-issuer.json').read_text())
        for scenario in corpus['cases']:
            with self.subTest(scenario=scenario['id']):
                custody=object();issuer=OperationOrdinalIssuer(custody,int(scenario['maximum']));actual=[]
                for event in scenario['events']:
                    if event in ('reserve','foreign_reserve'):
                        result=issuer.reserve(custody if event=='reserve' else object())
                        actual.append(result.ordinal if result.outcome=='issued' else result.reason)
                    elif event in ('control_unknown','cancel','end'):
                        issuer.close(custody)
                    elif event not in ('savepoint_rollback','failed_admission'):
                        self.fail('Unknown independent event')
                self.assertEqual(actual,scenario['expected'])

    def test_native_maximum_and_exact_argument_types(self):
        custody=object()
        self.assertEqual(OperationOrdinalIssuer(custody,9223372036854775807).reserve(custody).ordinal,'0')
        for maximum in (-1,9223372036854775808,True,1.0,'1'):
            with self.assertRaises(ValueError):
                OperationOrdinalIssuer(custody,maximum)


if __name__=='__main__':unittest.main()
