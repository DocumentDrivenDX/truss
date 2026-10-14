# Required retained-value rebinding

SDK25/native61 with Weft26/backend31 passes four basic UMF0.7/0.8 workflows:
valid registration through reads/report/history/query/feed/retry, plus missing,
null and empty-container counts (36.500s combined run). A genuine installed
SDK24/native60 fixture upgrades and preserves original report bytes, then adds a
required retained field and reads version3/history/query (9.995s). The upgrade
fixture uses the supported autocommit host and ordinary statement timeout.

Astra Ultra reviewed the implementation and approved promotion after these
checks. UMF owner-export storage remains unchanged; native60 archival manifest
matches published v0.0.24 pins. No managed-service qualification is claimed.
