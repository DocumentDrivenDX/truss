#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Archive the independent HF conformance corpus and its runner so it can run outside the checkout."""
import argparse,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
paths=[ROOT/'scripts/run-hf-conformance.py',ROOT/'scripts/native_fixture.py']
paths+=[q for q in (ROOT/'packages/python/tests').rglob('*') if q.is_file() and '__pycache__' not in q.parts and q.suffix!='.pyc']
paths+=[ROOT/'packages/python'/name for name in ('LICENSE.md','LICENSE-MIT','LICENSE-APACHE')]
a.output.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(a.output,'w',zipfile.ZIP_DEFLATED) as z:
 for path in sorted(set(paths)):
  if not path.exists():continue
  info=zipfile.ZipInfo(str(path.relative_to(ROOT)),date_time=(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
  z.writestr(info,path.read_bytes())
print(a.output)
