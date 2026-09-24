#!/usr/bin/env bash
# Repeatable build: PostgreSQL 18.6 from the GitHub mirror + Apache AGE PG18/v1.8.0-rc0
set -euo pipefail
S="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
B=$S/build; P=$B/pg18
date -u +"start %FT%TZ"
DEBIAN_FRONTEND=noninteractive apt-get install -y -q flex bison libicu-dev pkg-config libreadline-dev zlib1g-dev >/dev/null
cd $B
[ -d postgres ] || git clone --depth 1 --branch REL_18_6 https://github.com/postgres/postgres.git postgres
cd postgres && git log -1 --format='postgres %H %cd' 
./configure --prefix=$P --without-icu --silent
make -j4 -s world-bin >/dev/null 2>&1 || make -j4 -s >/dev/null
make -s install >/dev/null
(cd contrib && make -s -j4 install >/dev/null)
date -u +"pg built %FT%TZ"
cd $B
[ -d age ] || git clone --depth 1 --branch PG18/v1.8.0-rc0 https://github.com/apache/age.git age
cd age && git log -1 --format='age %H %cd %s'
make -s PG_CONFIG=$P/bin/pg_config -j4 >/dev/null
make -s PG_CONFIG=$P/bin/pg_config install >/dev/null
date -u +"age built %FT%TZ"
