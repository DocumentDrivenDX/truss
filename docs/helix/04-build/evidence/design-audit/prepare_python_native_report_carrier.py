"""Closed stdin/stdout private carrier bridge; no database access or authority."""
import json
from importlib.metadata import version
from pathlib import Path
import sys
from python_report_wire_candidate import ReportWireCandidate

if len(sys.argv) != 1:
    raise SystemExit('No arguments accepted')
contracts = Path(__file__).resolve().parents[3] / '02-design/contracts'
source = sys.stdin.buffer.read(1048577)
result = ReportWireCandidate(contracts).prepare_native(source)
print(json.dumps({'originalUtf8Hex': result.original.source_bytes.hex(),
                  'nativeTreeText': result.native_tree_text,
                  'nativeTaskCount': result.native_task_count,
                  'environment': {'python': sys.version, 'jsonschema': version('jsonschema'),
                                  'referencing': version('referencing')}}, separators=(',', ':')))
