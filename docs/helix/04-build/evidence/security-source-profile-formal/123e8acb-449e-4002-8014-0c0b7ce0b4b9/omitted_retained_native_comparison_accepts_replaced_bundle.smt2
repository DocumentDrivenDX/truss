; benchmark generated from python API
(set-info :status unknown)
(declare-fun original_policy () String)
(declare-fun native_policy () String)
(declare-fun selected_policy () String)
(declare-fun abstract_digest (String) (_ BitVec 256))
(assert
 (= native_policy original_policy))
(assert
 (and (distinct selected_policy original_policy) true))
(assert
 (let ((?x23 (abstract_digest selected_policy)))
(= ?x23 ?x23)))
(check-sat)
