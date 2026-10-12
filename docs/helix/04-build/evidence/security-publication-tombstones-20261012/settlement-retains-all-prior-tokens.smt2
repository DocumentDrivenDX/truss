; benchmark generated from python API
(set-info :status unknown)
(declare-fun ever_registered () (Array Int Bool))
(assert
 (let (($x19 (forall ((identity Int) )(let (($x15 (select ever_registered identity)))
(=> $x15 $x15)))
))
(not $x19)))
(check-sat)
