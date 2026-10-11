; benchmark generated from python API
(set-info :status unknown)
(declare-datatypes ((Row 0)) (((absent) (edge (rel Int) (source Int) (target Int) (payload Int)))))
(declare-fun held () Bool)
(declare-fun known () Bool)
(declare-fun write () Bool)
(declare-fun new () Row)
(declare-fun key () Int)
(declare-fun before () (Array Int Row))
(declare-fun op () Int)
(declare-fun native_scope () (Array Int Bool))
(declare-fun new_guard () Bool)
(declare-fun old_guard () Bool)
(declare-fun after () (Array Int Row))
(declare-fun required_scope () (Array Int Bool))
(declare-fun witness () Int)
(assert
 held)
(assert
 known)
(assert
 write)
(assert
 (or (and (= op 0) ((_ is absent ) (select before key)) ((_ is edge ) new)) (and (= op 1) ((_ is edge ) (select before key)) ((_ is edge ) new)) (and (= op 2) ((_ is edge ) (select before key)) ((_ is absent ) new))))
(assert
 (let ((?x49 (store before key new)))
 (let ((?x16 (select before key)))
 (let ((?x37 (rel ?x16)))
 (let (($x38 (select native_scope ?x37)))
 (let (($x29 ((_ is edge ) ?x16)))
 (let (($x39 (and $x29 $x38)))
 (let (($x36 (not known)))
 (let (($x45 (or $x36 (and old_guard $x39) (and new_guard (and ((_ is edge ) new) (select native_scope (rel new)))))))
 (let (($x47 (not (and held $x45))))
 (= after (ite (and write $x47) ?x49 before))))))))))))
(assert
 old_guard)
(assert
 new_guard)
(assert
 (forall ((rel Int) )(let (($x56 (select native_scope rel)))
 (let (($x57 (select required_scope rel)))
 (=> $x57 $x56))))
 )
(assert
 (= op 0))
(assert
 (= new (edge 101 1 1 7)))
(assert
 (let (($x81 (select native_scope 101)))
 (= $x81 false)))
(assert
 (select required_scope 100))
(assert
 (= witness key))
(assert
 (let ((?x16 (select before key)))
(let ((?x86 (select after key)))
(and (distinct ?x86 ?x16) true))))
(check-sat)
