; benchmark generated from python API
(set-info :status unknown)
(declare-fun receiver_constructed () Bool)
(declare-fun bounded_bytes () Bool)
(declare-fun valid_utf8 () Bool)
(declare-fun duplicate_members () Bool)
(declare-fun exact_keys () Bool)
(declare-fun wire_operation () String)
(declare-fun wire_version () String)
(declare-fun dispatch () Bool)
(declare-fun delegated_profile () Bool)
(declare-fun captured_valid () Bool)
(declare-fun channels_closed () Bool)
(assert
 (let (($x18 (not duplicate_members)))
 (let (($x19 (and (= wire_version "truss-owned-decision-request/0.1") (= wire_operation "read") exact_keys $x18 valid_utf8 bounded_bytes)))
 (let (($x24 (= receiver_constructed (and captured_valid delegated_profile))))
 (and $x24 (= dispatch (and $x19 receiver_constructed)))))))
(assert
 dispatch)
(assert
 (not channels_closed))
(check-sat)
