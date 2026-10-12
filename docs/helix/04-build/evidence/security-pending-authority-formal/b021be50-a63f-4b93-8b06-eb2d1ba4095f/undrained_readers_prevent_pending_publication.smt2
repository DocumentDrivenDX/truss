; benchmark generated from python API
(set-info :status unknown)
(declare-fun requalified () Bool)
(declare-fun remote_outcome_known () Bool)
(declare-fun pending_committed () Bool)
(declare-fun successor_committed () Bool)
(declare-fun remote_committed () Bool)
(declare-fun readers_drained () Bool)
(assert
 (let (($x14 (and pending_committed remote_outcome_known requalified)))
 (and (=> pending_committed readers_drained) (=> remote_committed pending_committed) (=> successor_committed $x14))))
(assert
 (not readers_drained))
(assert
 pending_committed)
(check-sat)
