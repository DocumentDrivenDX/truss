; benchmark generated from python API
(set-info :status unknown)
(declare-fun original_policy () String)
(declare-fun native_policy () String)
(declare-fun selected_policy () String)
(declare-fun abstract_digest (String) (_ BitVec 256))
(declare-fun selected_manifest_policy_digest () (_ BitVec 256))
(declare-fun weak_admitted () Bool)
(assert
 (= native_policy original_policy))
(assert
 (and (distinct selected_policy original_policy) true))
(assert
 (= selected_manifest_policy_digest (abstract_digest selected_policy)))
(assert
 (let (($x14 (= selected_manifest_policy_digest (abstract_digest selected_policy))))
 (= weak_admitted $x14)))
(assert
 weak_admitted)
(check-sat)
