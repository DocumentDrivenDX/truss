; benchmark generated from python API
(set-info :status unknown)
(declare-fun same_backend_retained_reader () Bool)
(declare-fun writer_admitted () Bool)
(assert
 (= writer_admitted (not same_backend_retained_reader)))
(assert
 same_backend_retained_reader)
(assert
 writer_admitted)
(check-sat)
