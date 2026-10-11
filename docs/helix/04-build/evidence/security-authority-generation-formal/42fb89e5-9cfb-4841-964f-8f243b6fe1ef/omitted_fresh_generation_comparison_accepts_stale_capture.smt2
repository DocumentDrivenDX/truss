; benchmark generated from python API
(set-info :status unknown)
(declare-fun new_generation () String)
(declare-fun old_generation () String)
(declare-fun whole_transaction_committed () Bool)
(declare-fun captured_generation () String)
(declare-fun weak_admitted () Bool)
(assert
 (and (distinct old_generation new_generation) true))
(assert
 whole_transaction_committed)
(assert
 (= captured_generation old_generation))
(assert
 (let (($x15 (= captured_generation old_generation)))
 (= weak_admitted $x15)))
(assert
 weak_admitted)
(assert
 (let ((?x11 (ite whole_transaction_committed new_generation old_generation)))
(and (distinct ?x11 captured_generation) true)))
(check-sat)
