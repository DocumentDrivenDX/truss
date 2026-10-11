; benchmark generated from python API
(set-info :status unknown)
(declare-fun original_width () Int)
(declare-fun later_width () Int)
(declare-fun later_field_values () (Array Int Int))
(declare-fun original_field_values () (Array Int Int))
(declare-fun original_ordered_components () (Array Int Int))
(declare-fun later_ordered_components () (Array Int Int))
(assert
 (= original_width 2))
(assert
 (= later_width 2))
(assert
 (= original_field_values later_field_values))
(assert
 (let ((?x46 (select original_ordered_components 0)))
 (= ?x46 0)))
(assert
 (= (select original_ordered_components 1) 1))
(assert
 (let ((?x51 (select later_ordered_components 0)))
 (= ?x51 1)))
(assert
 (= (select later_ordered_components 1) 0))
(assert
 (let ((?x56 (select original_field_values 1)))
 (let ((?x55 (select original_field_values 0)))
 (and (distinct ?x55 ?x56) true))))
(assert
 (let ((?x51 (select later_ordered_components 0)))
(let ((?x59 (select later_field_values ?x51)))
(let ((?x46 (select original_ordered_components 0)))
(let ((?x58 (select original_field_values ?x46)))
(and (distinct ?x58 ?x59) true))))))
(check-sat)
