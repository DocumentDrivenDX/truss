; benchmark generated from python API
(set-info :status unknown)
(declare-fun original_source_before () String)
(declare-fun captured_source () String)
(declare-fun original_source_after () String)
(declare-fun selected_source () String)
(assert
 (= captured_source original_source_before))
(assert
 (= selected_source original_source_after))
(assert
 (and (distinct original_source_before original_source_after) true))
(assert
 (and (distinct selected_source captured_source) true))
(check-sat)
