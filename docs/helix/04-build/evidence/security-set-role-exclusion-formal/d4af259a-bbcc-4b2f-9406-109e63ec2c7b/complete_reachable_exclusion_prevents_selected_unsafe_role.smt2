; benchmark generated from python API
(set-info :status unknown)
(declare-fun original_selected_unsafe_role () (Array Int Bool))
(declare-fun original_set_reachable () (Array Int Bool))
(declare-fun candidate_role () Int)
(assert
 (forall ((candidate_role Int) )(let (($x17 (not (select original_selected_unsafe_role candidate_role))))
 (let (($x18 (select original_set_reachable candidate_role)))
 (=> $x18 $x17))))
 )
(assert
 (select original_set_reachable candidate_role))
(assert
 (select original_selected_unsafe_role candidate_role))
(check-sat)
