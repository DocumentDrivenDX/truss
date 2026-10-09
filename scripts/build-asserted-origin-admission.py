"""Derive versioned capture from the original admission procedure, no repair UPDATE."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
s=(root/'packages/postgresql/native/operation-admission.sql').read_text()
s=s.replace('runtime_admit_operation(', 'runtime_admit_operation_with_asserted_origin(')
s=s.replace('candidate_bytes bytea, obligation_bytes bytea, group_bytes bytea\n','candidate_bytes bytea, obligation_bytes bytea, group_bytes bytea,\n  asserted_bytes bytea, capture_profile_bytes bytea\n')
s=s.replace('  FOREACH item IN ARRAY', '''  IF asserted_bytes IS NULL OR octet_length(asserted_bytes) NOT BETWEEN 1 AND 131072
    OR capture_profile_bytes IS NULL OR octet_length(capture_profile_bytes) NOT BETWEEN 1 AND 65536 THEN
    RAISE EXCEPTION 'original asserted capture bounds' USING ERRCODE='22023';
  END IF;
  FOREACH item IN ARRAY''')
s=s.replace('candidate_bytes,obligation_bytes,group_bytes]','candidate_bytes,obligation_bytes,group_bytes,asserted_bytes,capture_profile_bytes]')
s=s.replace('truss-native-operation-context/0.2','truss-native-operation-context/0.3')
s=s.replace("'database',current_database(),'backendPid',pg_backend_pid()::text", "'database',current_database(),'backendPid',pg_backend_pid()::text,\n    'assertedOriginUtf8Hex',encode(asserted_bytes,'hex'),\n    'assertedOriginCaptureProfileHex',encode(capture_profile_bytes,'hex')")
s=s.replace('  INSERT INTO truss.row_home_operation', '''  IF octet_length(native_context)>1048576 THEN
    RAISE EXCEPTION 'original encoded context bound' USING ERRCODE='54000';
  END IF;
  INSERT INTO truss.row_home_operation''')
s=s.replace('(text,bytea,bytea,bytea,bytea,bytea,bytea) FROM PUBLIC', '(text,bytea,bytea,bytea,bytea,bytea,bytea,bytea,bytea) FROM PUBLIC')
s='-- Context0.3 private byte-capture component; strict origin decoding/profile and installed authority remain separate.\n'+s
(root/'packages/postgresql/native/operation-asserted-origin-admission.sql').write_text(s)
