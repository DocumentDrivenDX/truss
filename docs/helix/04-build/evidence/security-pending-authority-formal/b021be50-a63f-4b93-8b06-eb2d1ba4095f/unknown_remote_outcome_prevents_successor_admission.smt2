; benchmark generated from python API
(set-info :status unknown)
(declare-fun requalified () Bool)
(declare-fun remote_outcome_known () Bool)
(declare-fun pending_committed () Bool)
(declare-fun successor_committed () Bool)
(declare-fun remote_committed () Bool)
(declare-fun readers_drained () Bool)
(declare-fun admit () Bool)
(assert
 (let (($x14 (and pending_committed remote_outcome_known requalified)))
 (and (=> pending_committed readers_drained) (=> remote_committed pending_committed) (=> successor_committed $x14))))
(assert
 (= admit (or (not pending_committed) successor_committed)))
(assert
 pending_committed)
(assert
 (not remote_outcome_known))
(assert
 admit)
(check-sat)
