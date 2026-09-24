#!/usr/bin/env bash
# C7: concurrency behaviour of Cypher SET and MERGE (AGE 1.8.0 / PG 18.6).
set -u
source "$(dirname "${BASH_SOURCE[0]}")/../env.sh"
Q() { psql -X -q -At -v ON_ERROR_STOP=0 "$@"; }
PRE="LOAD 'age'; SET search_path = ag_catalog, \"\$user\", public;"

reset_graph() {
  Q -c "$PRE SELECT drop_graph('ccy', true) FROM ag_graph WHERE name='ccy';" -c "$PRE SELECT create_graph('ccy');" >/dev/null
  Q -c "$PRE SELECT * FROM cypher('ccy', \$\$ CREATE (:Acc {k: 1, cnt: 0}) \$\$) AS (x agtype);" >/dev/null
}
props() { Q -c "$PRE SELECT p::text FROM cypher('ccy', \$\$ MATCH (n:Acc {k: 1}) RETURN properties(n) \$\$) AS (p agtype);" | tail -1; }

for ISO in "READ COMMITTED" "REPEATABLE READ"; do
  echo "==== C7.1 overlapping transactions SET different properties of one vertex ($ISO)"
  reset_graph
  ( Q -e -c "$PRE" -c "BEGIN ISOLATION LEVEL $ISO;" \
      -c "SELECT * FROM cypher('ccy', \$\$ MATCH (n:Acc {k: 1}) SET n.a = 1 RETURN properties(n) \$\$) AS (p agtype);" \
      -c "SELECT pg_sleep(3);" -c "COMMIT;" 2>&1 | sed 's/^/[A] /' ) &
  sleep 1
  ( Q -e -c "$PRE" -c "BEGIN ISOLATION LEVEL $ISO;" \
      -c "SELECT * FROM cypher('ccy', \$\$ MATCH (n:Acc {k: 1}) SET n.b = 2 RETURN properties(n) \$\$) AS (p agtype);" \
      -c "COMMIT;" 2>&1 | sed 's/^/[B] /' ) &
  wait
  echo "final properties: $(props)"
  echo
done

echo "==== C7.1b same overlap, plain SQL UPDATE on the label table for comparison (READ COMMITTED)"
reset_graph
( Q -e -c "BEGIN;" -c "UPDATE ccy.\"Acc\" SET properties = properties WHERE true;" -c "SELECT pg_sleep(3);" -c "COMMIT;" 2>&1 | sed 's/^/[A] /' ) &
sleep 1
( Q -e -c "$PRE" -c "BEGIN;" -c "SELECT * FROM cypher('ccy', \$\$ MATCH (n:Acc {k: 1}) SET n.b = 2 RETURN properties(n) \$\$) AS (p agtype);" -c "COMMIT;" 2>&1 | sed 's/^/[B] /' ) &
wait
echo "final properties: $(props)"
echo

echo "==== C7.2 8 clients x 100 autocommit increments of one counter: SET n.cnt = n.cnt + 1"
reset_graph
for c in $(seq 1 8); do
  ( for i in $(seq 1 100); do echo "SELECT * FROM cypher('ccy', \$\$ MATCH (n:Acc {k: 1}) SET n.cnt = n.cnt + 1 \$\$) AS (x agtype);"; done \
      | Q -c "$PRE" -f - 2>&1 | grep -c ERROR > $SPIKE/out/.c72_err_$c ) &
done
wait
ERR=$(cat $SPIKE/out/.c72_err_* | paste -sd+ | bc); rm -f $SPIKE/out/.c72_err_*
echo "attempted=800 errors=$ERR final=$(props)"
echo "sample error text:"
echo "SELECT * FROM cypher('ccy', \$\$ MATCH (n:Acc {k: 1}) SET n.cnt = n.cnt + 1 \$\$) AS (x agtype);" > /dev/null
( for c in 1 2 3 4; do ( for i in $(seq 1 50); do echo "SELECT * FROM cypher('ccy', \$\$ MATCH (n:Acc {k: 1}) SET n.cnt = n.cnt + 1 \$\$) AS (x agtype);"; done | Q -c "$PRE" -f - 2>&1 | grep -m1 ERROR ) & done; wait ) | sort | uniq -c | head -3
echo

echo "==== C7.3 relational baseline: 8 clients x 100 UPDATE t SET cnt = cnt + 1"
Q -c "DROP TABLE IF EXISTS public.ctr; CREATE TABLE public.ctr(k int primary key, cnt int); INSERT INTO public.ctr VALUES (1, 0);"
for c in $(seq 1 8); do
  ( for i in $(seq 1 100); do echo "UPDATE public.ctr SET cnt = cnt + 1 WHERE k = 1;"; done | Q -f - 2>&1 | grep -c ERROR > $SPIKE/out/.c73_err_$c ) &
done
wait
ERR=$(cat $SPIKE/out/.c73_err_* | paste -sd+ | bc); rm -f $SPIKE/out/.c73_err_*
echo "attempted=800 errors=$ERR final cnt=$(Q -c 'SELECT cnt FROM public.ctr')"
echo

merge_run() {
  local label=$1
  for c in $(seq 1 8); do
    ( for i in $(seq 1 100); do echo "SELECT * FROM cypher('ccy', \$\$ MERGE (u:U {key: $(( (i + c) % 10 ))}) \$\$) AS (x agtype);"; done \
        | Q -c "$PRE" -f - 2>&1 | grep ERROR > $SPIKE/out/.merge_err_$c ) &
  done
  wait
  echo "[$label] MERGE attempts=800 over 10 keys; errors=$(cat $SPIKE/out/.merge_err_* | wc -l)"
  cat $SPIKE/out/.merge_err_* | sed 's/^psql:<stdin>:[0-9]*: //' | sort | uniq -c | head -3
  rm -f $SPIKE/out/.merge_err_*
  Q -c "$PRE SELECT key::text, count(*) FROM cypher('ccy', \$\$ MATCH (u:U) RETURN u.key \$\$) AS (key agtype) GROUP BY 1 ORDER BY 1;" | tr '\n' ' '; echo
}
echo "==== C7.4 concurrent MERGE of the same keys, no unique index (8 clients, 10 keys)"
reset_graph
Q -c "$PRE SELECT create_vlabel('ccy','U');" >/dev/null
merge_run "no index"
echo "vertices per key shown as key|count; any count > 1 is a duplicate"
echo
echo "==== C7.5 concurrent MERGE with a unique expression index on U.key"
reset_graph
Q -c "$PRE SELECT create_vlabel('ccy','U');" >/dev/null
Q -c "$PRE CREATE UNIQUE INDEX u_key_uq ON ccy.\"U\" (agtype_access_operator(VARIADIC ARRAY[properties, '\"key\"'::agtype]));"
merge_run "unique index"
