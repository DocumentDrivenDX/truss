; benchmark generated from python API
(set-info :status unknown)
(declare-fun whole_transaction_committed () Bool)
(declare-fun old_generation () String)
(declare-fun new_generation () String)
(declare-fun old_role_state () Int)
(declare-fun new_role_state () Int)
(assert
 (not whole_transaction_committed))
(assert
 (let ((?x11 (ite whole_transaction_committed new_generation old_generation)))
(let ((?x10 (ite whole_transaction_committed new_role_state old_role_state)))
(or (and (distinct ?x10 old_role_state) true) (and (distinct ?x11 old_generation) true)))))
(check-sat)
