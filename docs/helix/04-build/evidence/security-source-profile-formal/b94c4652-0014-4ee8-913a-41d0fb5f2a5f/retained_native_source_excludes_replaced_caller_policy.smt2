; benchmark generated from python API
(set-info :status unknown)
(declare-fun original_policy () String)
(declare-fun native_policy () String)
(declare-fun selected_policy () String)
(assert
 (= native_policy original_policy))
(assert
 (and (distinct selected_policy original_policy) true))
(assert
 (= native_policy selected_policy))
(check-sat)
