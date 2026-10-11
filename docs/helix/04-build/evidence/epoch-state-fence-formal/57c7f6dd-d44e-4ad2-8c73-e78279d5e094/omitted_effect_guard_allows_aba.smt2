; benchmark generated from python API
(set-info :status unknown)
(declare-fun alive () Bool)
(declare-fun table_guard () Bool)
(declare-fun foreign_reader () Bool)
(declare-fun write () Bool)
(declare-fun state () Int)
(declare-fun desired () Int)
(declare-fun mid () Int)
(declare-fun end () Int)
(assert
 alive)
(assert
 (not table_guard))
(assert
 (not foreign_reader))
(assert
 write)
(assert
 (let (($x19 (not (or (and alive table_guard) foreign_reader))))
 (let (($x23 (and write $x19)))
 (= mid (ite $x23 desired state)))))
(assert
 (let (($x19 (not (or (and alive table_guard) foreign_reader))))
 (let (($x23 (and write $x19)))
 (= end (ite $x23 state mid)))))
(assert
 (and (distinct mid state) true))
(assert
 (= end state))
(check-sat)
