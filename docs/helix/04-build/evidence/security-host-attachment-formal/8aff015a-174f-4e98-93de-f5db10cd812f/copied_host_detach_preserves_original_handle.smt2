; benchmark generated from python API
(set-info :status unknown)
(declare-fun before_usable () Bool)
(declare-fun registered_host () Int)
(declare-fun claimed_host () Int)
(declare-fun after_usable () Bool)
(assert
 (= after_usable (ite (= claimed_host registered_host) false before_usable)))
(assert
 (and (distinct claimed_host registered_host) true))
(assert
 before_usable)
(assert
 (not after_usable))
(check-sat)
