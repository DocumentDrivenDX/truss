; benchmark generated from python API
(set-info :status unknown)
(declare-fun original_xid () Int)
(assert
 (let ((?x13 (div original_xid 4294967296)))
(let (($x14 (>= ?x13 2147483648)))
(let ((?x16 (ite $x14 (- ?x13 4294967296) ?x13)))
(let ((?x8 (mod original_xid 4294967296)))
(let (($x10 (>= ?x8 2147483648)))
(let ((?x12 (ite $x10 (- ?x8 4294967296) ?x8)))
(let (($x26 (>= original_xid 1)))
(let (($x29 (and $x26 (< original_xid 18446744073709551616))))
(and $x29 (or (< ?x12 (- 2147483648)) (>= ?x12 2147483648) (< ?x16 (- 2147483648)) (>= ?x16 2147483648))))))))))))
(check-sat)
