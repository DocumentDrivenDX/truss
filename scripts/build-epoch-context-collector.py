"""Original context0.4 collector with independent current epoch correspondence."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
s=(root/'packages/postgresql/native/catalog-captured-context.sql').read_text()
s=s.replace('runtime_collect_catalog_captured_context(', 'runtime_collect_catalog_epoch_context(')
s=s.replace('context jsonb;', 'context jsonb; epoch_capture record;')
s=s.replace('jsonb_object_keys(context))<>11','jsonb_object_keys(context))<>16')
s=s.replace("'assertedOriginCaptureProfileHex']", "'assertedOriginCaptureProfileHex','installationId','sourceEpoch','targetIncarnation','sourceEpochProfileHex','sourceEpochEvidenceHex']")
s=s.replace('truss-native-operation-context/0.3','truss-native-operation-context/0.4')
needle=' RETURN QUERY SELECT'
s=s.replace(needle,""" SELECT * INTO STRICT epoch_capture FROM truss.runtime_lock_source_epoch(
  context->>'installationId',context->>'sourceEpoch',context->>'targetIncarnation');
 IF context->>'sourceEpochProfileHex' IS DISTINCT FROM epoch_capture.profile_hex
  OR context->>'sourceEpochEvidenceHex' IS DISTINCT FROM epoch_capture.evidence_hex THEN
  RAISE EXCEPTION 'original captured epoch evidence correspondence required' USING ERRCODE='55000';
 END IF;
"""+needle)
s='-- Context0.4 native epoch/actor/cut correspondence; trusted installation admission remains separate.\n'+s
(root/'packages/postgresql/native/catalog-epoch-context.sql').write_text(s)
