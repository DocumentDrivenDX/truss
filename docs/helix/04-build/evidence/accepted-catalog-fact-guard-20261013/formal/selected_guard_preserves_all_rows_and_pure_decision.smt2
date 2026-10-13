; benchmark generated from python API
(set-info :status unknown)
(declare-sort SelectedFactRow 0)
(declare-fun operation () Int)
(declare-fun continuously_held_cut () Bool)
(declare-fun installed_before_effect_guard () Bool)
(declare-fun fixed_source_caller_context_pure_policy ((Array Int SelectedFactRow)) Bool)
(declare-fun before () (Array Int SelectedFactRow))
(declare-fun value () SelectedFactRow)
(declare-fun absent () SelectedFactRow)
(declare-fun key () Int)
(declare-fun same_backend () Bool)
(assert
 (>= operation 0))
(assert
 (<= operation 3))
(assert
 continuously_held_cut)
(assert
 installed_before_effect_guard)
(assert
 (let (($x28 (fixed_source_caller_context_pure_policy before)))
(let ((?x24 (ite (= operation 3) ((as const (Array Int SelectedFactRow)) absent) (store before key (ite (= operation 2) absent value)))))
(let (($x13 (not continuously_held_cut)))
(let (($x16 (or $x13 (and same_backend (not installed_before_effect_guard)))))
(let ((?x25 (ite $x16 ?x24 before)))
(let (($x27 (fixed_source_caller_context_pure_policy ?x25)))
(let (($x29 (and (distinct $x27 $x28) true)))
(let (($x26 (and (distinct ?x25 before) true)))
(or $x26 $x29))))))))))
(check-sat)
