; benchmark generated from python API
(set-info :status unknown)
(declare-fun reader () Bool)
(declare-fun tagged () Bool)
(declare-fun own () Bool)
(declare-fun writer_modes () Bool)
(declare-fun state () Int)
(declare-fun desired () Int)
(declare-fun own_guard () Bool)
(declare-fun write () Bool)
(declare-fun successor () Int)
(assert
 reader)
(assert
 tagged)
(assert
 (not own))
(assert
 writer_modes)
(assert
 (let (($x18 (not (and reader tagged (ite own own_guard writer_modes)))))
 (= successor (ite (and write $x18) desired state))))
(assert
 (and (distinct successor state) true))
(check-sat)
