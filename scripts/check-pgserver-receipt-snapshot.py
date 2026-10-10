"""Native snapshot visibility basis only; no original receipt or reached authority."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import tempfile
from urllib.parse import urlparse, parse_qs
import pg8000.dbapi
import pgserver

ROOT = Path(__file__).resolve().parents[1]
assert importlib.metadata.version('pgserver') == '0.1.4'
assert importlib.metadata.version('pg8000') == '1.31.5'
observations = []
with tempfile.TemporaryDirectory(prefix='truss-receipt-snapshot-') as directory:
    server = pgserver.get_server(Path(directory) / 'data', cleanup_mode='stop')
    connections = []
    try:
        uri = urlparse(server.get_uri())
        params = parse_qs(uri.query)
        host = params.get('host', [uri.hostname])[0]
        port = int(params.get('port', [uri.port or 5432])[0])
        kwargs = dict(user='postgres', database='postgres', port=port, ssl_context=False)
        if host.startswith('/'):
            kwargs['unix_sock'] = str(Path(host) / f'.s.PGSQL.{port}')
        else:
            kwargs['host'] = host
        writer, reader = [pg8000.dbapi.connect(**kwargs) for _ in range(2)]
        connections.extend([writer, reader])
        for connection in connections:
            connection.autocommit = True
        def query(connection, sql, args=()):
            cursor = connection.cursor()
            try:
                cursor.execute(sql, args)
                return cursor.fetchall() if cursor.description else None
            finally:
                cursor.close()
        version = query(writer, 'SHOW server_version')[0][0]
        assert version == '16.2'
        query(writer, 'CREATE TABLE public.visibility_probe(value text)')
        for kind in ('pending-write', 'feed-empty-transaction', 'aborted-transaction'):
            query(writer, 'BEGIN')
            xid = query(writer, 'SELECT pg_current_xact_id()::text')[0][0]
            if kind == 'pending-write':
                query(writer, "INSERT INTO public.visibility_probe VALUES ('original pending fixture')")
            query(reader, 'BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY')
            snapshot = query(reader, 'SELECT pg_current_snapshot()::text')[0][0]
            before = query(reader, 'SELECT pg_visible_in_snapshot(%s::xid8,%s::pg_snapshot)', (xid, snapshot))[0][0]
            assert before is False
            query(writer, 'ROLLBACK' if kind == 'aborted-transaction' else 'COMMIT')
            old = query(reader, 'SELECT pg_visible_in_snapshot(%s::xid8,pg_current_snapshot())', (xid,))[0][0]
            assert old is False
            if kind == 'pending-write':
                assert query(reader, 'SELECT count(*)::text FROM public.visibility_probe')[0][0] == '0'
            query(reader, 'ROLLBACK')
            query(reader, 'BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY')
            fresh = query(reader, 'SELECT pg_visible_in_snapshot(%s::xid8,pg_current_snapshot())', (xid,))[0][0]
            assert fresh is True
            if kind == 'pending-write':
                assert query(reader, 'SELECT count(*)::text FROM public.visibility_probe')[0][0] == '1'
            query(reader, 'ROLLBACK')
            observations.append(dict(kind=kind, writerXid=xid, originalSnapshot=snapshot, beforeCommit=before, settlement="rollback" if kind == "aborted-transaction" else "commit", oldSnapshotAfterSettlement=old, freshSnapshotAfterSettlement=fresh))
    finally:
        for connection in connections:
            connection.close()
        server.cleanup()
receipt = dict(scope='PostgreSQL snapshot primitive and independent fixture row correspondence only', pgserver='0.1.4', driver='pg8000 1.31.5 dbapi; probe transport only', serverVersion=version, observations=observations, reachedQualified=False, sourceSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), limitations=['Local trust administrator fixture, no ordinary-person authorization', 'No original receipt commitment, token resolver, retention or source epoch admission', 'Native visibility of an xid cannot alone distinguish an originally committed receipt from aborted effects', 'No replica application/coverage/seed evidence or public read capability', 'Existing private dependencies, not clean distribution qualification'])
(ROOT / 'docs/helix/04-build/evidence/design-audit/pgserver-receipt-snapshot-component.json').write_text(json.dumps(receipt, indent=2)+'\n')
print(json.dumps(dict(serverVersion=version, snapshotCases=len(observations), reachedQualified=False)))
