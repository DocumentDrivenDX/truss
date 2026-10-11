; benchmark generated from python API
(set-info :status unknown)
(declare-fun alive () Bool)
(declare-fun issuer_guard () Bool)
(declare-fun state () Int)
(declare-fun desired () Int)
(declare-fun foreign_reader () Bool)
(declare-fun write () Bool)
(declare-fun mid () Int)
(assert
 alive)
(assert
 issuer_guard)
(assert
 (let ((?x21 (ite (and write (not (or (and alive issuer_guard) foreign_reader))) desired state)))
 (= mid ?x21)))
(assert
 (and (distinct mid state) true))
(check-sat)
