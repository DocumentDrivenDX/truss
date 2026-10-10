"""Versioned collector preserves original native actor and cut checks."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
s=(root/'packages/postgresql/native/catalog-original-context.sql').read_text()
s=s.replace('runtime_collect_catalog_original_context(', 'runtime_collect_catalog_captured_context(')
s=s.replace('count(*) FROM jsonb_object_keys(context))<>9','count(*) FROM jsonb_object_keys(context))<>11')
s=s.replace("'actorRoleOid','sessionRoleOid']", "'actorRoleOid','sessionRoleOid','assertedOriginUtf8Hex','assertedOriginCaptureProfileHex']")
s=s.replace('truss-native-operation-context/0.2','truss-native-operation-context/0.3')
needle="  OR context->>'xid' IS DISTINCT FROM expected_writer"
s=s.replace(needle,"""  OR context->>'assertedOriginUtf8Hex' !~ '^([0-9a-f]{2})+$'
  OR octet_length(context->>'assertedOriginUtf8Hex') NOT BETWEEN 2 AND 262144
  OR context->>'assertedOriginCaptureProfileHex' !~ '^([0-9a-f]{2})+$'
  OR octet_length(context->>'assertedOriginCaptureProfileHex') NOT BETWEEN 2 AND 131072
"""+needle)
s='-- Versioned context0.3 collector: captured bytes, not complete installed-profile authority.\n'+s
(root/'packages/postgresql/native/catalog-captured-context.sql').write_text(s)
