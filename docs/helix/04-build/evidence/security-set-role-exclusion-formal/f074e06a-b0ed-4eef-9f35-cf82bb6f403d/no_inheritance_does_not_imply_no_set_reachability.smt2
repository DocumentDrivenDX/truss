; benchmark generated from python API
(set-info :status unknown)
(declare-fun candidate_role () Int)
(declare-fun original_inherited () (Array Int Bool))
(declare-fun original_set_reachable () (Array Int Bool))
(assert
 (not (select original_inherited candidate_role)))
(assert
 (select original_set_reachable candidate_role))
(check-sat)
