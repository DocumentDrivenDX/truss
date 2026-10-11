; benchmark generated from python API
(set-info :status unknown)
(declare-fun complete_source_rows () Int)
(declare-fun quota () Int)
(declare-fun received_native_rows () Int)
(assert
 (>= complete_source_rows 0))
(assert
 (>= quota 0))
(assert
 (let ((?x9 (+ quota 1)))
 (= received_native_rows (ite (<= complete_source_rows ?x9) complete_source_rows ?x9))))
(assert
 (<= received_native_rows quota))
(assert
 (and (distinct received_native_rows complete_source_rows) true))
(check-sat)
