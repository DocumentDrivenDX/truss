; benchmark generated from python API
(set-info :status unknown)
(declare-fun authority_changed () Bool)
(declare-fun data_commit_in_progress () Bool)
(declare-fun coordinator_lost () Bool)
(declare-fun original_data_transaction_holds_authority_exclusion () Bool)
(assert
 (let (($x63 (not original_data_transaction_holds_authority_exclusion)))
(let (($x24 (not authority_changed)))
(let (($x25 (=> original_data_transaction_holds_authority_exclusion $x24)))
(and $x25 $x63 coordinator_lost data_commit_in_progress authority_changed)))))
(check-sat)
