; benchmark generated from python API
(set-info :status unknown)
(declare-fun selected_resolution () String)
(declare-fun native_resolution () String)
(declare-fun selected_policy () String)
(declare-fun native_policy () String)
(declare-fun original_resolution () String)
(declare-fun original_policy () String)
(assert
 (let (($x14 (= native_resolution selected_resolution)))
 (let (($x13 (= native_policy selected_policy)))
 (let (($x12 (= selected_resolution original_resolution)))
 (let (($x11 (= selected_policy original_policy)))
 (and $x11 $x12 $x13 $x14))))))
(assert
 (and (distinct native_policy original_policy) true))
(check-sat)
