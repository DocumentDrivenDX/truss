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
    if type(qualified_successor) is not _EpochComparison or pending.profile!=b'{"kind":"truss-authority-transition-pending/0.1"}':
        raise ValueError('Original pending fixture and successor comparison required')
    if (pending.installation,pending.incarnation)!=(qualified_successor.installation,qualified_successor.incarnation):
        raise ValueError('Original installation/incarnation correspondence required')
    return _issue_fixture_successor(connection,pending,qualified_successor.profile,qualified_successor.evidence)
