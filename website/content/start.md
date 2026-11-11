---
title: "Run it in five minutes."
description: "Install the Python package, start a private PostgreSQL and exercise Truss end to end."
number: "03"
---
## Install

```sh
python -m venv .venv && . .venv/bin/activate
pip install "umf-truss[local,native,query]" \
  --find-links https://github.com/DocumentDrivenDX/pgserver/releases/expanded_assets/pg18.6-pgv0.8.6-r2
```

Requires Python 3.11 or newer. The `local` extra brings PostgreSQL 18.6 (`pgserver-pg18`), whose wheels are GitHub release assets for now, hence `--find-links`. Python embeds V8; Bun and Node are not needed.

## Run the quickstart

```sh
curl -LO https://raw.githubusercontent.com/DocumentDrivenDX/truss/main/packages/python/examples/quickstart.py
curl -LO https://raw.githubusercontent.com/DocumentDrivenDX/truss/main/packages/python/examples/notes.umf.json
python quickstart.py ./truss-demo
# {"catalog": "accepted", "mutation": "committed", "lookup": "found", "query": "relationship", "feed_transactions": 2, "ack": "committed"}
```

It starts a private PostgreSQL on a Unix socket (no TCP listener), installs Truss, registers a UMF document, creates two notes and an edge, looks one up by key, runs a relationship query, and reads and acknowledges the change feed. CI runs this script against the built wheel on every change.

## Go further

- [Python API guide](https://github.com/DocumentDrivenDX/truss/blob/main/packages/python/README.md)
- [`adopter_workflow.py`](https://github.com/DocumentDrivenDX/truss/blob/main/packages/python/examples/adopter_workflow.py): receipts, replay, imports and dry runs
- [Architecture](https://github.com/DocumentDrivenDX/truss/blob/main/docs/helix/02-design/architecture.md), [decisions](https://github.com/DocumentDrivenDX/truss/tree/main/docs/helix/02-design/adr) and [contracts](https://github.com/DocumentDrivenDX/truss/tree/main/docs/helix/02-design/contracts)
