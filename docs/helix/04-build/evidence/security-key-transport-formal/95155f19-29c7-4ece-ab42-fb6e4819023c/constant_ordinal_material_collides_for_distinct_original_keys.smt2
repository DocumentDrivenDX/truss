; benchmark generated from python API
(set-info :status unknown)
(declare-fun original_field_values () (Array Int Int))
(declare-fun original_normalized_key_material () (Array Int Int))
(declare-fun later_normalized_key_material () (Array Int Int))
(declare-fun stable_deterministic_encoder (Int Int Int (Array Int Int)) Int)
(declare-fun stable_key_id () Int)
(declare-fun qualified_type () Int)
(assert
 (let ((?x56 (select original_field_values 1)))
 (let ((?x55 (select original_field_values 0)))
 (and (distinct ?x55 ?x56) true))))
(assert
 (let ((?x62 ((as const (Array Int Int)) 0)))
 (= original_normalized_key_material ?x62)))
(assert
 (let ((?x62 ((as const (Array Int Int)) 0)))
 (= later_normalized_key_material ?x62)))
(assert
 (let ((?x66 (stable_deterministic_encoder qualified_type stable_key_id 1 later_normalized_key_material)))
(let ((?x65 (stable_deterministic_encoder qualified_type stable_key_id 1 original_normalized_key_material)))
(= ?x65 ?x66))))
(check-sat)
