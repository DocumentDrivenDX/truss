; benchmark generated from python API
(set-info :status unknown)
(declare-fun final_private_privilege () Bool)
(declare-fun initial_private_privilege () Bool)
(declare-fun permit () Bool)
(declare-fun release () Bool)
(assert
 (let (($x11 (not final_private_privilege)))
 (let (($x10 (not initial_private_privilege)))
 (= release (and permit $x10 $x11)))))
(assert
 initial_private_privilege)
(assert
 release)
(check-sat)
