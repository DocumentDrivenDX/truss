; benchmark generated from python API
(set-info :status unknown)
(declare-fun bounded_bytes () Bool)
(declare-fun valid_utf8 () Bool)
(declare-fun duplicate_members () Bool)
(declare-fun exact_keys () Bool)
(declare-fun wire_operation () String)
(declare-fun wire_version () String)
(declare-fun dispatch () Bool)
(assert
 (let (($x18 (not duplicate_members)))
 (let (($x19 (and (= wire_version "truss-owned-decision-request/0.1") (= wire_operation "read") exact_keys $x18 valid_utf8 bounded_bytes)))
 (= dispatch $x19))))
(assert
 duplicate_members)
(assert
 dispatch)
(check-sat)
