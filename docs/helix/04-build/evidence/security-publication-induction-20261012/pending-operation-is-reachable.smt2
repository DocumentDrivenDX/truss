; benchmark generated from python API
(set-info :status unknown)
(declare-fun generation () Int)
(declare-fun active () (Array Int Bool))
(declare-fun pending () (Array Int Bool))
(declare-fun requested_generation () Int)
(declare-fun operation () Int)
(declare-fun claim_generation () (Array Int Int))
(assert
 (= generation 1))
(assert
 (let ((?x17 ((as const (Array Int Bool)) false)))
 (= active ?x17)))
(assert
 (let ((?x17 ((as const (Array Int Bool)) false)))
 (= pending ?x17)))
(assert
 (= requested_generation generation))
(assert
 (let (($x39 (select active operation)))
 (not $x39)))
(assert
 (let (($x60 (forall ((identity Int) )(let (($x55 (= (select (store claim_generation operation generation) identity) generation)))
 (let (($x57 (and (select (store active operation true) identity) $x55)))
 (let ((?x19 (store pending operation true)))
 (let (($x58 (select ?x19 identity)))
 (=> $x58 $x57))))))
 ))
 (let (($x15 (<= generation 9223372036854775807)))
 (let (($x13 (> generation 0)))
 (and $x13 $x15 $x60)))))
(assert
 (let ((?x19 (store pending operation true)))
(select ?x19 operation)))
(check-sat)
