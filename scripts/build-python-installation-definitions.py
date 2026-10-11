"""Compile original release definitions on an independent disposable PG18.6.

No installation constructor, target observation or target snapshot is consumed.
The same registered projection selects compared fields, not whole catalog closure.
"""
from pathlib import Path
from hashlib import sha256
from importlib.metadata import version as package_version
import json
import tempfile
from urllib.parse import urlparse,parse_qs
from pg8000.native import Connection
from truss import LocalPostgres
from truss._runtime_profile import RUNTIME_DISTRIBUTION
from truss._installation_statement_release import STATEMENTS_SHA256

root=Path(__file__).resolve().parents[1]
asset_path=root/'packages/python/src/truss/_installation/statements.json'
original=asset_path.read_bytes()
if sha256(original).hexdigest()!=STATEMENTS_SHA256:raise ValueError('Original statement release required')
profile=json.loads(original)
owner_path=root/'docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql'
owner=owner_path.read_bytes()
if sha256(owner).hexdigest()!=profile['ownerExportSha256']:raise ValueError('Original owner export required')
if '; '.join(s['sql'] for s in profile['statements']).encode()!=owner:raise ValueError('Complete ordered export required')
query_path=root/'packages/python/src/truss/_installation/definitions.sql'
query=query_path.read_bytes()
with tempfile.TemporaryDirectory(prefix='truss-independent-release-') as directory:
    with LocalPostgres(Path(directory)/'data') as runtime:
        uri=urlparse(runtime.info.connection_uri);params=parse_qs(uri.query)
        host=params.get('host',[uri.hostname])[0];port=int(params.get('port',[uri.port or 5432])[0])
        kwargs={'user':'postgres','database':'postgres','port':port,'ssl_context':False}
        kwargs['unix_sock' if host.startswith('/') else 'host']=str(Path(host)/f'.s.PGSQL.{port}') if host.startswith('/') else host
        connection=Connection(**kwargs)
        try:
            backend_sha256=sha256(runtime.psql_path.with_name('postgres').read_bytes()).hexdigest()
            backend_description=connection.run('SELECT pg_catalog.version()')[0][0]
            version=connection.run("SELECT pg_catalog.current_setting('server_version_num')")[0][0]
            if version!='180006':raise ValueError('Independent compiler profile requires PostgreSQL18.6')
            if connection.run("SELECT pg_catalog.to_regnamespace('truss')::pg_catalog.text")!=[[None]]:raise ValueError('Independent fresh namespace required')
            connection.run('BEGIN');connection.run('SET LOCAL search_path = pg_catalog, pg_temp')
            try:
                for statement in profile['statements']:connection.run(statement['sql'])
                rows=connection.run(query.decode('utf8'))
                if len(rows)!=1 or len(rows[0])!=1 or type(rows[0][0]) is not str:raise ValueError('Original native projection required')
                native=rows[0][0].encode('utf8')
            finally:connection.run('ROLLBACK')
            if connection._transaction_status!=b'I' or connection.run("SELECT pg_catalog.to_regnamespace('truss')::pg_catalog.text")!=[[None]]:raise ValueError('Independent compiler rollback confirmation required')
        finally:connection.close()
paths=[asset_path,owner_path,query_path,Path(__file__).resolve()]
value={'interface':'truss-selected-native-definition-baseline/0.1.0','nativeVersion':version,
       'backendSha256':backend_sha256,'backendDescription':backend_description,'pgserverVersion':package_version(RUNTIME_DISTRIBUTION),'pg8000Version':package_version('pg8000'),'fixedSessionSettings':{'search_path':'pg_catalog, pg_temp'},
       'statementReleaseSha256':STATEMENTS_SHA256,'modelSha256':profile['modelSha256'],
       'ownerExportSha256':profile['ownerExportSha256'],'querySha256':sha256(query).hexdigest(),
       'sources':{str(p.relative_to(root)):sha256(p.read_bytes()).hexdigest() for p in paths},
       'compiledOriginal':native.decode('utf8'),'independentRollbackConfirmed':True,'installationReady':False,
       'scope':'independent_original_release_compilation_selected_expressions_constraints_indexes'}
encoded=(json.dumps(value,indent=2)+'\n').encode('utf8')
(root/'packages/python/src/truss/_installation/definitions.json').write_bytes(encoded)
(root/'packages/python/src/truss/_installation_definition_release.py').write_text(
 '"""Independent native source compilation pins, not installation authority."""\nDEFINITIONS_SHA256 = '+repr(sha256(encoded).hexdigest())+'\nDEFINITION_QUERY_SHA256 = '+repr(sha256(query).hexdigest())+'\n')
print(json.dumps({'version':version,'sha256':sha256(encoded).hexdigest(),'counts':{k:len(v) for k,v in json.loads(native).items()},'rollbackConfirmed':True}))
