; benchmark generated from python API
(set-info :status unknown)
(declare-fun table_privilege () Bool)
(declare-fun callback () Bool)
(declare-fun column_privilege () Bool)
(assert
 (let (($x13 (not table_privilege)))
 (= callback $x13)))
(assert
 (not table_privilege))
(assert
 column_privilege)
(assert
 callback)
(check-sat)
