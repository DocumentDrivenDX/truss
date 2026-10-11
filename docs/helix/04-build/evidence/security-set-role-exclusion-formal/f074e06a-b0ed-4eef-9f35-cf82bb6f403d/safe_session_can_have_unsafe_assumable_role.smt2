; benchmark generated from python API
(set-info :status unknown)
(declare-fun session () Int)
(declare-fun original_selected_unsafe_role () (Array Int Bool))
(declare-fun candidate_role () Int)
(declare-fun original_set_reachable () (Array Int Bool))
(declare-fun original_inherited () (Array Int Bool))
(assert
 (not (select original_selected_unsafe_role session)))
(assert
 (select original_set_reachable candidate_role))
(assert
 (select original_selected_unsafe_role candidate_role))
(assert
 (not (select original_inherited candidate_role)))
(check-sat)
