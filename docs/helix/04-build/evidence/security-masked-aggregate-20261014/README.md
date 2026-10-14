# Masked salary aggregate query-profile refusal

In the actual native broker fixture for Bob/revoked Alice/unassigned Outsider, the original relational producer is asked to compile SUM(r.salary) under the unchanged withheld-salary policy/query-use profile. It refuses with nonzero status and empty stdout before SQL is emitted. A separate diagnostic probe identifies WFT-SECURITY-QUERY-PROFILE admission refusal. Existing permitted COUNT/group/filter and protected publication controls pass in the same native run.

Native1/54.862s on runtime0.64 passes. This contributes to US-056-AC6/truss.B08 for unsupported masked aggregate use, not native SUM arithmetic, explicit raw-value permission allowance, every filter/sort/group/join/aggregate or full case qualification. No original132 case status changes. Trusted source/compiler/native custody premises remain unchanged.
