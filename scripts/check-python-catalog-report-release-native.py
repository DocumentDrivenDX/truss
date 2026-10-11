#!/usr/bin/env python3
"""Retired historical frozen-source catalog-report experiment producer.

Original sources and receipts remain in the HELIX evidence archives. Current
catalog-report tests use the installed17.11 suite and owned fixture lifecycle.
"""
raise SystemExit(
    'Historical catalog-report producer retired. Run scripts/qualify-pgserver-pg17.py '
    'with an installed Truss wheel, a fresh --run-id and --workers; '
    'the installed suite covers current report, dispatch and staging modules.'
)
