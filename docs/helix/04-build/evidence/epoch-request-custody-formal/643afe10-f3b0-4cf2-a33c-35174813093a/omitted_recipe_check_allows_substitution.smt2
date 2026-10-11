; benchmark generated from python API
(set-info :status unknown)
(declare-fun owner () Int)
(declare-fun gate () Int)
(declare-fun request_session () Int)
(declare-fun session () Int)
(declare-fun request () Int)
(declare-fun root () Int)
(declare-fun family () Int)
(declare-fun response () Int)
(declare-fun lifecycle () Int)
(declare-fun original_sql () Int)
(declare-fun sql () Int)
(assert
 (= gate owner))
(assert
 (= session request_session))
(assert
 (= root request))
(assert
 (let (($x27 (= family 1)))
 (or (= family 0) $x27)))
(assert
 (= response family))
(assert
 (= lifecycle family))
(assert
 (and (distinct sql original_sql) true))
(check-sat)
