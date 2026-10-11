; benchmark generated from python API
(set-info :status unknown)
(declare-fun decision_permit () Bool)
(declare-fun release () Bool)
(declare-fun guard_active () Bool)
(assert
 (= release decision_permit))
(assert
 decision_permit)
(assert
 (not guard_active))
(assert
 release)
(check-sat)
