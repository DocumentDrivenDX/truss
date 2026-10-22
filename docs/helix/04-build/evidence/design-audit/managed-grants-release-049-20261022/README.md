# Managed platform grants v0.0.49 release qualification

This packet supports [PLAN-MANAGED-GRANTS-001](../../../managed-platform-grants-plan.md)
and [RELEASE-PYTHON-0.0.49](../../../releases/v0.0.49.md). Final publication is
pending. Preliminary results below do not establish qualification of a public
v0.0.49 package.

`preliminary/receipt.json` inventories the retained preliminary evidence and
records its limits, including earlier failed attempts and incomplete raw-log
retention. The integrated macOS ARM64 candidate passed the selected 20-module
campaign (128 tests, no skips), the 62-case HF corpus, nine strict protected
checks, the original public workload and the lifecycle supplement. The public
workload retains 1,000 objects and 1,000 edges, 1,000 reads and 200 committed
updates. These counts describe the retained candidate receipts only.

The candidate source48 captures are preliminary inputs. They must not be
substituted for captures from the checksum-verified, actually published
v0.0.48 wheel. Final source48 admission must preserve every published immutable
artifact and the original migration manifest before adding its route to the
managed-grants target.

`supplemental/run_final_local_campaign.py` is the final local campaign producer.
It records the wheel, input files, installed payload, exact independent UMF
oracle, Bun and PostgreSQL identities and verifies them again at completion.
The lifecycle producer is retained unchanged in the same directory. Final local,
hosted Linux and public-download receipts will be added separately so the
preliminary record remains intact.

The mandatory finite release campaign is defined by
[the release workflow](../../../../../../.github/workflows/release.yml).
The historical broad all-discovery diagnostic remains incomplete and
unqualified. Actual Lakebase acceptance, TLS/token behavior and consumer
adoption remain separate gates; this packet makes no acceptance claim for them.
