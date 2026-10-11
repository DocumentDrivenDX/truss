; benchmark generated from python API
(set-info :status unknown)
(declare-fun original_width () Int)
(declare-fun later_width () Int)
(declare-fun later_ordered_components () (Array Int Int))
(declare-fun original_ordered_components () (Array Int Int))
(declare-fun later_field_values () (Array Int Int))
(declare-fun original_field_values () (Array Int Int))
(declare-fun witness () Int)
(assert
 (> original_width 0))
(assert
 (= original_width later_width))
(assert
 (= original_ordered_components later_ordered_components))
(assert
 (forall ((index Int) )(let ((?x25 (select original_ordered_components index)))
 (let (($x28 (= (select original_field_values ?x25) (select later_field_values ?x25))))
 (=> (and (>= index 0) (< index original_width)) $x28))))
 )
(assert
 (>= witness 0))
(assert
 (< witness original_width))
(assert
 (let ((?x36 (select later_field_values (select later_ordered_components witness))))
(let ((?x34 (select original_field_values (select original_ordered_components witness))))
(and (distinct ?x34 ?x36) true))))
(check-sat)
