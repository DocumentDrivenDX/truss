; benchmark generated from python API
(set-info :status unknown)
(declare-fun writer_table () Bool)
(declare-fun reader_table () Bool)
(declare-fun writer_row () Bool)
(declare-fun writer_waits () Bool)
(declare-fun reader_waits () Bool)
(assert
 (= writer_waits (and writer_row reader_table (not writer_table))))
(assert
 (= reader_waits (and writer_row reader_table)))
(assert
 (=> writer_row writer_table))
(assert
 (not (and writer_table reader_table)))
(assert
 writer_waits)
(assert
 reader_waits)
(check-sat)
