; benchmark generated from python API
(set-info :status unknown)
(declare-fun owner () Int)
(declare-fun gate () Int)
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
(assert
 (= gate owner))
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
 (= family 1))
(assert
 (= response 0))
(assert
 (= lifecycle 1))
(check-sat)
