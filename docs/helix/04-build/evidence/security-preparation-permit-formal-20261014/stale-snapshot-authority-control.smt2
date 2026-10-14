; benchmark generated from python API
(set-info :status unknown)
(declare-fun original_coordinator_live () Bool)
(declare-fun authentic_issuer () Bool)
(declare-fun native_data_exclusion () Bool)
(declare-fun original_source_match () Bool)
(declare-fun current_permission () Bool)
(declare-fun old_permission () Bool)
(assert
 (let (($x57 (not current_permission)))
(and old_permission $x57 original_source_match native_data_exclusion authentic_issuer original_coordinator_live)))
(check-sat)
