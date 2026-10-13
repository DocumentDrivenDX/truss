; benchmark generated from python API
(set-info :status unknown)
(declare-fun native_scope () (Array Int Bool))
(declare-fun required_scope () (Array Int Bool))
(declare-fun later_scope () (Array Int Bool))
(declare-fun witness () Int)
(assert
 (forall ((rel Int) )(let (($x56 (select native_scope rel)))
 (let (($x57 (select required_scope rel)))
 (=> $x57 $x56))))
 )
(assert
 (forall ((rel Int) )(let (($x107 (select later_scope rel)))
 (let (($x56 (select native_scope rel)))
 (=> $x56 $x107))))
 )
(assert
 (select required_scope witness))
(assert
 (not (select later_scope witness)))
(check-sat)
