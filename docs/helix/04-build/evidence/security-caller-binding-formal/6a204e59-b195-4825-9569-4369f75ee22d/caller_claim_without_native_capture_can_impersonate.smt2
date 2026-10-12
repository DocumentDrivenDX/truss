; benchmark generated from python API
(set-info :status unknown)
(declare-fun mapped_effective () Int)
(declare-fun actual_effective () Int)
(declare-fun mapped_session () Int)
(declare-fun claimed_session () Int)
(declare-fun actual_session () Int)
(assert
 (let (($x14 (= actual_effective mapped_effective)))
 (let (($x17 (= claimed_session mapped_session)))
 (and $x17 $x14))))
(assert
 (and (distinct claimed_session actual_session) true))
(check-sat)
