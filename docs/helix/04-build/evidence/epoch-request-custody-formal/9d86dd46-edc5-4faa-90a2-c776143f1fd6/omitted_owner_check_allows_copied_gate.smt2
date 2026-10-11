; benchmark generated from python API
(set-info :status unknown)
(declare-fun request_session () Int)
(declare-fun session () Int)
(declare-fun request () Int)
(declare-fun root () Int)
(declare-fun exact_primitive_types () Bool)
(declare-fun original_sql () Int)
(declare-fun sql () Int)
(declare-fun original_comparison () Int)
(declare-fun comparison () Int)
(declare-fun family () Int)
(declare-fun response () Int)
(declare-fun lifecycle () Int)
(declare-fun owner () Int)
(declare-fun gate () Int)
(assert
 (= session request_session))
(assert
 (= root request))
(assert
 exact_primitive_types)
(assert
 (= sql original_sql))
(assert
 (= comparison original_comparison))
(assert
 (let (($x27 (= family 1)))
 (or (= family 0) $x27)))
(assert
 (= response family))
(assert
 (= lifecycle family))
(assert
 (and (distinct gate owner) true))
(check-sat)
