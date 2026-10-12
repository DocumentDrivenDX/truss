; benchmark generated from python API
(set-info :status unknown)
(declare-fun successor_committed () Bool)
(declare-fun pending_committed () Bool)
(declare-fun admit () Bool)
(declare-fun remote_committed () Bool)
(assert
 (= admit (or (not pending_committed) successor_committed)))
(assert
 remote_committed)
(assert
 (not pending_committed))
(assert
 (not successor_committed))
(assert
 admit)
(check-sat)
