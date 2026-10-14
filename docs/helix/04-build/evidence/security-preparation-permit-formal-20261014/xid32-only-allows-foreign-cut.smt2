; benchmark generated from python API
(set-info :status unknown)
(declare-fun supplied_data_xid8 () (_ BitVec 64))
(declare-fun original_data_xid8 () (_ BitVec 64))
(assert
 (let (($x54 (and (distinct original_data_xid8 supplied_data_xid8) true)))
(let (($x9 (= ((_ extract 31 0) original_data_xid8) ((_ extract 31 0) supplied_data_xid8))))
(and $x9 $x54))))
(check-sat)
