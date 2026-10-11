; benchmark generated from python API
(set-info :status unknown)
(declare-fun new_generation () String)
(declare-fun old_generation () String)
(declare-fun whole_transaction_committed () Bool)
(assert
 (and (distinct old_generation new_generation) true))
(assert
 whole_transaction_committed)
(assert
 (let ((?x11 (ite whole_transaction_committed new_generation old_generation)))
(= ?x11 old_generation)))
(check-sat)
