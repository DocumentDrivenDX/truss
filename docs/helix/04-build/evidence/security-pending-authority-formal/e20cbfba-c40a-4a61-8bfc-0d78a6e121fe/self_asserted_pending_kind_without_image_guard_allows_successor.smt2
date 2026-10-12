; benchmark generated from python API
(set-info :status unknown)
(declare-fun successor_committed () Bool)
(declare-fun pending_committed () Bool)
(declare-fun admit () Bool)
(declare-fun native_image_matches () Bool)
(assert
 (= admit (or (not pending_committed) successor_committed)))
(assert
 pending_committed)
(assert
 successor_committed)
(assert
 (not native_image_matches))
(assert
 admit)
(check-sat)
