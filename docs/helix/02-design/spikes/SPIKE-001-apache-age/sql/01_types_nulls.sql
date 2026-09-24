-- C2 / C3 / C8: value fidelity of agtype properties (Apache AGE 1.8.0 on PostgreSQL 18.6)
-- Each probe writes a property through Cypher, then reads it back (a) through Cypher and
-- (b) as the raw stored agtype text of the label table, so storage and output are both visible.
\pset pager off
LOAD 'age';
SET search_path = ag_catalog, "$user", public;
SELECT drop_graph('fid', true) FROM ag_graph WHERE name = 'fid';
SELECT create_graph('fid');

\echo '==== C2.1 int64 boundaries'
SELECT * FROM cypher('fid', $$ CREATE (n:V {k:'int', max: 9223372036854775807, min: -9223372036854775808}) RETURN n.max, n.min $$) AS (max agtype, min agtype);
SELECT * FROM cypher('fid', $$ RETURN 9223372036854775808 $$) AS (overflow_literal agtype);
SELECT * FROM cypher('fid', $$ RETURN 9223372036854775807 + 1 $$) AS (overflow_arith agtype);
SELECT * FROM cypher('fid', $$ MATCH (n:V {k:'int'}) RETURN n.max = 9223372036854775807, n.min = -9223372036854775808, n.max - 1 $$) AS (eq_max agtype, eq_min agtype, max_minus_1 agtype);

\echo '==== C2.2 decimals: plain literal vs ::numeric, and scale'
SELECT * FROM cypher('fid', $$ CREATE (n:V {k:'dec', d_plain: 12345678901234567890.123456789, d_num: 12345678901234567890.123456789::numeric, s_plain: 0.10, s_num: 0.10::numeric, s_num2: 1.500::numeric}) RETURN n.d_plain, n.d_num, n.s_plain, n.s_num, n.s_num2 $$) AS (d_plain agtype, d_num agtype, s_plain agtype, s_num agtype, s_num2 agtype);
SELECT * FROM cypher('fid', $$ MATCH (n:V {k:'dec'}) RETURN n.s_num = 0.1::numeric, n.s_num + 0.20::numeric, n.d_num * 1 $$) AS (eq agtype, sum agtype, times_int agtype);
\echo '-- decimals passed as a parameter map (text agtype input): JSON number vs ::numeric annotation'
SELECT '{"d": 12345678901234567890.123456789}'::agtype AS json_number_input;
SELECT '{"d": 12345678901234567890.123456789::numeric}'::agtype AS annotated_input;
SELECT '12345678901234567890'::agtype AS int_over_range_input;
PREPARE put_dec(agtype) AS SELECT * FROM cypher('fid', $$ CREATE (n:V {k:'decparam', d: $d, s: $s}) RETURN n.d, n.s $$, $1) AS (d agtype, s agtype);
EXECUTE put_dec('{"d": 12345678901234567890.123456789, "s": 0.10}');
EXECUTE put_dec('{"d": 12345678901234567890.123456789::numeric, "s": 0.10::numeric}');

\echo '==== C2.3 floats and special values'
SELECT * FROM cypher('fid', $$ CREATE (n:V {k:'flt', a: 0.1, b: 1.7976931348623157e308, c: 5e-324, d: -0.0, e: 'NaN'::float, f: '-Infinity'::float, g: 0.1 + 0.2}) RETURN n.a, n.b, n.c, n.d, n.e, n.f, n.g $$) AS (a agtype, b agtype, c agtype, d agtype, e agtype, f agtype, g agtype);

\echo '==== C2.4 Unicode strings: emoji, combining vs precomposed, U+0000'
SELECT * FROM cypher('fid', $$ CREATE (n:V {k:'str', emoji: 'thumbs 👍🏽 ok', comb: 'é', pre: 'é'}) RETURN n.emoji, n.comb, n.pre, n.comb = n.pre, size(n.comb), size(n.pre) $$) AS (emoji agtype, comb agtype, pre agtype, same agtype, len_comb agtype, len_pre agtype);
SELECT * FROM cypher('fid', $$ CREATE (n:V {k:'nul', s: 'a\u0000b'}) RETURN n.s $$) AS (s agtype);
SELECT '{"s": "a\u0000b"}'::agtype AS nul_via_text_input;

\echo '==== C2.5 binary data: is there a bytes type?'
SELECT * FROM cypher('fid', $$ RETURN '\x00ff'::bytea $$) AS (b agtype);
SELECT * FROM cypher('fid', $$ RETURN '\x00ff'::bytes $$) AS (b agtype);
SELECT '\x00ff'::bytea::agtype AS bytea_to_agtype;

\echo '==== C2.6 temporal: date / time / timestamp types or functions?'
SELECT * FROM cypher('fid', $$ RETURN date('2026-09-24') $$) AS (d agtype);
SELECT * FROM cypher('fid', $$ RETURN datetime('2026-09-24T10:00:00+02:00') $$) AS (d agtype);
SELECT * FROM cypher('fid', $$ RETURN localtime('10:00:00') $$) AS (d agtype);
SELECT * FROM cypher('fid', $$ RETURN '2026-09-24'::date $$) AS (d agtype);
SELECT * FROM cypher('fid', $$ RETURN timestamp() > 0 $$) AS (timestamp_fn_is_epoch_ms agtype);
SELECT now()::agtype AS timestamptz_to_agtype;
SELECT to_jsonb(now())::agtype AS via_jsonb_becomes_string;

\echo '==== C8 nested maps, lists and arbitrary (unknown) keys'
SELECT * FROM cypher('fid', $$ CREATE (n:V {k:'nest', unknown_key_1: {a: {b: {c: [1, {d: 'x'}, [2, 3]]}}}, `key with spaces`: 1, `ключ`: 'v', `👍`: true}) RETURN properties(n) $$) AS (p agtype);
SELECT * FROM cypher('fid', $$ MATCH (n:V {k:'nest'}) RETURN keys(n) $$) AS (keys agtype);

\echo '==== C3.1 absent vs explicit null'
SELECT * FROM cypher('fid', $$ CREATE (n:V {k:'nul1', p: null, q: 1}) RETURN properties(n), keys(n) $$) AS (props agtype, keys agtype);
SELECT * FROM cypher('fid', $$ MATCH (n:V {k:'nul1'}) SET n.q = null RETURN properties(n), keys(n) $$) AS (props agtype, keys agtype);
SELECT * FROM cypher('fid', $$ MATCH (n:V {k:'nul1'}) RETURN n.p IS NULL, n.never_set IS NULL, exists(n.p), exists(n.never_set) $$) AS (p_null agtype, never_null agtype, p_exists agtype, never_exists agtype);
SELECT * FROM cypher('fid', $$ MATCH (n:V {k:'nul1'}) SET n += {r: null, s: 2} RETURN properties(n) $$) AS (props agtype);
SELECT * FROM cypher('fid', $$ MATCH (n:V {k:'nul1'}) SET n = {k:'nul1', t: null} RETURN properties(n) $$) AS (props agtype);
PREPARE put_null(agtype) AS SELECT * FROM cypher('fid', $$ CREATE (n:V {k:'nulparam', p: $p}) RETURN properties(n) $$, $1) AS (props agtype);
EXECUTE put_null('{"p": null}');
SELECT * FROM cypher('fid', $$ MATCH (n:V) WHERE n.k IN ['nul1','nulparam'] RETURN n.k, properties(n) $$) AS (k agtype, props agtype);

\echo '==== C3.2 lists (order, duplicates, null elements) and maps with null values'
SELECT * FROM cypher('fid', $$ CREATE (n:V {k:'lst', l: [3, 1, 3, null, 1, 'x', [1,1]], empty_l: [], m: {a: null, b: 1, c: [null]}, empty_m: {}}) RETURN n.l, n.empty_l, n.m, n.empty_m, keys(n.m) $$) AS (l agtype, empty_l agtype, m agtype, empty_m agtype, mkeys agtype);

\echo '==== raw stored agtype text in the label table (what plain SQL sees)'
SELECT id, properties::text FROM fid."V" ORDER BY id;

\echo '==== C2 follow-up probes'
\echo '-- numeric from a string literal cast inside Cypher (avoids the float literal path?)'
SELECT * FROM cypher('fid', $$ RETURN '12345678901234567890.123456789'::numeric, '0.10'::numeric $$) AS (a agtype, b agtype);
\echo '-- integer overflow on stored values'
SELECT * FROM cypher('fid', $$ MATCH (n:V {k:'int'}) RETURN n.max + 1 $$) AS (r agtype);
SELECT * FROM cypher('fid', $$ MATCH (n:V {k:'int'}) RETURN n.max * 2 $$) AS (r agtype);
SELECT * FROM cypher('fid', $$ MATCH (n:V {k:'int'}) RETURN n.min - 1 $$) AS (r agtype);
SELECT * FROM cypher('fid', $$ MATCH (n:V {k:'int'}) RETURN -n.min $$) AS (r agtype);
SELECT * FROM cypher('fid', $$ MATCH (n:V {k:'int'}) RETURN abs(n.min) $$) AS (r agtype);
SELECT * FROM cypher('fid', $$ MATCH (n:V {k:'int'}) RETURN n.max + 1.0 $$) AS (r agtype);
SELECT * FROM cypher('fid', $$ MATCH (n:V {k:'int'}) RETURN 9223372036854775807 * 2 $$) AS (r agtype);
SELECT * FROM cypher('fid', $$ MATCH (n:V {k:'int'}) SET n.wrapped = n.max + 1 RETURN n.wrapped $$) AS (stored agtype);
\echo '-- SQL side: same arithmetic on bigint errors'
SELECT 9223372036854775807::bigint + 1;
\echo '-- toInteger / toFloat on big values'
SELECT * FROM cypher('fid', $$ RETURN toInteger('9223372036854775807'), toInteger('9223372036854775808'), toFloat(9007199254740993) $$) AS (a agtype, b agtype, c agtype);
