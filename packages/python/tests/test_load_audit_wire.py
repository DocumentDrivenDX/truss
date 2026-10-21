# SPDX-License-Identifier: MIT OR Apache-2.0
"""The selected load audit adapter accepts only a bounded metadata projection."""
import json
import unittest
from unittest.mock import patch

from truss._load_audit_runtime import (_decode_page, _decode_listing_page,
    _decode_mutation_page, _decode_mutation_listing_page,
    grant_module_audit_access, page_import_load_audit, page_mutation_group_audit)
from truss.load_audit import (LoadAuditListingCursor, LoadAuditListingEnd, LoadAuditInvocationSummary,
    MutationGroupAuditListingCursor, MutationGroupAuditListingEnd, ModuleAuditGrant,
    LoadAuditUnavailable)
from truss.psycopg_host import PsycopgHost
from truss.execution import Ok


class LoadAuditWireTests(unittest.TestCase):
    def test_invalid_grant_and_listing_filters_fail_before_host_entry(self):
        host=object.__new__(PsycopgHost)
        with patch.object(PsycopgHost,'_run_operation') as run:
            grant=grant_module_audit_access(host,None,ModuleAuditGrant(
                document_id='doc',module_id='mod',auditor_role='bad\ud800'),{},'a'*64,None)
            load=page_import_load_audit(host,None,{'loadId':'bad\ud800'},None,16,{},'a'*64,None)
            mutation=page_mutation_group_audit(host,None,{'entityKey':{'values':[object()]}},
                                                None,16,{},'a'*64,None)
            unsafe_load_cursor=LoadAuditListingCursor(installation_id='installation-1',source_epoch='epoch-1',
                release_id='release-1',release_sha256='a'*64,frontier_xid='900',filters_sha256='b'*64,
                after_observed_at='\ud800',after_invocation_id='71a0f1d0-1234-4234-9234-71a0f1d01234')
            unsafe_mutation_cursor=MutationGroupAuditListingCursor(installation_id='installation-1',source_epoch='epoch-1',
                release_id='release-1',release_sha256='a'*64,frontier_xid='900',filters_sha256='b'*64,
                after_observed_at='\ud800',after_attempt_id='71a0f1d0-1234-4234-9234-71a0f1d01234')
            load_cursor_result=page_import_load_audit(host,None,{'documentId':'doc','moduleId':'mod'},
                unsafe_load_cursor,16,{},'a'*64,None)
            mutation_cursor_result=page_mutation_group_audit(host,None,{'documentId':'doc','moduleId':'mod'},
                unsafe_mutation_cursor,16,{},'a'*64,None)
        self.assertEqual(grant,Ok(LoadAuditUnavailable(reason='observation')))
        self.assertEqual(load,Ok(LoadAuditUnavailable(reason='observation')))
        self.assertEqual(mutation,Ok(LoadAuditUnavailable(reason='observation')))
        self.assertEqual(load_cursor_result,Ok(LoadAuditUnavailable(reason='observation')))
        self.assertEqual(mutation_cursor_result,Ok(LoadAuditUnavailable(reason='observation')))
        run.assert_not_called()

    def page(self):
        return {
            'outcome': 'page', 'invocationId': '71a0f1d0-1234-4234-9234-71a0f1d01234', 'loadId': 'load-a',
            'assertedOriginSha256': 'a' * 64, 'nativeActor': '120','nativeActorName':'consumer',
            'observedAt':'2026-10-20T00:00:00.000000Z','createdCount':'1','skippedCount':'0','rejectedCount':'0',
            'loadCreatedCount':'1','loadSkippedCount':'0','loadRejectedCount':'0',
            'inputSha256': 'b' * 64, 'inputCount': '1', 'totalChunks': '1',
            'observedChunks': ['0'], 'state': 'complete', 'nextChunk': None,
            'entries': [{
                'inputIndex': '0', 'outcome': 'created', 'recordKind': 'object',
                'identity': {'kind': 'object', 'typeId': '17', 'definitionPin': 'pin',
                             'owner': {'documentId': 'doc', 'moduleId': 'mod'},
                             'keyNumber': '1', 'keyDefinitionPin': 'key-pin'},
                'payloadProfile': {'identity': 'profile', 'version': '1', 'sha256': 'c' * 64},
                'payloadSha256': 'd' * 64, 'groupAttemptId': 'attempt-1',
            }],
        }

    def encoded(self, page=None):
        return json.dumps(self.page() if page is None else page,
                          separators=(',', ':')).encode()

    def test_accepts_closed_metadata_only_page(self):
        page = _decode_page(self.encoded())
        self.assertEqual(page.entries[0].identity['keyNumber'], '1')
        self.assertEqual(page.asserted_origin_sha256, 'a' * 64)
        self.assertEqual(page.state, 'complete')
        self.assertIsNone(page.next_cursor)

    def test_page_continuation_is_typed_and_invocation_bound(self):
        value = self.page()
        value['totalChunks'] = '2'
        value['state'] = 'partial'
        value['loadCreatedCount']=None;value['loadSkippedCount']=None;value['loadRejectedCount']=None
        value['nextChunk'] = '1'
        page = _decode_page(self.encoded(value))
        self.assertEqual(page.next_cursor.invocation_id, page.invocation_id)
        self.assertEqual(page.next_cursor.chunk_index, '1')

    def summary(self):
        return {
            'outcome':'summary','invocationId':'71a0f1d0-1234-4234-9234-71a0f1d01234',
            'loadId':'load-a','assertedOriginSha256':'a'*64,'nativeActorOid':'120',
            'nativeActorName':'consumer','inputSha256':'b'*64,'inputCount':'1',
            'totalChunks':'1','observedChunkCount':'1','observedChunks':['0'],'state':'complete',
            'observedAtFrom':'2026-10-20T00:00:00.000000Z','observedAtUntil':'2026-10-20T00:00:00.000000Z',
            'createdCount':'1','skippedCount':'0','rejectedCount':'0',
            'nextPageCursor':None,
            'chunks':[{'chunkIndex':'0','observedAt':'2026-10-20T00:00:00.000000Z',
                       'createdCount':'1','skippedCount':'0','rejectedCount':'0'}]}

    def test_listing_summary_is_typed_and_cursor_is_invocation_bound(self):
        value=self.summary()
        value['nextPageCursor']={
            'profile':'truss-import-load-audit-cursor/0.2','installationId':'installation-1',
            'sourceEpoch':'epoch-1','releaseId':'release-1','releaseSha256':'a'*64,
            'frontierXid':'900','filtersSha256':'b'*64,'afterObservedAt':'2026-10-20T00:00:00.000000Z',
            'afterInvocationId':'71a0f1d0-1234-4234-9234-71a0f1d01234'}
        page=_decode_listing_page(self.encoded(value))
        self.assertIsInstance(page,LoadAuditInvocationSummary)
        self.assertIsInstance(page.next_page_cursor,LoadAuditListingCursor)
        self.assertEqual(page.next_page_cursor.after_observed_at,'2026-10-20T00:00:00.000000Z')
        self.assertEqual(page.chunks[0].created_count,'1')
        self.assertIsInstance(_decode_listing_page(b'{"outcome":"end","nextPageCursor":null}'),LoadAuditListingEnd)

    def test_partial_listing_accepts_sparse_committed_chunks(self):
        value=self.summary()
        value.update({
            'inputCount':'2', 'totalChunks':'3', 'observedChunkCount':'2',
            'observedChunks':['0','2'], 'state':'partial',
            'observedAtUntil':'2026-10-20T00:00:02.000000Z',
            'createdCount':'2',
            'chunks':[
                {'chunkIndex':'0','observedAt':'2026-10-20T00:00:00.000000Z',
                 'createdCount':'1','skippedCount':'0','rejectedCount':'0'},
                {'chunkIndex':'2','observedAt':'2026-10-20T00:00:02.000000Z',
                 'createdCount':'1','skippedCount':'0','rejectedCount':'0'},
            ],
        })
        page=_decode_listing_page(self.encoded(value))
        self.assertEqual(page.observed_chunks,('0','2'))
        self.assertEqual(tuple(chunk.chunk_index for chunk in page.chunks),('0','2'))

    def test_listing_summary_rejects_raw_origin_and_inconsistent_census(self):
        value=self.summary();value['assertedOrigin']={'entries':[]}
        with self.assertRaises(ValueError):_decode_listing_page(self.encoded(value))
        value=self.summary();value['createdCount']='0'
        with self.assertRaises(ValueError):_decode_listing_page(self.encoded(value))

    def test_listing_cursor_rejects_unknown_or_noncanonical_fields(self):
        value=self.summary()
        value['nextPageCursor']={'profile':'truss-import-load-audit-cursor/0.2','installationId':'installation-1',
            'sourceEpoch':'epoch-1','releaseId':'release-1','releaseSha256':'a'*64,
            'frontierXid':'900','filtersSha256':'b'*64,'afterObservedAt':'2026-10-20T00:00:00.000000Z',
            'afterInvocationId':'71a0f1d0-1234-4234-9234-71a0f1d01234','secret':'no'}
        with self.assertRaises(ValueError):_decode_listing_page(self.encoded(value))

    def test_rejects_raw_values_or_origin_members(self):
        page = self.page()
        page['assertedOrigin'] = {'entries': []}
        with self.assertRaises(ValueError):
            _decode_page(self.encoded(page))
        page = self.page()
        page['entries'][0]['identity']['components'] = [{'value': 'secret'}]
        with self.assertRaises(ValueError):
            _decode_page(self.encoded(page))

    def test_rejects_duplicate_members_and_numeric_wire_tokens(self):
        raw = self.encoded().replace(b'"outcome":"page"', b'"outcome":"page","outcome":"page"')
        with self.assertRaises(ValueError):
            _decode_page(raw)
        with self.assertRaises(ValueError):
            _decode_page(self.encoded().replace(b'"inputCount":"1"', b'"inputCount":1'))

    def test_rejects_duplicate_indices_and_unknown_entry_fields(self):
        page = self.page()
        page['entries'].append(dict(page['entries'][0]))
        with self.assertRaises(ValueError):
            _decode_page(self.encoded(page))

    def mutation_page(self):
        return {
            'outcome': 'page', 'attemptId': '71a0f1d0-1234-4234-9234-71a0f1d01234',
            'nativeActorOid': '120','nativeActorName':'consumer',
            'assertedAction': 'import', 'writerXid': '987',
            'observedAt':'2026-10-20T00:00:00.000000Z',
            'ownerScopes':[{'documentId':'doc','moduleId':'mod'}],
            'operationCount': '1', 'eventCount': '1',
            'entries': [{'operationIndex': '0', 'entityKind': 'object',
                         'entityId': '21', 'entityType': '17', 'operation': 'delete',
                         'observedAt': '2026-10-20T00:00:00+00:00'}],
        }

    def test_accepts_metadata_only_complete_mutation_group_page(self):
        page = _decode_mutation_page(json.dumps(self.mutation_page(), separators=(',', ':')).encode())
        self.assertEqual(page.entries[0].entity_id, '21')
        self.assertEqual(page.asserted_action, 'import')
        self.assertEqual(page.native_actor_name,'consumer')
        self.assertEqual(page.owner_scopes,({'documentId':'doc','moduleId':'mod'},))

    def test_mutation_listing_cursor_is_typed_and_end_is_explicit(self):
        value=self.mutation_page()
        value['nextPageCursor']={'profile':'truss-mutation-group-audit-cursor/0.2',
            'installationId':'installation-1','sourceEpoch':'epoch-1','releaseId':'release-1',
            'releaseSha256':'a'*64,'frontierXid':'900','filtersSha256':'b'*64,
            'afterObservedAt':'2026-10-20T00:00:00.000000Z','afterAttemptId':'71a0f1d0-1234-4234-9234-71a0f1d01234'}
        page=_decode_mutation_listing_page(json.dumps(value,separators=(',',':')).encode())
        self.assertIsInstance(page.next_page_cursor,MutationGroupAuditListingCursor)
        self.assertEqual(page.next_page_cursor.after_observed_at,'2026-10-20T00:00:00.000000Z')
        self.assertEqual(page.native_actor_name,'consumer')
        self.assertIsInstance(_decode_mutation_listing_page(b'{"outcome":"end","nextPageCursor":null}'),MutationGroupAuditListingEnd)

    def test_rejects_group_page_raw_origin_values_and_unbounded_ordinals(self):
        page = self.mutation_page()
        page['rawOrigin'] = {'secret': 'value'}
        raw = json.dumps(page, separators=(',', ':')).encode()
        with self.assertRaises(ValueError):
            _decode_mutation_page(raw)
        page = self.mutation_page()
        page['entries'][0]['operationIndex'] = '1'
        with self.assertRaises(ValueError):
            _decode_mutation_page(json.dumps(page, separators=(',', ':')).encode())
        page = self.page()
        page['entries'][0]['rawPayload'] = 'secret'
        with self.assertRaises(ValueError):
            _decode_page(self.encoded(page))


if __name__ == '__main__':
    unittest.main()
