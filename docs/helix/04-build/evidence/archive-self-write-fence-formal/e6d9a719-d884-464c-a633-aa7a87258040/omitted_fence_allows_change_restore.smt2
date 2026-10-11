; benchmark generated from python API
(set-info :status unknown)
(declare-fun alive () Bool)
(declare-fun installed () Bool)
(declare-fun mutate () Bool)
(declare-fun state () Int)
(declare-fun desired () Int)
(declare-fun intermediate () Int)
(declare-fun final () Int)
(assert
 alive)
(assert
 (not installed))
(assert
 mutate)
(assert
 (let (($x13 (not (and alive installed mutate))))
 (let (($x14 (and mutate $x13)))
 (= intermediate (ite $x14 desired state)))))
(assert
 (let (($x13 (not (and alive installed mutate))))
 (let (($x14 (and mutate $x13)))
 (= final (ite $x14 state intermediate)))))
(assert
 (and (distinct intermediate state) true))
(assert
 (= final state))
(check-sat)
