; benchmark generated from python API
(set-info :status unknown)
(declare-fun original_width () Int)
(declare-fun later_width () Int)
(declare-fun later_normalized_key_material () (Array Int Int))
(declare-fun original_normalized_key_material () (Array Int Int))
(declare-fun stable_deterministic_encoder (Int Int Int (Array Int Int)) Int)
(declare-fun stable_key_id () Int)
(declare-fun qualified_type () Int)
(assert
 (= original_width 1))
(assert
 (= later_width 2))
(assert
 (= original_normalized_key_material later_normalized_key_material))
(assert
 (let ((?x40 (stable_deterministic_encoder qualified_type stable_key_id later_width later_normalized_key_material)))
(let ((?x39 (stable_deterministic_encoder qualified_type stable_key_id original_width original_normalized_key_material)))
(and (distinct ?x39 ?x40) true))))
(check-sat)
