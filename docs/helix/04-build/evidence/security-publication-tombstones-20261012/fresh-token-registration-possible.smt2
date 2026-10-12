; benchmark generated from python API
(set-info :status unknown)
(declare-fun operation () Int)
(declare-fun ever_registered () (Array Int Bool))
(declare-fun active () (Array Int Bool))
(assert
 (let (($x12 (select ever_registered operation)))
 (not $x12)))
(assert
 (not (select active operation)))
(assert
 (let ((?x9 (store ever_registered operation true)))
(select ?x9 operation)))
(check-sat)
