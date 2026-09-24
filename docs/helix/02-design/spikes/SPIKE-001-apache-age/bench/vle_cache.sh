#!/usr/bin/env bash
# C12 addendum: cost of the first variable-length (VLE) query per new session, and after a write.
source "$(dirname "${BASH_SOURCE[0]}")/../env.sh"
export PGOPTIONS='-c search_path=ag_catalog,public'
Q="SELECT count(*) FROM cypher('bench', \$\$ MATCH (a:Person)-[:KNOWS*1..3]->(d:Person) WHERE a.uid = 4242 RETURN d.uid \$\$) AS (u agtype);"
echo "== VLE first-query cost per new session (graph cache build), 3 fresh sessions, each runs the same query 3 times"
for s in 1 2 3; do echo "-- session $s"; psql -X -At -c '\timing on' -c "$Q" -c "$Q" -c "$Q" 2>&1 | grep -E "^Time|^[0-9]+$" | paste -sd' '; done
echo "== after a write in the same session (per-graph version counter invalidates the cache)"
psql -X -At -c '\timing on' -c "$Q" -c "SELECT * FROM cypher('bench', \$\$ CREATE (:Person {uid: 999999}) \$\$) AS (x agtype);" -c "$Q" -c "$Q" 2>&1 | grep -E "^Time|^[0-9]+$" | paste -sd' '
psql -X -q -c "SELECT * FROM cypher('bench', \$\$ MATCH (p:Person {uid: 999999}) DELETE p \$\$) AS (x agtype);" >/dev/null
