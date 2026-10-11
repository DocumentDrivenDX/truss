; benchmark generated from python API
(set-info :status unknown)
(declare-fun reader () Bool)
(declare-fun tagged () Bool)
(declare-fun own_guard () Bool)
(declare-fun writer_modes () Bool)
(declare-fun write () Bool)
(declare-fun state () Int)
(declare-fun desired () Int)
(declare-fun own () Bool)
(declare-fun successor () Int)
(declare-fun epoch_before () Int)
(declare-fun epoch_after () Int)
(assert
 (not reader))
(assert
 tagged)
(assert
 own_guard)
(assert
 writer_modes)
(assert
 write)
(assert
 (let (($x18 (not (and reader tagged (ite own own_guard writer_modes)))))
 (= successor (ite (and write $x18) desired state))))
(assert
 (and (distinct successor state) true))
(assert
 (= epoch_after epoch_before))
(check-sat)
