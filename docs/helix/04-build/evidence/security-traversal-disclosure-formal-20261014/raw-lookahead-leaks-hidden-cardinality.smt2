; benchmark generated from python API
(set-info :status unknown)
(declare-fun requested_bound () Int)
(declare-fun hidden_related_occurrences () Int)
(declare-fun eligible_related_occurrences () Int)
(assert
 (let ((?x55 (+ eligible_related_occurrences hidden_related_occurrences)))
(let (($x51 (>= eligible_related_occurrences 0)))
(and $x51 (> hidden_related_occurrences 0) (> requested_bound 0) (<= eligible_related_occurrences requested_bound) (> ?x55 requested_bound)))))
(check-sat)
