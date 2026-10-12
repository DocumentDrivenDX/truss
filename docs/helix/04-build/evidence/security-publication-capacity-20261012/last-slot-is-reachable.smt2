; benchmark generated from python API
(set-info :status unknown)
(declare-fun capacity () Int)
(declare-fun retained () Int)
(assert
 (let (($x12 (>= retained 0)))
 (let (($x10 (<= capacity 1048576)))
 (let (($x8 (>= capacity 1)))
 (and $x8 $x10 $x12 (<= retained capacity))))))
(assert
 (= retained (- capacity 1)))
(assert
 (< retained capacity))
(assert
 (let ((?x16 (+ retained 1)))
(= ?x16 capacity)))
(check-sat)
