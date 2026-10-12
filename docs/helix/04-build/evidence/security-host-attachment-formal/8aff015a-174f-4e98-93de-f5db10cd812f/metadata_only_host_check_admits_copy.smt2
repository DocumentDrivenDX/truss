; benchmark generated from python API
(set-info :status unknown)
(declare-fun metadata_matches () Bool)
(declare-fun allowed () Bool)
(declare-fun registered_host () Int)
(declare-fun claimed_host () Int)
(assert
 (= allowed metadata_matches))
(assert
 metadata_matches)
(assert
 (and (distinct claimed_host registered_host) true))
(assert
 allowed)
(check-sat)
