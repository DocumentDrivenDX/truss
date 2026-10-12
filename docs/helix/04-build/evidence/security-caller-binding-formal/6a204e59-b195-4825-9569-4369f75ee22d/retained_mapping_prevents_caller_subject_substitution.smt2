; benchmark generated from python API
(set-info :status unknown)
(declare-fun native_mapped_subject () String)
(declare-fun selected_subject () String)
(declare-fun mapped_effective () Int)
(declare-fun actual_effective () Int)
(declare-fun mapped_session () Int)
(declare-fun actual_session () Int)
(assert
 (let (($x15 (= selected_subject native_mapped_subject)))
 (let (($x14 (= actual_effective mapped_effective)))
 (let (($x13 (= actual_session mapped_session)))
 (and $x13 $x14 $x15)))))
(assert
 (and (distinct selected_subject native_mapped_subject) true))
(check-sat)
