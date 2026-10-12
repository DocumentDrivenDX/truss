; benchmark generated from python API
(set-info :status unknown)
(declare-fun lost_guard () Bool)
(declare-fun reacquired_guard () Bool)
(declare-fun captured_guard () Bool)
(declare-fun observed_guard () Bool)
(declare-fun permit () Bool)
(declare-fun release () Bool)
(assert
 (let (($x15 (= observed_guard (or (and captured_guard (not lost_guard)) reacquired_guard))))
 (and $x15 (=> reacquired_guard lost_guard))))
(assert
 (= release (and permit observed_guard)))
(assert
 captured_guard)
(assert
 lost_guard)
(assert
 (not reacquired_guard))
(assert
 release)
(check-sat)
