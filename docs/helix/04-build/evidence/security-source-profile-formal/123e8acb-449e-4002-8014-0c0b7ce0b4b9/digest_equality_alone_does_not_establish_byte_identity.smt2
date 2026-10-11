; benchmark generated from python API
(set-info :status unknown)
(declare-fun abstract_digest (String) (_ BitVec 256))
(declare-fun original_policy () String)
(declare-fun native_policy () String)
(assert
 (= (abstract_digest native_policy) (abstract_digest original_policy)))
(assert
 (and (distinct native_policy original_policy) true))
(check-sat)
