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




class OperationOrdinalRegistryTests(unittest.TestCase):
    def test_shared_facades_and_ended_transaction_cannot_reset(self):
        from truss._operation_ordinal import OperationOrdinalRegistry
        producer, connection, transaction = object(), object(), object()
        registry = OperationOrdinalRegistry(producer, connection, 2, 10)
        first = registry.bind(producer, connection, transaction)
        self.assertEqual(first.reserve(transaction).ordinal, '0')
        second = registry.bind(producer, connection, transaction)
        self.assertIs(first, second)
        self.assertEqual(second.reserve(transaction).ordinal, '1')
        registry.end(producer, connection, transaction)
        rebound = registry.bind(producer, connection, transaction)
        self.assertIs(rebound, first)
        self.assertEqual(rebound.reserve(transaction).reason, 'closed')
        later = object()
        self.assertEqual(registry.bind(producer, connection, later).reserve(later).ordinal, '0')
        with self.assertRaises(ValueError):
            registry.bind(producer, connection, object())

    def test_foreign_custody_and_connection_close(self):
        from truss._operation_ordinal import OperationOrdinalRegistry
        producer, connection, transaction = object(), object(), object()
        registry = OperationOrdinalRegistry(producer, connection, 1, 0)
        for arguments in [(object(), connection, transaction), (producer, object(), transaction)]:
            with self.assertRaises(ValueError):
                registry.bind(*arguments)
        issuer = registry.bind(producer, connection, transaction)
        with self.assertRaises(ValueError):
            registry.close(object())
        registry.close(producer)
        self.assertEqual(issuer.reserve(transaction).reason, 'closed')
        with self.assertRaises(ValueError):
            registry.bind(producer, connection, transaction)

if __name__=='__main__':unittest.main()
