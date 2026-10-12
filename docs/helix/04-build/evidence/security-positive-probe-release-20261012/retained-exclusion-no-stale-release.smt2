; benchmark generated from python API
(set-info :status unknown)
(declare-fun release () Int)
(declare-fun ack () Int)
(declare-fun loss () Int)
(declare-fun probe () Int)
(declare-fun acquire () Int)
(assert
 (and (distinct acquire probe loss ack release) true))
(assert
 (let (($x12 (>= acquire 0)))
 (and $x12 (< acquire 5))))
(assert
 (let (($x16 (>= probe 0)))
 (and $x16 (< probe 5))))
(assert
 (let (($x19 (>= loss 0)))
 (and $x19 (< loss 5))))
(assert
 (let (($x22 (>= ack 0)))
 (and $x22 (< ack 5))))
(assert
 (let (($x25 (>= release 0)))
 (and $x25 (< release 5))))
(assert
 (< acquire probe))
(assert
 (< probe release))
(assert
 (< probe loss))
(assert
 (< loss ack))
(assert
 (< release loss))
(assert
 (< ack release))
(check-sat)
