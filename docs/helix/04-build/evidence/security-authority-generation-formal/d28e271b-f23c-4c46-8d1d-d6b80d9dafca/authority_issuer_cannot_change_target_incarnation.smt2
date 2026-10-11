; benchmark generated from python API
(set-info :status unknown)
(declare-fun original_target_incarnation () String)
(declare-fun selected_target_incarnation () String)
(declare-fun authority_issuer_admitted () Bool)
(assert
 (let (($x20 (= selected_target_incarnation original_target_incarnation)))
 (= authority_issuer_admitted $x20)))
(assert
 authority_issuer_admitted)
(assert
 (and (distinct selected_target_incarnation original_target_incarnation) true))
(check-sat)
