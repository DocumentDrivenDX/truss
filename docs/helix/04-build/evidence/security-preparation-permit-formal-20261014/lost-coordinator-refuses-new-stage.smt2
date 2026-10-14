; benchmark generated from python API
(set-info :status unknown)
(declare-fun original_coordinator_live () Bool)
(declare-fun authentic_issuer () Bool)
(declare-fun native_data_exclusion () Bool)
(declare-fun original_source_match () Bool)
(declare-fun current_permission () Bool)
(assert
 (let (($x19 (and current_permission original_source_match native_data_exclusion authentic_issuer original_coordinator_live)))
(and $x19 (not original_coordinator_live))))
(check-sat)
