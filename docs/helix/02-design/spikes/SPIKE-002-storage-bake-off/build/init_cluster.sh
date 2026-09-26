#!/usr/bin/env bash
# Initialise and start one cluster (PGVER=17 or 18) owned by the postgres OS user, then create database "bakeoff".
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/../env.sh"
mkdir -p "$(dirname "$PGDATA")"; chown postgres: "$(dirname "$PGDATA")"
if [ ! -f "$PGDATA/PG_VERSION" ]; then
  su postgres -c "$PGBIN/initdb -D $PGDATA --locale=C.UTF-8 --encoding=UTF8 -U postgres -A trust" >/dev/null
  cat >> "$PGDATA/postgresql.conf" <<CONF
port = $PGPORT
unix_socket_directories = '/tmp'
listen_addresses = ''
shared_buffers = 1GB
work_mem = 64MB
maintenance_work_mem = 512MB
max_wal_size = 8GB
checkpoint_timeout = 30min
max_connections = 50
CONF
fi
su postgres -c "$PGBIN/pg_ctl -D $PGDATA -l $PGDATA/../server.log -w start" >/dev/null
psql -X -q -d postgres -c "CREATE DATABASE bakeoff" 2>/dev/null || true
psql -X -At -c "select version()"
