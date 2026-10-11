; benchmark generated from python API
(set-info :status unknown)
(declare-fun original_selected_unsafe_role () (Array Int Bool))
(declare-fun original_set_reachable () (Array Int Bool))
(declare-fun later_set_reachable () (Array Int Bool))
(assert
 (forall ((candidate_role Int) )(let (($x17 (not (select original_selected_unsafe_role candidate_role))))
 (let (($x18 (select original_set_reachable candidate_role)))
 (=> $x18 $x17))))
 )
(assert
 (let (($x23 (forall ((candidate_role Int) )(let (($x17 (not (select original_selected_unsafe_role candidate_role))))
(let (($x21 (select later_set_reachable candidate_role)))
(=> $x21 $x17))))
))
(not $x23)))
(check-sat)
