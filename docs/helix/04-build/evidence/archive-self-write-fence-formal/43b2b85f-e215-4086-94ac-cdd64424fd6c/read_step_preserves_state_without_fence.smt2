; benchmark generated from python API
(set-info :status unknown)
(declare-fun mutate () Bool)
(declare-fun state () Int)
(declare-fun desired () Int)
(declare-fun installed () Bool)
(declare-fun alive () Bool)
(declare-fun intermediate () Int)
(assert
 (not mutate))
(assert
 (let (($x13 (not (and alive installed mutate))))
 (let (($x14 (and mutate $x13)))
 (= intermediate (ite $x14 desired state)))))
(assert
 (and (distinct intermediate state) true))
(check-sat)
