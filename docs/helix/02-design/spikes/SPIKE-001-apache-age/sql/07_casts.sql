-- C10: reading AGE-stored values from plain SQL and converting agtype to ordinary SQL types.
-- Uses the 'fid' graph from 01_types_nulls.sql. AGE 1.8.0 / PG 18.6.
\pset pager off
LOAD 'age';
SET search_path = ag_catalog, "$user", public;

\echo '==== C10.1 available casts from agtype (pg_cast)'
SELECT castsource::regtype AS source, casttarget::regtype AS target, castcontext AS context FROM pg_cast WHERE castsource = 'agtype'::regtype ORDER BY 2::text;

\echo '==== C10.2 plain SQL over the label table: operators ->, ->> and casts'
SELECT properties ->> 'k'::text AS k_text, (properties -> 'max'::text)::bigint AS max_bigint, (properties -> 'min'::text)::bigint AS min_bigint
FROM fid."V" WHERE properties @> '{"k": "int"}';
SELECT (properties -> 'emoji'::text)::text AS string_via_text_cast, properties ->> 'emoji'::text AS string_via_arrow_text FROM fid."V" WHERE properties @> '{"k": "str"}';
SELECT (properties -> 'a'::text)::float8 AS f, (properties -> 'e'::text)::float8 AS nan, (properties -> 'f'::text)::float8 AS neg_inf FROM fid."V" WHERE properties @> '{"k": "flt"}';

\echo '==== C10.3 exact decimals: there is no agtype -> numeric cast'
SELECT (properties -> 'd'::text)::numeric AS direct_numeric FROM fid."V" WHERE properties @> '{"k": "decparam"}' AND properties ->> 'd'::text LIKE '%123456789%';
SELECT (properties -> 'd'::text)::text AS as_text, properties ->> 'd'::text AS arrow_text FROM fid."V" WHERE properties @> '{"k": "decparam"}';
SELECT rtrim(properties ->> 's'::text, ':numeric')::numeric AS workaround_strip_suffix FROM fid."V" WHERE properties @> '{"k": "decparam"}';
SELECT (properties -> 'd'::text)::jsonb AS via_jsonb, ((properties -> 'd'::text)::jsonb)::numeric AS jsonb_then_numeric,
       ((properties -> 's'::text)::jsonb)::numeric AS scale_via_jsonb FROM fid."V" WHERE properties @> '{"k": "decparam"}';
SELECT properties::jsonb AS whole_map_as_jsonb FROM fid."V" WHERE properties @> '{"k": "int"}';

\echo '==== C10.4 lossy or surprising conversions'
SELECT '1.9'::agtype::int AS float_to_int, '1.5'::agtype::bigint AS half_to_bigint, '-1.5'::agtype::bigint AS neg_half;
SELECT '9223372036854775807'::agtype::int AS bigint_to_int_overflow;
SELECT '"42"'::agtype::int AS string_to_int;
SELECT '"true"'::agtype::boolean AS string_to_bool;
SELECT '9007199254740993'::agtype::float8 AS big_int_to_float8;
SELECT 'null'::agtype::int IS NULL AS agtype_null_to_sql_null;


\echo '==== C10.6 exact decimal via ->> text then ::numeric, and type ambiguity of the text path'
SELECT (properties ->> 'd'::text)::numeric AS exact_numeric, (properties ->> 's'::text)::numeric AS exact_scale FROM fid."V" WHERE properties @> '{"k": "decparam"}' AND properties ->> 's'::text = '0.10';
SELECT '{"a": "0.10", "b": 0.10::numeric, "c": 0.1}'::agtype ->> 'a'::text AS string_val, '{"a": "0.10", "b": 0.10::numeric, "c": 0.1}'::agtype ->> 'b'::text AS numeric_val, '{"a": "0.10", "b": 0.10::numeric, "c": 0.1}'::agtype ->> 'c'::text AS float_val;
SELECT '0.10::numeric'::agtype::jsonb AS numeric_to_jsonb;
SELECT '0.1'::agtype::jsonb AS float_to_jsonb;
SELECT '{"f": 0.1}'::agtype::jsonb AS map_with_float_to_jsonb;
SELECT '{"n": 12345678901234567890.123456789::numeric, "s": 0.10::numeric}'::agtype::jsonb AS map_with_numeric_to_jsonb;

\echo '==== C10.5 a typed relational view over the graph for other tools'
CREATE OR REPLACE VIEW public.v_fid_int AS
SELECT id::text AS vertex_id, properties ->> 'k'::text AS k, (properties -> 'max'::text)::bigint AS max_value
FROM fid."V" WHERE properties ? 'max'::text;
SELECT * FROM public.v_fid_int;
\echo '-- the same view read by a role with SELECT only on the view (no AGE search_path, no LOAD)'
DROP ROLE IF EXISTS reader; CREATE ROLE reader LOGIN;
GRANT USAGE ON SCHEMA public TO reader; GRANT SELECT ON public.v_fid_int TO reader;
\c - reader
SELECT * FROM public.v_fid_int;
\c - postgres
