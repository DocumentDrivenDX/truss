; benchmark generated from python API
(set-info :status unknown)
(declare-fun caller_restriction () Bool)
(declare-fun original_permissive () Bool)
(declare-fun added_permissive () Bool)
(assert
 (let (($x9 (and original_permissive caller_restriction)))
(let (($x12 (not $x9)))
(let (($x10 (or original_permissive added_permissive)))
(let (($x11 (and $x10 caller_restriction)))
(let (($x14 (not added_permissive)))
(and $x14 $x11 $x12)))))))
(check-sat)
