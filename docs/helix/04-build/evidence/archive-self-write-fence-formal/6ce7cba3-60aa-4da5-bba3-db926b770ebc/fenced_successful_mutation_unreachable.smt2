; benchmark generated from python API
(set-info :status unknown)
(declare-fun alive () Bool)
(declare-fun installed () Bool)
(declare-fun mutate () Bool)
(assert
 alive)
(assert
 installed)
(assert
 mutate)
(assert
 (not (and alive installed mutate)))
(check-sat)
