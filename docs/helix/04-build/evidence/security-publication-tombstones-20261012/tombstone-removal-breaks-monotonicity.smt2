; benchmark generated from python API
(set-info :status unknown)
(declare-fun operation () Int)
(declare-fun ever_registered () (Array Int Bool))
(assert
 (select ever_registered operation))
(assert
 (let (($x30 (forall ((identity Int) )(let (($x28 (select (store ever_registered operation false) identity)))
(let (($x15 (select ever_registered identity)))
(=> $x15 $x28))))
))
(not $x30)))
(check-sat)
