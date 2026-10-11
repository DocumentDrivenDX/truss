; benchmark generated from python API
(set-info :status unknown)
(declare-fun decision_permit () Bool)
(declare-fun guard_active () Bool)
(declare-fun executor_verified () Bool)
(declare-fun caller_verified () Bool)
(declare-fun release () Bool)
(declare-fun caller_private_access () Bool)
(assert
 (let (($x11 (and caller_verified executor_verified guard_active decision_permit)))
 (= release $x11)))
(assert
 release)
(assert
 (not caller_private_access))
(check-sat)
