; benchmark generated from python API
(set-info :status unknown)
(declare-fun metadata_matches () Bool)
(declare-fun allowed () Bool)
(declare-fun registered_handle () Int)
(declare-fun claimed_handle () Int)
(assert
 (= allowed metadata_matches))
(assert
 metadata_matches)
(assert
 (and (distinct claimed_handle registered_handle) true))
(assert
 allowed)
(check-sat)
