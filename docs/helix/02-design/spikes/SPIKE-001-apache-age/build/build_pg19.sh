#!/usr/bin/env bash
# C1 addendum: PostgreSQL 19 beta 4 (GitHub mirror tag REL_19_BETA4) + AGE tag PG19/v1.8.0-rc0, then a smoke test.
set -euo pipefail
S="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
B=$S/build; P=$B/pg19; R=/var/lib/postgresql/age-spike19
date -u +"start %FT%TZ"
cd $B
[ -d postgres19 ] || git clone -q --depth 1 --branch REL_19_BETA4 https://github.com/postgres/postgres.git postgres19
cd postgres19 && git log -1 --format='postgres %H %cd'
./configure --prefix=$P --without-icu --silent
make -j4 -s >/dev/null 2>&1; make -s install >/dev/null
cd $B
[ -d age19 ] || git clone -q --depth 1 --branch PG19/v1.8.0-rc0 https://github.com/apache/age.git age19
cd age19 && git log -1 --format='age %H %cd %s'
make -s PG_CONFIG=$P/bin/pg_config -j4 >/dev/null 2>&1 && make -s PG_CONFIG=$P/bin/pg_config install >/dev/null
date -u +"built %FT%TZ"
rm -rf $R; mkdir -p $R; cp -a $P $R/; chown -R postgres:postgres $R
su postgres -c "$R/pg19/bin/initdb -D $R/data -E UTF8 --locale=C.UTF-8 -U postgres >/dev/null && echo \"shared_preload_libraries='age'
port=54319
listen_addresses=''
unix_socket_directories='$R'\" >> $R/data/postgresql.conf && $R/pg19/bin/pg_ctl -D $R/data -l $R/server.log start >/dev/null"
sleep 2
$R/pg19/bin/psql -X -h $R -p 54319 -U postgres -e -c "SELECT version();" -c "CREATE EXTENSION age;" -c "SELECT extversion FROM pg_extension WHERE extname='age';" \
  -c "SET search_path = ag_catalog, public;" -c "SELECT create_graph('smoke');" \
  -c "SELECT * FROM cypher('smoke', \$\$ CREATE (a:P {n: 1})-[:K]->(b:P {n: 2})-[:K]->(c:P {n: 3}) \$\$) AS (x agtype);" \
  -c "SELECT * FROM cypher('smoke', \$\$ MATCH (a:P {n: 1})-[:K*1..2]->(x) RETURN x.n ORDER BY x.n \$\$) AS (n agtype);" \
  -c "SELECT * FROM cypher('smoke', \$\$ MERGE (p:P {n: 9}) ON CREATE SET p.created = true RETURN properties(p) \$\$) AS (p agtype);" 2>&1
su postgres -c "$R/pg19/bin/pg_ctl -D $R/data stop >/dev/null"
date -u +"done %FT%TZ"
