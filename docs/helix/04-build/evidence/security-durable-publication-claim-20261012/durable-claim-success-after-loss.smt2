; benchmark generated from python API
(set-info :status unknown)
(declare-fun ack () Int)
(declare-fun settle () Int)
(declare-fun release () Int)
(declare-fun loss () Int)
(declare-fun register () Int)
(assert
 (and (distinct register loss release settle ack) true))
(assert
 (let (($x12 (>= register 0)))
 (and $x12 (< register 5))))
(assert
 (let (($x16 (>= loss 0)))
 (and $x16 (< loss 5))))
(assert
 (let (($x19 (>= release 0)))
 (and $x19 (< release 5))))
(assert
 (let (($x22 (>= settle 0)))
 (and $x22 (< settle 5))))
(assert
 (let (($x25 (>= ack 0)))
 (and $x25 (< ack 5))))
(assert
 (< register loss))
(assert
 (< register release))
(assert
 (< register settle))
(assert
 (< settle ack))
(assert
 (< loss release))
(assert
 (< release settle))
(check-sat)
