; benchmark generated from python API
(set-info :status unknown)
(declare-fun selected_resolution () String)
(declare-fun native_resolution () String)
(declare-fun selected_policy () String)
(declare-fun native_policy () String)
(declare-fun original_resolution () String)
(declare-fun original_policy () String)
(assert
 (let (($x19 (= native_resolution selected_resolution)))
 (let (($x18 (= native_policy selected_policy)))
 (let (($x17 (= selected_resolution original_resolution)))
 (let (($x16 (= selected_policy original_policy)))
 (and $x16 $x17 $x18 $x19))))))
(assert
 (and (distinct native_resolution original_resolution) true))
(check-sat)
