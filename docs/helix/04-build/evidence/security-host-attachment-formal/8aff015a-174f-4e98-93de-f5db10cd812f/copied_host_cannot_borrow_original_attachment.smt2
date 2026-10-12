; benchmark generated from python API
(set-info :status unknown)
(declare-fun registered_handle () Int)
(declare-fun claimed_handle () Int)
(declare-fun registered_host () Int)
(declare-fun claimed_host () Int)
(declare-fun metadata_matches () Bool)
(declare-fun allowed () Bool)
(assert
 (let (($x14 (= claimed_host registered_host)))
 (= allowed (and metadata_matches $x14 (= claimed_handle registered_handle)))))
(assert
 (and (distinct claimed_host registered_host) true))
(assert
 allowed)
(check-sat)
