; benchmark generated from python API
(set-info :status unknown)
(declare-fun reader () Bool)
(declare-fun tagged () Bool)
(declare-fun own () Bool)
(declare-fun retained_operation () Bool)
(declare-fun operation_guard () Bool)
(declare-fun state () Int)
(declare-fun desired () Int)
(declare-fun writer_modes () Bool)
(declare-fun own_guard () Bool)
(declare-fun write () Bool)
(declare-fun successor () Int)
(assert
 (not reader))
(assert
 tagged)
(assert
 own)
(assert
 retained_operation)
(assert
 operation_guard)
(assert
 (let (($x22 (not (and tagged own retained_operation operation_guard))))
 (let (($x20 (not (and reader tagged (ite own own_guard writer_modes)))))
 (let (($x23 (and $x20 $x22)))
 (= successor (ite (and write $x23) desired state))))))
(assert
 (and (distinct successor state) true))
(check-sat)
