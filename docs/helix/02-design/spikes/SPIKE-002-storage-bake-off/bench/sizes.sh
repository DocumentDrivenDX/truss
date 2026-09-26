#!/usr/bin/env bash
# On-disk size per relation and per option on a fresh load (run before any write benchmark bloats the tables).
source "$(dirname "${BASH_SOURCE[0]}")/../env.sh"
echo "== fresh load (setup.sh), after the enforcement and fidelity suites only (their writes roll back); $(psql -X -At -c 'select version()')"
psql -X -c "SELECT n.nspname||'.'||c.relname AS rel, pg_class_n.reltuples::bigint AS rows, round(pg_relation_size(c.oid)/1048576.0,1) heap_mb, round(pg_indexes_size(c.oid)/1048576.0,1) idx_mb, round(pg_total_relation_size(c.oid)/1048576.0,1) total_mb FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace JOIN pg_class pg_class_n ON pg_class_n.oid=c.oid WHERE n.nspname IN ('sales','c') AND c.relkind='r' AND pg_total_relation_size(c.oid) > 100000 ORDER BY 1"
psql -X -c "SELECT n.nspname AS schema, round(sum(pg_total_relation_size(c.oid))/1048576.0,1) total_mb FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname IN ('sales','c') AND c.relkind='r' GROUP BY 1"
psql -X -c "SELECT indexrelname, round(pg_relation_size(indexrelid)/1048576.0,1) mb FROM pg_stat_user_indexes WHERE schemaname='c' AND relname IN ('object','edge') ORDER BY 2 DESC"
