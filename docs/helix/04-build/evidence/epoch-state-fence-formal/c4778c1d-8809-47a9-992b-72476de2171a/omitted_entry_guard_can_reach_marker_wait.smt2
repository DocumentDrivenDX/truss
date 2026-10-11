; benchmark generated from python API
(set-info :status unknown)
(declare-fun alive () Bool)
(declare-fun issuer_guard () Bool)
(declare-fun foreign_reader () Bool)
(assert
 alive)
(assert
 (not issuer_guard))
(assert
 (not foreign_reader))
(assert
 (not (or (and alive issuer_guard) foreign_reader)))
(check-sat)
