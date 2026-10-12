; benchmark generated from python API
(set-info :status unknown)
(declare-fun generation () Int)
(declare-fun claim_generation () (Array Int Int))
(declare-fun active () (Array Int Bool))
(declare-fun pending () (Array Int Bool))
(declare-fun operation () Int)
(assert
 (let (($x29 (forall ((identity Int) )(let ((?x23 (select claim_generation identity)))
 (let (($x24 (= ?x23 generation)))
 (let (($x25 (select active identity)))
 (let (($x26 (and $x25 $x24)))
 (let (($x27 (select pending identity)))
 (=> $x27 $x26)))))))
 ))
 (let (($x15 (<= generation 9223372036854775807)))
 (let (($x13 (> generation 0)))
 (and $x13 $x15 $x29)))))
(assert
 (let (($x39 (select active operation)))
 (not $x39)))
(assert
 (select pending (+ operation 1)))
(assert
 (< generation 9223372036854775807))
(assert
 (let (($x84 (forall ((identity Int) )(let (($x25 (select active identity)))
(let (($x27 (select pending identity)))
(=> $x27 (and $x25 (= (select claim_generation identity) (+ generation 1)))))))
))
(let (($x75 (and (> (+ generation 1) 0) (<= (+ generation 1) 9223372036854775807) $x84)))
(not $x75))))
(check-sat)
