; benchmark generated from python API
(set-info :status unknown)
(declare-fun s_0_0 () Bool)
(declare-fun i_0_0 () Bool)
(declare-fun s_0_1 () Bool)
(declare-fun i_0_1 () Bool)
(declare-fun s_0_2 () Bool)
(declare-fun i_0_2 () Bool)
(declare-fun s_1_0 () Bool)
(declare-fun i_1_0 () Bool)
(declare-fun s_1_1 () Bool)
(declare-fun i_1_1 () Bool)
(declare-fun s_1_2 () Bool)
(declare-fun i_1_2 () Bool)
(declare-fun s_2_0 () Bool)
(declare-fun i_2_0 () Bool)
(declare-fun s_2_1 () Bool)
(declare-fun i_2_1 () Bool)
(declare-fun s_2_2 () Bool)
(declare-fun i_2_2 () Bool)
(assert
 (= s_0_0 false))
(assert
 (= i_0_0 false))
(assert
 (= s_0_1 false))
(assert
 (= i_0_1 true))
(assert
 (= s_0_2 false))
(assert
 (= i_0_2 false))
(assert
 (= s_1_0 false))
(assert
 (= i_1_0 false))
(assert
 (= s_1_1 false))
(assert
 (= i_1_1 false))
(assert
 (= s_1_2 true))
(assert
 (= i_1_2 false))
(assert
 (= s_2_0 false))
(assert
 (= i_2_0 false))
(assert
 (= s_2_1 false))
(assert
 (= i_2_1 false))
(assert
 (= s_2_2 false))
(assert
 (= i_2_2 false))
(assert
 (let (($x106 (or (or false i_1_2) (and (or false i_1_0) (or false i_0_2)))))
(let (($x110 (or (or false i_2_1) (and (or false i_2_0) (or false i_0_1)))))
(let (($x112 (or (or true i_2_2) (and (or false i_2_0) (or false i_0_2)))))
(let (($x130 (or $x112 (and $x110 $x106))))
(let (($x148 (or $x130 (and $x130 $x130))))
(let (($x43 (or (or false s_1_2) (and (or false s_1_0) (or false s_0_2)))))
(let (($x47 (or (or false s_2_1) (and (or false s_2_0) (or false s_0_1)))))
(let (($x49 (or (or true s_2_2) (and (or false s_2_0) (or false s_0_2)))))
(let (($x67 (or $x49 (and $x47 $x43))))
(let (($x24 (or false s_0_1)))
(let (($x35 (or $x24 (and (or true s_0_0) $x24))))
(let (($x25 (or false s_0_2)))
(let (($x55 (or (or $x25 (and (or true s_0_0) $x25)) (and $x35 $x43))))
(let (($x73 (or $x55 (and $x55 $x67))))
(let (($x104 (or (or true i_1_1) (and (or false i_1_0) (or false i_0_1)))))
(let (($x124 (or $x106 (and $x104 $x106))))
(let (($x142 (or $x124 (and $x124 $x130))))
(let (($x65 (or $x47 (and $x47 (or (or true s_1_1) (and (or false s_1_0) $x24))))))
(let (($x53 (or $x35 (and $x35 (or (or true s_1_1) (and (or false s_1_0) $x24))))))
(let (($x71 (or $x53 (and $x55 $x65))))
(let (($x87 (or false i_0_1)))
(let (($x98 (or $x87 (and (or true i_0_0) $x87))))
(let (($x88 (or false i_0_2)))
(let (($x118 (or (or $x88 (and (or true i_0_0) $x88)) (and $x98 $x106))))
(let (($x136 (or $x118 (and $x118 $x130))))
(let (($x26 (or false s_1_0)))
(let (($x39 (or $x26 (and $x26 (or true s_0_0)))))
(let (($x29 (or false s_2_0)))
(let (($x63 (or (or $x29 (and $x29 (or true s_0_0))) (and $x47 $x39))))
(let (($x23 (or true s_0_0)))
(let (($x69 (or (or (or $x23 (and $x23 $x23)) (and $x35 $x39)) (and $x55 $x63))))
(let (($x152 (or (and $x69 $x136) (and $x71 $x142) (and $x73 $x148))))
(and (distinct $x152 false) true))))))))))))))))))))))))))))))))))
(check-sat)
