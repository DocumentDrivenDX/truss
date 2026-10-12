; benchmark generated from python API
(set-info :status unknown)
(declare-fun direct_set_predefined () Bool)
(declare-fun callback () Bool)
(declare-fun inherited_predefined () Bool)
(assert
 (let (($x15 (not direct_set_predefined)))
 (= callback $x15)))
(assert
 inherited_predefined)
(assert
 (not direct_set_predefined))
(assert
 callback)
(check-sat)
