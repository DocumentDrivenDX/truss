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
 (let ((?x15 (ite (and mutate (not (and alive installed mutate))) desired state)))
 (= intermediate ?x15)))
(assert
 (and (distinct intermediate state) true))
(check-sat)
