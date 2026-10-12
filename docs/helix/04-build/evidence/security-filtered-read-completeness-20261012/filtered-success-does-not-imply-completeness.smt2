; benchmark generated from python API
(set-info :status unknown)
(declare-fun valid_cut1_1 () Bool)
(declare-fun valid_cut1_0 () Bool)
(declare-fun active_1 () Bool)
(declare-fun active_0 () Bool)
(assert
 (let (($x14 (and valid_cut1_0 valid_cut1_1)))
(let (($x19 (not $x14)))
(let (($x12 (and valid_cut1_1 active_1)))
(let (($x11 (and valid_cut1_0 active_0)))
(let (($x15 (or $x11 $x12)))
(and $x15 $x19)))))))
(check-sat)
