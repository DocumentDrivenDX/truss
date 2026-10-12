; benchmark generated from python API
(set-info :status unknown)
(declare-fun captured_source () String)
(declare-fun selected_source () String)
(declare-fun original_source_before () String)
(declare-fun original_source_after () String)
(assert
 (let (($x33 (= selected_source captured_source)))
 (let (($x32 (= captured_source original_source_before)))
 (and $x32 $x33))))
(assert
 (and (distinct original_source_before original_source_after) true))
(assert
 (= selected_source original_source_after))
(check-sat)
