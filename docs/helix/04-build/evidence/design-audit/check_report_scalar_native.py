"""Temporary PostgreSQL scalar candidate versus original independent byte vectors."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
SOURCE = ROOT / 'docs/helix/02-design/contracts/report-scalar-bytes-v0.2.proposal.sql'
VECTORS = ROOT / 'docs/helix/03-test/report-scalar-stream-v0.1.proposal.vectors.json'
source = SOURCE.read_text()
fixture = json.loads(VECTORS.read_bytes())
statements = ['BEGIN;', "SET LOCAL statement_timeout='15s';",
              'CREATE TEMP TABLE scalar_anchor(value text) ON COMMIT DROP;',
              source.replace('truss.runtime_report_scalar_bytes_v0_2', 'pg_temp.runtime_report_scalar_bytes_v0_2'),
              "SELECT 'server|'||current_setting('server_version_num');"]
results = []
for vector in fixture['vectors']:
    original = b''.join(bytes.fromhex(p['hex']) * int(p['repeat']) for p in vector['sourceParts'])
    if len(original) > 131072: raise ValueError('Original fixture bound')
    literal = "decode('" + original.hex() + "','hex')"
    if vector['expectedUtf8Valid']:
        expected = b''.join(bytes.fromhex(p['hex']) * int(p['repeat']) for p in vector['expectedCanonicalParts'])
        if sha256(expected).hexdigest() != vector['expectedCanonicalSha256']:
            raise ValueError('Original expected hash mismatch')
        statements.append("SELECT '" + vector['name'] + "|'||encode(pg_temp.runtime_report_scalar_bytes_v0_2(" + literal + "),'hex');")
        results.append({'name': vector['name'], 'expected': vector['expectedCanonicalSha256'],
                        'expectedNativeHex': expected.hex()})
    else:
        statements.append("DO $$ BEGIN BEGIN PERFORM pg_temp.runtime_report_scalar_bytes_v0_2(" + literal + "); RAISE EXCEPTION 'invalid source accepted'; EXCEPTION WHEN SQLSTATE '22021' THEN NULL; END; END $$;")
        statements.append("SELECT '" + vector['name'] + "|refused_22021';")
        results.append({'name': vector['name'], 'expected': 'refused_22021'})
expanded = b'"' + b'\\u000a' * 200000 + b'"'
if len(json.dumps('\n' * 200000).encode('utf8')) >= 1048576 or len(expanded) <= 1048576:
    raise ValueError('Independent short-escape expansion boundary required')
statements.append("SELECT 'short-escape-expands-beyond-one-MiB|'||encode(pg_temp.runtime_report_scalar_bytes_v0_2(decode(repeat('0a',200000),'hex')),'hex');")
results.append({'name': 'short-escape-expands-beyond-one-MiB', 'expected': sha256(expanded).hexdigest(), 'expectedNativeHex': expanded.hex()})
boundary = b'"' + b'\\u0000' * 699050 + b'aa' + b'"'
statements += ["SELECT 'exact-output-capacity|'||encode(pg_temp.runtime_report_scalar_bytes_v0_2(decode(repeat('00',699050)||'6161','hex')),'hex');",
               "DO $$ BEGIN BEGIN PERFORM pg_temp.runtime_report_scalar_bytes_v0_2(decode(repeat('00',699050)||'616161','hex')); RAISE EXCEPTION 'one-over output accepted'; EXCEPTION WHEN SQLSTATE '54000' THEN NULL; END; END $$;",
               "SELECT 'one-over-output-capacity|refused_54000';"]
results += [{'name': 'exact-output-capacity', 'expected': sha256(boundary).hexdigest(), 'expectedNativeHex': boundary.hex()},
            {'name': 'one-over-output-capacity', 'expected': 'refused_54000'}]
statements += ["DO $$ BEGIN BEGIN PERFORM pg_temp.runtime_report_scalar_bytes_v0_2(decode(repeat('00',699051),'hex')); RAISE EXCEPTION 'output overflow accepted'; EXCEPTION WHEN SQLSTATE '54000' THEN NULL; END; END $$;",
               "SELECT 'output-capacity|refused_54000';",
               "DO $$ BEGIN BEGIN PERFORM pg_temp.runtime_report_scalar_bytes_v0_2(decode(repeat('61',1048577),'hex')); RAISE EXCEPTION 'source overflow accepted'; EXCEPTION WHEN SQLSTATE '54000' THEN NULL; END; END $$;",
               "SELECT 'source-capacity|refused_54000';", 'ROLLBACK;']
results += [{'name': 'output-capacity', 'expected': 'refused_54000'},
            {'name': 'source-capacity', 'expected': 'refused_54000'}]
run = subprocess.run(['docker', 'exec', '-i', 'truss-runtime-admission', 'psql',
                      '-X', '-q', '-A', '-t', '-v', 'ON_ERROR_STOP=1', '-U', 'postgres', '-d', 'postgres'],
                     input='\n'.join(statements), text=True, capture_output=True, timeout=120)
if run.returncode: raise RuntimeError(run.stderr)
lines = run.stdout.splitlines()
if len(lines) != len(results) + 1 or not lines[0].startswith('server|'):
    raise ValueError('Complete original native observation inventory required')
for expected, line in zip(results, lines[1:]):
    native_hex = expected.pop('expectedNativeHex', None)
    if line != expected['name'] + '|' + (native_hex if native_hex is not None else expected['expected']):
        raise ValueError('Independent native byte mismatch: ' + expected['name'])
    observed = line.split('|', 1)[1]
    if native_hex is not None:
        expected['completeOriginalBytesEqual'] = True
        expected['nativeBytes'] = len(bytes.fromhex(observed))
        expected['observed'] = sha256(bytes.fromhex(observed)).hexdigest()
    else:
        expected['observed'] = observed
receipt = {'status': 'passed_temporary_native_scalar_candidate', 'serverVersionNum': lines[0].split('|')[1],
           'observations': results, 'sourceSha256': sha256(SOURCE.read_bytes()).hexdigest(),
           'fixtureSha256': sha256(VECTORS.read_bytes()).hexdigest(),
           'checkerSha256': sha256(Path(__file__).read_bytes()).hexdigest(),
           'scope': 'Temporary function in one rolled-back native session; exact independent scalar bytes and invalid UTF-8/capacity refusals only. No installed routine, whole-report encoder, precharged native/driver resource profile, authority or acceptance effects.'}
(HERE / 'report-scalar-native.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(str(len(results)) + ' native scalar candidate observations passed; full report/account unqualified')
