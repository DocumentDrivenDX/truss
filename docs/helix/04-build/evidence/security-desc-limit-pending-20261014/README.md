# Pending descending-order limit control

The original native ontology fixture now retains an opt-in regression control (`TRUSS_SECURITY_ONTOLOGY_DESC_LIMIT=1`): `SELECT r.resourceId FROM Resource r ORDER BY r.resourceId DESC LIMIT 1`. Bob must receive RB; revoked Alice and Outsider must receive no rows. Hidden ownerless RO sorts before RB under descending order, so this control detects applying LIMIT before security eligibility.

The first attempt failed after 45.392 seconds because the original relational producer rejected `desc` with WFT-UNSUPPORTED, parse span 58..62. No descending execution SQL or successful native result was emitted. The retained terminal log records the enclosing test failure. The control remains opt-in pending genuine original direction-bearing compiler support; ascending order is not a substitute.

This is pending component coverage toward Truss B01/B03 and US-056-AC2. It does not qualify those complete acceptance cases, change the original 132-case inventory, close pg-raw.B10, or authorize public activation. The previously passing filter/count/group/publication controls remain enabled normally.
