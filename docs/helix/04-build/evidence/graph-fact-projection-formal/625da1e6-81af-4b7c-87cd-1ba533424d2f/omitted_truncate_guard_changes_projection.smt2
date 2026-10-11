; benchmark generated from python API
(set-info :status unknown)
(declare-datatypes ((Row 0)) (((absent) (edge (rel Int) (source Int) (target Int) (payload Int)))))
(declare-fun held () Bool)
(declare-fun truncate_guard () Bool)
(declare-fun before () (Array Int Row))
(declare-fun truncated () (Array Int Row))
(declare-fun witness () Int)
(declare-fun required_scope () (Array Int Bool))
(assert
 held)
(assert
 (not truncate_guard))
(assert
 (= truncated (ite (not (and held truncate_guard)) ((as const (Array Int Row)) absent) before)))
(assert
 (let ((?x63 (select before witness)))
(let ((?x68 (ite (and ((_ is edge ) ?x63) (select required_scope (rel ?x63))) ?x63 absent)))
(let ((?x96 (select truncated witness)))
(let ((?x101 (ite (and ((_ is edge ) ?x96) (select required_scope (rel ?x96))) ?x96 absent)))
(and (distinct ?x101 ?x68) true))))))
(check-sat)
