"""Reuse pinned UMF browser assets with the current reviewed Truss catalog."""
from pathlib import Path
import subprocess, json, hashlib, sys
root=Path(__file__).resolve().parents[1]
owner=Path('/Users/erik/Projects/umf')
revision='c433cfcdde21995803aad65234f20ba95d8c3222'
base='docs/helix/05-deploy/microsite/dist/'
def upstream(name):
 return subprocess.check_output(['git','show',revision+':'+base+name],cwd=owner)
outputs={name:upstream(name) for name in ['explorer.js','explorer.css','style.css','logo.svg']}
html=upstream('explorer.html').decode()
main=html[html.index('<main'):html.index('</main>')+7]
main=main.replace('Explore the shape<br><em>and the meaning.</em>','Explore the Truss storage schema.').replace('Browse domain packs, follow their references, and inspect the details that travel with each schema.','Inspect the reviewed layout 0.15 structural projection: tables, columns, keys, relationships, and retained native metadata.')
outputs['index.html']=('''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Truss schema browser</title><link rel="stylesheet" href="style.css"><link rel="stylesheet" href="explorer.css"></head><body>'''+main+'<script type="module" src="explorer.js"></script></body></html>\n').encode()
source=root/'docs/helix/02-design/models/truss-layout-core-structural-0.3.proposal.umf.json'
outputs['schema-catalog.json']=(json.dumps({'version':1,'entries':[{'id':'truss-layout','title':'Truss storage layout','category':'domain','path':'truss-layout.umf.json','text':source.read_text(),'format':'json','description':'Structural projection 0.3 of native layout 0.15. Native-only semantics are retained; inspection does not certify installation or complete DDL equivalence.'}]},indent=2)+'\n').encode()
outputs['truss-layout.umf.json']=source.read_bytes()
manifest={'owner':'DocumentDrivenDX/umf','revision':revision,'model':str(source.relative_to(root)),'assets':{k:hashlib.sha256(v).hexdigest() for k,v in outputs.items()},'scope':'Unmodified UMF browser JS/CSS; Truss HTML shell and exact current schema catalog. No production deployment.'}
outputs['manifest.json']=(json.dumps(manifest,indent=2)+'\n').encode()
out=root/'website/static/schema';out.mkdir(parents=True,exist_ok=True)
for name,data in outputs.items():
 target=out/name
 if '--check' in sys.argv: assert target.read_bytes()==data,name
 else: target.write_bytes(data)
print('Pinned UMF schema browser assets and exact Truss catalog verified.')
