; benchmark generated from python API
(set-info :status unknown)
(declare-fun initial_private_privilege () Bool)
(declare-fun permit () Bool)
(declare-fun release () Bool)
(declare-fun final_private_privilege () Bool)
(assert
 (= release (and permit (not initial_private_privilege))))
(assert
 (not initial_private_privilege))
(assert
 final_private_privilege)
(assert
 release)
(check-sat)
