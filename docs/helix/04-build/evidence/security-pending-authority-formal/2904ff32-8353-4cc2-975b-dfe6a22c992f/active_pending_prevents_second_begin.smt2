; benchmark generated from python API
(set-info :status unknown)
(declare-fun already_pending () Bool)
(declare-fun begin_transition () Bool)
(assert
 (let (($x25 (not already_pending)))
 (=> begin_transition $x25)))
(assert
 already_pending)
(assert
 begin_transition)
(check-sat)
