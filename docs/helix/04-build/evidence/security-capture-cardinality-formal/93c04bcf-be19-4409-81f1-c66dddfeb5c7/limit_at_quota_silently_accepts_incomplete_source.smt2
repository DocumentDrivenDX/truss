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
 (= received_native_rows (ite (<= complete_source_rows quota) complete_source_rows quota)))
(assert
 (<= received_native_rows quota))
(assert
 (> complete_source_rows quota))
(check-sat)
