; benchmark generated from python API
(set-info :status unknown)
(declare-fun original_width () Int)
(declare-fun later_width () Int)
(declare-fun later_ordered_components () (Array Int Int))
(declare-fun original_ordered_components () (Array Int Int))
(declare-fun later_field_values () (Array Int Int))
(declare-fun original_field_values () (Array Int Int))
(assert
 (> original_width 0))
(assert
 (= original_width later_width))
(assert
 (= original_ordered_components later_ordered_components))
(assert
 (forall ((index Int) )(let ((?x23 (select original_ordered_components index)))
 (let ((?x24 (select original_field_values ?x23)))
 (let (($x39 (= ?x24 (select later_field_values ?x23))))
 (let (($x26 (>= index 0)))
 (let (($x27 (and $x26 (< index original_width))))
 (=> $x27 $x39)))))))
 )
(assert
 (let ((?x35 (lambda ((index Int) )(let ((?x31 (select later_field_values (select later_ordered_components index))))
(ite (and (>= index 0) (< index later_width)) ?x31 0)))
))
(let ((?x29 (lambda ((index Int) )(let ((?x23 (select original_ordered_components index)))
(let ((?x24 (select original_field_values ?x23)))
(let (($x26 (>= index 0)))
(let (($x27 (and $x26 (< index original_width))))
(ite $x27 ?x24 0))))))
))
(and (distinct ?x29 ?x35) true))))
(check-sat)
