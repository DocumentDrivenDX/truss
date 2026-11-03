-- SPDX-License-Identifier: MIT OR Apache-2.0
-- Fresh native0.76 schema source. This is not an upgrade or data migration.
ALTER TABLE truss.prop_def ADD COLUMN native_temporal jsonb;
ALTER TABLE truss.prop_def ADD CONSTRAINT prop_def_local_temporal_source CHECK (
 CASE WHEN scalar_type='localTimestamp' THEN
  cardinality='one' AND home='json' AND item IS NULL AND coalesce(facets,'{}')='{}'::jsonb
  AND jsonb_typeof(native_temporal)='object'
  AND native_temporal-ARRAY['profile','kind','source']='{}'::jsonb
  AND native_temporal->>'profile'='truss.local-timestamp/0.1' AND native_temporal->>'kind'='local'
  AND jsonb_typeof(native_temporal->'source')='object'
  AND native_temporal->'source'-ARRAY['documentId','sha256','record','field','fieldViewPointer']='{}'::jsonb
  AND jsonb_typeof(native_temporal->'source'->'documentId')='string'
  AND jsonb_typeof(native_temporal->'source'->'sha256')='string'
  AND native_temporal->'source'->>'sha256' ~ '^[0-9a-f]{64}$'
  AND jsonb_typeof(native_temporal->'source'->'fieldViewPointer')='string'
  AND jsonb_typeof(native_temporal->'source'->'record')='object'
  AND native_temporal->'source'->'record'-ARRAY['module','element']='{}'::jsonb
  AND jsonb_typeof(native_temporal->'source'->'field')='object'
  AND native_temporal->'source'->'field'-ARRAY['module','element']='{}'::jsonb
 ELSE native_temporal IS NULL END IS TRUE);
