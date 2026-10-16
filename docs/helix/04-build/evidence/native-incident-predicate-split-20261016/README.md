# Separate typed incident-edge predicates

The final object inventory keeps its original image-first CASE and node ordinal ordering. The incident predicate now uses separate source and target EXISTS subqueries, preserving exact typed endpoints and membership by relationship type and edge ID, including deleted nodes, self edges and parallel edges. There are no API, authority, storage or deadline changes.

Astra reviewed the predicate equivalence. Eight basic native workflows pass. The unchanged original 1,000-node/1,000-edge matrix passed, including 1,000 identity reads, 100 key reads, 200 individually committed updates and five changed 1,000-object update groups with reopened readback. Median 1,000-update apply was 9,816.563 ms, commit 3,828.218 ms and total 13,751.151 ms. The report explicitly leaves performance qualification not evaluated. This still lacks reliable statement-deadline headroom; no causal speedup or release-runner qualification is claimed.
