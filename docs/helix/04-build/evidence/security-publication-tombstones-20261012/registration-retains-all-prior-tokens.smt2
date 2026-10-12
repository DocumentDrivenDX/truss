; benchmark generated from python API
(set-info :status unknown)
(declare-fun operation () Int)
(declare-fun ever_registered () (Array Int Bool))
(assert
 (let (($x17 (forall ((identity Int) )(let ((?x9 (store ever_registered operation true)))
(let (($x14 (select ?x9 identity)))
(let (($x15 (select ever_registered identity)))
(=> $x15 $x14)))))
))
(not $x17)))
(check-sat)
