; benchmark generated from python API
(set-info :status unknown)
(declare-fun bridge_inherited_predefined () Bool)
(declare-fun set_bridge () Bool)
(declare-fun direct_set_predefined () Bool)
(declare-fun inherited_predefined () Bool)
(declare-fun callback () Bool)
(assert
 (let (($x12 (or inherited_predefined direct_set_predefined (and set_bridge bridge_inherited_predefined))))
 (let (($x13 (not $x12)))
 (= callback $x13))))
(assert
 direct_set_predefined)
(assert
 callback)
(check-sat)
