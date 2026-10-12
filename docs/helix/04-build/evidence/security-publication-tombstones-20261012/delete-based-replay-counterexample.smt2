; benchmark generated from python API
(set-info :status unknown)
(declare-fun operation () Int)
(declare-fun ever_registered () (Array Int Bool))
(declare-fun active () (Array Int Bool))
(assert
 (select ever_registered operation))
(assert
 (not (select active operation)))
(check-sat)
