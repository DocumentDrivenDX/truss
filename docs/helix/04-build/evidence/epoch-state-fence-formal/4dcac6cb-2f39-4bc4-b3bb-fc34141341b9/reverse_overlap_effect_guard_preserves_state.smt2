; benchmark generated from python API
(set-info :status unknown)
(declare-fun alive () Bool)
(declare-fun table_guard () Bool)
(declare-fun state () Int)
(declare-fun desired () Int)
(declare-fun foreign_reader () Bool)
(declare-fun write () Bool)
(declare-fun mid () Int)
(assert
 alive)
(assert
 table_guard)
(assert
 (let (($x19 (not (or (and alive table_guard) foreign_reader))))
 (let (($x23 (and write $x19)))
 (= mid (ite $x23 desired state)))))
(assert
 (and (distinct mid state) true))
(check-sat)
