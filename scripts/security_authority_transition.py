"""Private committed-pending authority transition spike; no qualified issuer.

The original installed native issuer owns epochs. Pending is deliberately outside
all admitted dependency-provider profiles. Administrative references and successor
requalification are trusted fixture premises, never credentials or capabilities.
"""
import json
from psycopg import pq
from truss._psycopg_epoch_cut import _EpochComparison


def _issue_fixture_successor(connection, expected, profile, evidence):
    if type(expected) is not _EpochComparison or connection.info.transaction_status != pq.TransactionStatus.IDLE:
        raise ValueError('Original idle administrative fixture and epoch required')
    with connection.transaction():
        connection.execute('SET TRANSACTION ISOLATION LEVEL READ COMMITTED',prepare=False)
        # Serialize participating writers before comparing the actual pointer and
        # registry image. A supplied comparison is not an issuer credential.
        connection.execute('SELECT truss.runtime_fence_shared_authority_writer()',prepare=False)
        with connection.cursor() as cursor:
            cursor.execute("SELECT r.installation_id::pg_catalog.text,r.source_epoch::pg_catalog.text,"
                           "r.target_incarnation::pg_catalog.text,pg_catalog.encode(r.profile_bytes,'hex') AS profile_hex,"
                           "pg_catalog.encode(r.evidence_bytes,'hex') AS evidence_hex,pg_catalog.current_setting('transaction_isolation') AS transaction_isolation "
                           "FROM truss.source_epoch_current c JOIN truss.source_epoch_registry r "
                           "ON r.installation_id OPERATOR(pg_catalog.=) c.installation_id "
                           "AND r.source_epoch OPERATOR(pg_catalog.=) c.source_epoch "
                           "WHERE c.singleton_id OPERATOR(pg_catalog.=) 1",prepare=False,binary=False)
            rows=cursor.fetchmany(2)
            if (cursor.description is None or len(cursor.description)!=6
                    or any(d.type_code!=25 for d in cursor.description)
                    or rows!=[(expected.installation,expected.epoch,expected.incarnation,expected.profile.hex(),expected.evidence.hex(),'read committed')]):
                raise ValueError('Original current transition bytes required')
        row=connection.execute("SELECT truss.runtime_issue_source_epoch(%s,%s,%s,%s,%s)",
            (expected.installation,expected.epoch,expected.incarnation,profile,evidence),prepare=False).fetchone()
        if row is None or len(row)!=1 or type(row[0]) is not str:raise ValueError('Original native issued generation required')
        result=_EpochComparison(expected.installation,row[0],expected.incarnation,profile,evidence)
    # Return only after actual successful transaction completion. Unknown commit
    # outcomes require fresh administrative inspection, never blind replay.
    return result


def _begin_pending_authority_fixture(connection, original):
    profile=json.dumps({'kind':'truss-authority-transition-pending/0.1'},sort_keys=True,separators=(',',':')).encode()
    return _issue_fixture_successor(connection,original,profile,b'owned-pending-authority-fixture')


def _finish_pending_authority_fixture(connection, pending, qualified_successor):
    # Qualified successor is an explicit administrative premise. This helper
    # neither authenticates its producer nor independently qualifies its contents.
    if type(pending) is not _EpochComparison or type(qualified_successor) is not _EpochComparison or pending.profile!=b'{"kind":"truss-authority-transition-pending/0.1"}':
        raise ValueError('Original pending fixture and successor comparison required')
    if (pending.installation,pending.incarnation)!=(qualified_successor.installation,qualified_successor.incarnation):
        raise ValueError('Original installation/incarnation correspondence required')
    return _issue_fixture_successor(connection,pending,qualified_successor.profile,qualified_successor.evidence)
