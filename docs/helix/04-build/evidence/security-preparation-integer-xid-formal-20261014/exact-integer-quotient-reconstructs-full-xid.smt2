; benchmark generated from python API
(set-info :status unknown)
(declare-fun original_xid () Int)
(assert
 (let (($x32 (and (distinct (+ (* (div original_xid 4294967296) 4294967296) (mod original_xid 4294967296)) original_xid) true)))
(let (($x26 (>= original_xid 1)))
(let (($x29 (and $x26 (< original_xid 18446744073709551616))))
(and $x29 $x32)))))
(check-sat)
