; benchmark generated from python API
(set-info :status unknown)
(declare-fun privileged_role () Bool)
(declare-fun definer_execute () Bool)
(declare-fun column_privilege () Bool)
(declare-fun table_privilege () Bool)
(declare-fun callback () Bool)
(assert
 (let (($x10 (or table_privilege column_privilege definer_execute privileged_role)))
 (= callback (not $x10))))
(assert
 column_privilege)
(assert
 callback)
(check-sat)
