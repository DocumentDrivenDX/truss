; benchmark generated from python API
(set-info :status unknown)
(declare-fun caller_restriction () Bool)
(declare-fun original_permissive () Bool)
(declare-fun added_restriction () Bool)
(assert
 (let (($x9 (and original_permissive caller_restriction)))
(let (($x12 (not $x9)))
(and $x9 added_restriction $x12))))
(check-sat)
