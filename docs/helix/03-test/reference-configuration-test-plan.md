---
ddx:
  id: truss.reference-configuration-test-plan
  type: test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: truss.reference-configuration
      kind: informed_by
    - id: CONTRACT-007
      kind: informed_by
    - id: CONTRACT-008
      kind: informed_by
---

# Reference configuration qualification

Authority: [configuration candidate](../02-design/contracts/reference-configuration.proposal.md)
CFG-01–12; existing original embedding and bootstrap Contracts continue to govern
native admission. This plan applies to the actual reference composition/launcher
and its installed Python consumer, not a parallel test-only loader.

Run CFG-01–05/07/08 against installed package boundaries with a deterministic
host adapter: spy on environment reads, object identity, adapter construction,
connection/SQL/worker/filesystem effects and retry count. Require zero effects for
invalid/unsupported options and zero environment reads for embedded injection.
Exercise all declared precedence combinations and duplicate keys within one
layer, not legitimate overrides across layers. Record exact input/profile/package
pins and safe results; do not serialize original host objects for evidence.

CFG-06/10 use synthetic sensitive markers across every sink: console, file,
bridge/export receiver, exception text, repr and fingerprint inputs. A hash of a
secret does not satisfy absence. Change visibility while verifying unchanged
structured event meaning and durable request outcome. Include a hostile repr
fixture to prove no host-handle stringification. Actual OTel receive/mapping and
bounded outage/drop tests remain part of the observability qualification.

CFG-09 runs on the selected actual pgserver tuple with owned disposable/retained
directories and independently observes runtime custody refusal. CFG-11/12 need
actual original native transaction/account/configuration producers: change startup
options while a transaction is live and change native configuration independently.
Prove no budget refund/authority mint and one pre-effect native drift refusal.
Fake options or schema-valid artifacts cannot qualify these native cases.

Publish exact commands/tool/package/source/profile revisions, results and scoped
capture limits once implementation exists. None of CFG-01–12 is passed by this
plan. Existing local runtime tests and native configuration snapshots remain
separate, narrower evidence; reuse them only where the actual mapped behavior is
unchanged. Conditional formal analysis applies to native admission/account
properties through their owning designs; configuration parsing itself has no
new temporal-analysis obligation.
