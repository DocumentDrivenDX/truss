; benchmark generated from python API
(set-info :status unknown)
(declare-fun fresh_post_barrier_snapshot () Bool)
(declare-fun native_image_matches () Bool)
(declare-fun requalified () Bool)
(declare-fun remote_outcome_known () Bool)
(declare-fun pending_committed () Bool)
(declare-fun successor_committed () Bool)
(declare-fun remote_committed () Bool)
(declare-fun readers_drained () Bool)
(assert
 (let (($x17 (and pending_committed remote_outcome_known requalified native_image_matches fresh_post_barrier_snapshot)))
 (let (($x14 (and readers_drained fresh_post_barrier_snapshot)))
 (and (=> pending_committed $x14) (=> remote_committed pending_committed) (=> successor_committed $x17)))))
(assert
 (not fresh_post_barrier_snapshot))
(assert
 pending_committed)
(check-sat)
