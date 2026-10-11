; benchmark generated from python API
(set-info :status unknown)
(declare-fun marker1 () Bool)
(declare-fun effect1 () Bool)
(declare-fun marker2 () Bool)
(declare-fun effect2 () Bool)
(assert
 (=> effect1 marker1))
(assert
 (=> effect2 marker2))
(assert
 (not (and marker1 marker2)))
(assert
 effect1)
(assert
 effect2)
(check-sat)
