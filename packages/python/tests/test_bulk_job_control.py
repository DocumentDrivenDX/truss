# SPDX-License-Identifier: MIT OR Apache-2.0
"""Pure job-control core against the pinned UMF owner fixture (CONTRACT-904 / CONTRACT-013).

Scope: transition table, fences, decision order, item tokens, capacity arithmetic. This proves the
portable coordination rules only. It does not run PostgreSQL, locks, custody or any native
integration, so none of the US-048 criteria is claimed passed by it; they stay planned.
Expectations come only from the fixture (hand-authored upstream, owner review pending) and from
the CONTRACT-013 capacity numbers; nothing is computed from the code under test.
"""
import copy
import hashlib
import json
import pathlib
import unittest

from truss import _bulk_job_control as m

FIXTURE = pathlib.Path(__file__).parent / 'fixtures/bulk-update/transitions.json'
PINNED_SHA256 = 'ad94f478c7c84b0c404115b275e830c91645c3f6fa009fb52ae44410a13f396e'
RAW = FIXTURE.read_bytes()
FX = json.loads(RAW)
MiB = 1024 * 1024


def run(case):
    state, event = copy.deepcopy(case['state']), copy.deepcopy(case['event'])
    out = m.apply_event(state, event)
    assert state == case['state'] and event == case['event'], 'inputs mutated'
    return out


def by_ac(ac):
    return [c for c in FX['transitions'] if c['covers'] == ac]


class PinnedFixture(unittest.TestCase):
    def test_fixture_is_the_pinned_original(self):
        self.assertEqual(hashlib.sha256(RAW).hexdigest(), PINNED_SHA256)


class Transitions(unittest.TestCase):
    def test_every_table_row_yields_exact_next_state(self):
        for c in by_ac('US-907-AC1'):
            if not c['expect']['ok']:
                continue
            r = run(c)
            self.assertTrue(r['ok'], c['id'])
            for k, v in c['expect']['state'].items():
                self.assertEqual(r['state'][k], v, (c['id'], k))
            if c['expect'].get('basis'):
                self.assertEqual(r.get('basis'), c['expect']['basis'], c['id'])

    def test_unlisted_pairs_refuse_and_terminals_absorb(self):
        permitted = {tuple(p) for p in FX['permittedPairs']}
        for sk, state in FX['samples'].items():
            for ek, event in FX['eventSamples'].items():
                r = m.apply_event(copy.deepcopy(state), copy.deepcopy(event))
                self.assertEqual(r['ok'], (sk, ek) in permitted, f'{sk}|{ek}')
                if r['ok'] and sk in ('completed', 'stopped', 'cancelled'):
                    for k, v in state.items():
                        self.assertEqual(r['state'][k], v, f'{sk}|{ek}|{k}')

    def test_fence_claim_cancel_reconcile_cases(self):
        for ac in ('US-907-AC2', 'US-907-AC3', 'US-907-AC4'):
            for c in by_ac(ac):
                r, e = run(c), c['expect']
                self.assertEqual(r['ok'], e['ok'], c['id'])
                if e['ok']:
                    for k, v in e['state'].items():
                        self.assertEqual(r['state'][k], v, (c['id'], k))
                    if e.get('basis'):
                        self.assertEqual(r.get('basis'), e['basis'], c['id'])
                elif e.get('code'):
                    self.assertEqual(r.get('code'), e['code'], c['id'])

    def test_ambiguous_evidence_never_proves_rollback(self):
        seen = 0
        for c in by_ac('US-907-AC3'):
            if c['id'].startswith('rec-ambiguous'):
                seen += 1
                r = run(c)
                self.assertEqual(r['state']['status'], 'reconciling', c['id'])
                self.assertIsNone(r['state']['stop'], c['id'])
        self.assertGreaterEqual(seen, 5)


class Fences(unittest.TestCase):
    def test_exact_decimal_without_wrap(self):
        for a, b in FX['fences']['next']:
            self.assertEqual(m.next_fence(a), b)
        for bad in FX['fences']['invalid']:
            with self.assertRaises(m.BulkRefusal, msg=repr(bad)):
                m.next_fence(bad)
        with self.assertRaises(m.BulkRefusal):
            m.next_fence(1)


class DecisionOrder(unittest.TestCase):
    def test_delegation_then_guards_then_tx1(self):
        for c in FX['decisionOrder']:
            i = c['input']
            r = m.decision_order(i['delegation'], i['guards'], i.get('tx1'), i.get('guardItem'))
            for k, v in c['expect'].items():
                self.assertEqual(r[k], v, (c['id'], k))
            if c['expect'].get('code') == 'PAP_GUARD':
                self.assertNotIn(r['code'], ('EXPECTED_VERSION', 'ENTITY_MISSING'))


class Tokens(unittest.TestCase):
    def test_injective_tokens_within_bound(self):
        t = FX['tokens']
        for v in t['valid']:
            k = m.item_token(v['ns'], v['id'], v['batch'], v['item'])
            self.assertEqual(k, v['token'])
            self.assertLessEqual(len(k), t['maxTokenUnits'])
            self.assertEqual(m.parse_item_token(k), {'namespace': v['ns'], 'id': v['id'], 'batch': v['batch'], 'item': v['item']})
        for v in t['invalid']:
            with self.assertRaises(m.BulkRefusal, msg=repr(v)):
                m.item_token(v['ns'], v['id'], v['batch'], v['item'])
        for a, b in t['distinct']:
            self.assertNotEqual(m.item_token(a['ns'], a['id'], a['batch'], a['item']), m.item_token(b['ns'], b['id'], b['batch'], b['item']))
        for k in t['parseRefuse']:
            with self.assertRaises(m.BulkRefusal, msg=k):
                m.parse_item_token(k)
        for k in t['reserved']:
            self.assertTrue(m.is_reserved_key(k))
            self.assertEqual(m.check_key_use(k, False), {'ok': False, 'code': 'PAP_RESERVED'})
            self.assertTrue(m.check_key_use(k, True)['ok'])
        for k in t['notReserved']:
            self.assertFalse(m.is_reserved_key(k))


class Capacity(unittest.TestCase):
    """CONTRACT-013: manifestControlBound + ceil(maxItems/batchSize) x R <= C (R=2 MiB, C=256 MiB)."""

    def test_defaults_admit_with_40_mib_spare(self):
        r = m.check_capacity(16 * MiB, 10000, 100, 2 * MiB, 256 * MiB)
        self.assertEqual((r['batches'], r['required'], r['spare']), (100, 216 * MiB, 40 * MiB))

    def test_eight_mib_result_bound_refuses(self):
        with self.assertRaises(m.BulkRefusal) as cm:
            m.check_capacity(16 * MiB, 10000, 100, 8 * MiB, 256 * MiB)
        self.assertEqual(cm.exception.code, 'PAP_LIMIT')

    def test_exact_boundary_admits_and_one_byte_over_refuses(self):
        self.assertEqual(m.check_capacity(16 * MiB, 10000, 100, 2 * MiB, 216 * MiB)['spare'], 0)
        with self.assertRaises(m.BulkRefusal):
            m.check_capacity(16 * MiB, 10000, 100, 2 * MiB, 216 * MiB - 1)

    def test_partial_last_batch_counts_as_a_batch(self):
        self.assertEqual(m.check_capacity(0, 101, 100, 1, 10)['batches'], 2)

    def test_invalid_inputs_refuse(self):
        for args in ((0, 10, 0, 1, 10), (-1, 10, 1, 1, 10), (0, 10, 1, True, 10), (0, 10, 1, 1.5, 10)):
            with self.assertRaises(m.BulkRefusal, msg=repr(args)):
                m.check_capacity(*args)


class FinalBatchCancel(unittest.TestCase):
    """Own expectation (not in the pinned fixture): a cancel pending when the LAST batch commits
    leaves a completed job, because nothing remains to fence (BulkUpdate.tla TerminalPreserved)."""

    def _admitted_one_batch(self):
        s = m.apply_event(None, {'kind': 'submit', 'batchCount': 1})['state']
        s = m.apply_event(s, {'kind': 'claim'})['state']
        s = m.apply_event(s, {'kind': 'execute', 'batch': 0, 'fence': '1'})['state']
        return m.apply_event(s, {'kind': 'cancel'})['state']

    def test_last_batch_commit_with_pending_cancel_completes(self):
        r = m.apply_event(self._admitted_one_batch(), {'kind': 'commit'})
        self.assertEqual((r['state']['status'], r['state']['committedBatches']), ('completed', 1))

    def test_reconciled_last_batch_with_pending_cancel_completes(self):
        s = m.apply_event(self._admitted_one_batch(), {'kind': 'lose-custody'})['state']
        r = m.apply_event(s, {'kind': 'reconcile', 'evidence': 'committed'})
        self.assertEqual(r['state']['status'], 'completed')

    def test_non_final_batch_with_pending_cancel_is_cancelled(self):
        s = m.apply_event(None, {'kind': 'submit', 'batchCount': 2})['state']
        s = m.apply_event(m.apply_event(s, {'kind': 'claim'})['state'], {'kind': 'execute', 'batch': 0, 'fence': '1'})['state']
        s = m.apply_event(s, {'kind': 'cancel'})['state']
        self.assertEqual(m.apply_event(s, {'kind': 'commit'})['state']['status'], 'cancelled')


if __name__ == '__main__':
    unittest.main()
