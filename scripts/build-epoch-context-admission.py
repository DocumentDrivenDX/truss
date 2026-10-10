"""Same-original-operation epoch observation, not trusted installation authority."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
s=(root/'packages/postgresql/native/operation-asserted-origin-admission.sql').read_text()
s=s.replace('runtime_admit_operation_with_asserted_origin(', 'runtime_admit_operation_with_epoch_context(')
s=s.replace('asserted_bytes bytea, capture_profile_bytes bytea\n','asserted_bytes bytea, capture_profile_bytes bytea,\n  expected_installation text, expected_epoch text, expected_incarnation text\n')
s=s.replace('  native_context bytea;', '  native_context bytea;\n  epoch_capture record;')
s=s.replace('  -- Catalog exclusion precedes', '''  -- Lock/observe original current epoch before catalog/business admission.
  -- Expected values compare facts; trusted deployment admission is separate.
  SELECT * INTO STRICT epoch_capture FROM truss.runtime_lock_source_epoch(
    expected_installation,expected_epoch,expected_incarnation);
  -- Catalog exclusion precedes''')
s=s.replace('  -- Catalog exclusion precedes', """  total_bytes := total_bytes + (octet_length(epoch_capture.profile_hex)+octet_length(epoch_capture.evidence_hex))/2;
  IF total_bytes>4194304 THEN
    RAISE EXCEPTION 'original epoch artifact aggregate bound' USING ERRCODE='54000';
  END IF;
  -- Catalog exclusion precedes""")
s=s.replace('truss-native-operation-context/0.3','truss-native-operation-context/0.4')
s=s.replace("'assertedOriginCaptureProfileHex',encode(capture_profile_bytes,'hex')", "'assertedOriginCaptureProfileHex',encode(capture_profile_bytes,'hex'),\n    'installationId',epoch_capture.installation_id,'sourceEpoch',epoch_capture.source_epoch,\n    'targetIncarnation',epoch_capture.target_incarnation,\n    'sourceEpochProfileHex',epoch_capture.profile_hex,\n    'sourceEpochEvidenceHex',epoch_capture.evidence_hex")
s=s.replace('(text,bytea,bytea,bytea,bytea,bytea,bytea,bytea,bytea) FROM PUBLIC','(text,bytea,bytea,bytea,bytea,bytea,bytea,bytea,bytea,text,text,text) FROM PUBLIC')
s='-- Context0.4 original epoch/actor/asserted byte capture component; not complete installed admission.\n'+s
(root/'packages/postgresql/native/operation-epoch-context-admission.sql').write_text(s)
