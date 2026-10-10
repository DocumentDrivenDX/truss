#!/usr/bin/env python3
"""Historical isolation + nested-definer experiment; not current installation."""
import hashlib
import importlib.metadata
import importlib.resources
import json
from pathlib import Path
import subprocess
import tempfile
import pgserver

root = Path(__file__).resolve().parents[1]
paths = ['docs/helix/02-design/contracts/storage-layout.sql',
         'docs/helix/02-design/contracts/module-isolation.sql',
         'docs/helix/02-design/contracts/module-isolation.check.sql']
originals = [(root / path).read_bytes() for path in paths]
psql = Path(str(importlib.resources.files('pgserver'))) / 'pginstall/bin/psql'
fixture = """
CREATE FUNCTION truss.caller_probe() RETURNS json LANGUAGE sql STABLE SECURITY DEFINER
SET search_path=pg_catalog,pg_temp AS $$
SELECT json_build_object('acting',truss.acting_role(),'effective',current_user,
 'ids',coalesce((SELECT json_agg(id ORDER BY id) FROM truss.object),'[]'::json))
$$;
ALTER FUNCTION truss.caller_probe() OWNER TO iso_ra;
REVOKE ALL ON FUNCTION truss.caller_probe() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION truss.caller_probe() TO iso_wa,iso_wb,iso_none;
SET ROLE iso_wa; SELECT truss.caller_probe(); RESET ROLE;
SET ROLE iso_wb; SELECT truss.caller_probe(); RESET ROLE;
PREPARE caller_probe AS SELECT truss.caller_probe();
SET ROLE iso_wa; EXECUTE caller_probe; RESET ROLE;
SET ROLE iso_wb; EXECUTE caller_probe; RESET ROLE;
SET ROLE iso_none; EXECUTE caller_probe; RESET ROLE;
DEALLOCATE caller_probe;
"""
with tempfile.TemporaryDirectory(prefix='truss-corrected-isolation-') as directory:
    server = pgserver.get_server(Path(directory) / 'data', cleanup_mode='stop')
    try:
        def query(sql):
            return subprocess.check_output([str(psql), server.get_uri(), '-X', '-q', '-A', '-t',
                '-v', 'ON_ERROR_STOP=1'], input=sql, text=True, timeout=60).strip()
        version = query('SHOW server_version;')
        if version != '16.15' or importlib.metadata.version('pgserver') != '0.1.4+truss.pg16.15':
            raise RuntimeError('Original corrected candidate required')
        output = query('BEGIN;\n' + '\n'.join(data.decode() for data in originals) + fixture + '\nROLLBACK;')
        lines = [line for line in output.splitlines() if line]
        if lines[0] != 'module-isolation check passed' or len(lines) != 6:
            raise RuntimeError('Unexpected complete original check output: ' + output)
        observed = [json.loads(line) for line in lines[1:]]
        expected = [{'acting': role, 'effective': 'iso_ra', 'ids': ids} for role, ids in
            [('iso_wa',[101,102,104]),('iso_wb',[103]),('iso_wa',[101,102,104]),
             ('iso_wb',[103]),('iso_none',[])]]
        if observed != expected:
            raise RuntimeError('Nested caller policy mismatch: ' + repr(observed))
        if query("SELECT to_regnamespace('truss') IS NULL;") != 't':
            raise RuntimeError('Rollback did not remove fixture namespace')
    finally:
        server.cleanup()
receipt = {'scope': 'Original historical0.2 module isolation and five nested non-superuser definer observations on corrected candidate only',
    'serverVersion': version, 'pgserver': importlib.metadata.version('pgserver'),
    'historicalCheckPassed': True, 'observed': observed, 'expected': expected,
    'preparedObservationCount': 3, 'unpreparedObservationCount': 2,
    'fixtureSql': fixture, 'fixtureSqlSha256': hashlib.sha256(fixture.encode()).hexdigest(),
    'sources': [{'path': path, 'sha256': hashlib.sha256(data).hexdigest()} for path, data in zip(paths, originals)],
    'producerSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'current016InstallationQualified': False, 'r4Qualified': False, 'r5Qualified': False}
(root / 'docs/helix/04-build/evidence/design-audit/pgserver-corrected-isolation.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({'historicalCheckPassed': True, 'nestedObservations': 5, 'r4Qualified': False}))
