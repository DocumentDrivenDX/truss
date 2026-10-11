; benchmark generated from python API
(set-info :status unknown)
(declare-fun started () Bool)
(declare-fun tagged () Bool)
(declare-fun writer_modes () Bool)
(declare-fun ended () Bool)
(declare-fun writer_held () Bool)
(declare-fun accepted () Bool)
(assert
 started)
(assert
 tagged)
(assert
 (not writer_modes))
(assert
 (not ended))
(assert
 (= writer_held (and started tagged writer_modes (not ended))))
(assert
 (not (and writer_held accepted)))
(assert
 accepted)
(check-sat)
