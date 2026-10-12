; benchmark generated from python API
(set-info :status unknown)
(declare-fun a1 () Bool)
(declare-fun s1 () Bool)
(declare-fun i1 () Bool)
(declare-fun a0 () Bool)
(declare-fun s0 () Bool)
(declare-fun i0 () Bool)
(assert
 (let (($x65 (or (and (not i0) (not s0) a0 (not i1) (not s1) a1) (and (not i0) (not s0) a0 (not i1) s1 (not a1)) (and (not i0) (not s0) a0 (not i1) s1 a1) (and (not i0) (not s0) a0 i1 (not s1) (not a1)) (and (not i0) (not s0) a0 i1 (not s1) a1) (and (not i0) (not s0) a0 i1 s1 (not a1)) (and (not i0) (not s0) a0 i1 s1 a1) (and (not i0) s0 (not a0) (not i1) (not s1) a1) (and (not i0) s0 (not a0) (not i1) s1 (not a1)) (and (not i0) s0 (not a0) (not i1) s1 a1) (and (not i0) s0 (not a0) i1 (not s1) (not a1)) (and (not i0) s0 (not a0) i1 (not s1) a1) (and (not i0) s0 (not a0) i1 s1 (not a1)) (and (not i0) s0 (not a0) i1 s1 a1) (and (not i0) s0 a0 (not i1) (not s1) a1) (and (not i0) s0 a0 (not i1) s1 (not a1)) (and (not i0) s0 a0 (not i1) s1 a1) (and (not i0) s0 a0 i1 (not s1) (not a1)) (and (not i0) s0 a0 i1 (not s1) a1) (and (not i0) s0 a0 i1 s1 (not a1)) (and (not i0) s0 a0 i1 s1 a1) (and i0 (not s0) (not a0) (not i1) (not s1) a1) (and i0 (not s0) (not a0) (not i1) s1 a1) (and i0 (not s0) (not a0) i1 (not s1) (not a1)) (and i0 (not s0) (not a0) i1 (not s1) a1) (and i0 (not s0) (not a0) i1 s1 (not a1)) (and i0 (not s0) (not a0) i1 s1 a1) (and i0 (not s0) a0 (not i1) (not s1) a1) (and i0 (not s0) a0 (not i1) s1 (not a1)) (and i0 (not s0) a0 (not i1) s1 a1) (and i0 (not s0) a0 i1 (not s1) (not a1)) (and i0 (not s0) a0 i1 (not s1) a1) (and i0 (not s0) a0 i1 s1 (not a1)) (and i0 (not s0) a0 i1 s1 a1) (and i0 s0 (not a0) (not i1) (not s1) a1) (and i0 s0 (not a0) (not i1) s1 (not a1)) (and i0 s0 (not a0) (not i1) s1 a1) (and i0 s0 (not a0) i1 (not s1) (not a1)) (and i0 s0 (not a0) i1 (not s1) a1) (and i0 s0 (not a0) i1 s1 (not a1)) (and i0 s0 (not a0) i1 s1 a1) (and i0 s0 a0 (not i1) (not s1) a1) (and i0 s0 a0 (not i1) s1 (not a1)) (and i0 s0 a0 (not i1) s1 a1) (and i0 s0 a0 i1 (not s1) (not a1)) (and i0 s0 a0 i1 (not s1) a1) (and i0 s0 a0 i1 s1 (not a1)) (and i0 s0 a0 i1 s1 a1))))
(and (distinct $x65 $x65) true)))
(check-sat)
