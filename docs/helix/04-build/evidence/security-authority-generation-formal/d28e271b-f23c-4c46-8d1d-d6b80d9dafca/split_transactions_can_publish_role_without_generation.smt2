; benchmark generated from python API
(set-info :status unknown)
(declare-fun new_role_state () Int)
(declare-fun old_role_state () Int)
(declare-fun new_generation () String)
(declare-fun old_generation () String)
(declare-fun separate_role_commit () Bool)
(declare-fun separate_generation_commit () Bool)
(assert
 (and (distinct old_role_state new_role_state) true))
(assert
 (and (distinct old_generation new_generation) true))
(assert
 separate_role_commit)
(assert
 (not separate_generation_commit))
(assert
 (let ((?x15 (ite separate_role_commit new_role_state old_role_state)))
 (= ?x15 new_role_state)))
(assert
 (let ((?x16 (ite separate_generation_commit new_generation old_generation)))
(= ?x16 old_generation)))
(check-sat)
