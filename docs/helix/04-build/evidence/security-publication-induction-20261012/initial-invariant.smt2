; benchmark generated from python API
(set-info :status unknown)
(assert
 (let (($x47 (forall ((identity Int) )(let ((?x17 ((as const (Array Int Bool)) false)))
(let (($x44 (select ?x17 identity)))
(=> $x44 (and $x44 (= 1 (select ((as const (Array Int Int)) 0) identity)))))))
))
(not (and (> 1 0) (<= 1 9223372036854775807) $x47))))
(check-sat)
