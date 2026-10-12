; benchmark generated from python API
(set-info :status unknown)
(declare-fun final_private_privilege () Bool)
(declare-fun initial_private_privilege () Bool)
(declare-fun permit () Bool)
(declare-fun release () Bool)
(declare-fun intermediate_private_privilege () Bool)
(assert
 (let (($x11 (not final_private_privilege)))
 (let (($x10 (not initial_private_privilege)))
 (= release (and permit $x10 $x11)))))
(assert
 (not initial_private_privilege))
(assert
 intermediate_private_privilege)
(assert
 final_private_privilege)
(assert
 release)
(check-sat)
