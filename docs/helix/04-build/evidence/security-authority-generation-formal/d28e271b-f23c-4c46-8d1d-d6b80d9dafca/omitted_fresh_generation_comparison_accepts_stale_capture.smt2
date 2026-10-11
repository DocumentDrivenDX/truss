; benchmark generated from python API
(set-info :status unknown)
(declare-fun new_generation () String)
(declare-fun old_generation () String)
(declare-fun whole_transaction_committed () Bool)
(assert
 (and (distinct old_generation new_generation) true))
(assert
 whole_transaction_committed)
(check-sat)
