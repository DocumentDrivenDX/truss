; benchmark generated from python API
(set-info :status unknown)
(declare-fun successor_committed () Bool)
(declare-fun pending_committed () Bool)
(declare-fun admit () Bool)
(declare-fun remote_outcome_known () Bool)
(declare-fun requalified () Bool)
(assert
 (= admit (or (not pending_committed) successor_committed)))
(assert
 pending_committed)
(assert
 (not remote_outcome_known))
(assert
 (not requalified))
(assert
 successor_committed)
(assert
 admit)
(check-sat)
