# Held-out block: addendum on metrics

Written 2026-10-01 at 12:34 UTC, before the first part (2026-09-26 to 09-30) was exported
at 12:49 UTC. Later additions came after that export and before any count of a block day
was read:
- 2026-10-01, 12:54 UTC: one sentence on downloading a part when the drive is not at hand;
- 2026-10-02: how metric 10 matches its endpoints to E1–E4, the report script, and the
  amendment of metric 7, found when the script was run on the paper's own days.
- 2026-10-10: the amendment of metric 7 adopted, after all three parts were exported.

The file was committed and pushed after part 1 was exported, and before any count of a
block day was read. Its push time on GitHub therefore shows that it came before the
reading, though not before the export.

The addendum adds three metrics, fixes how the code is run, and amends one decision rule,
metric 7's, for the reason given below. Otherwise it changes nothing in
`heldout_block_protocol.md`:
- no configuration, parameter or endpoint;
- no injection;
- no other metric or decision rule.

## Why

An outside review of the paper (2026-09-30) asked for two things the protocol does not name:
- how reliable the scope is once the gate opens, which the held-out day could not measure,
  since its gate opened in 3 clean windows;
- the behavior over the weekly cycle, which the block's two full weeks cover.

It also asked that nothing be tuned on the block.

## Added metrics, reported whatever their value

8. **Scope reliability once the gate opens.** For the binomial configuration (configuration
   1), on clean windows:
   - the gate openings g (`clean_gate_windows`);
   - the joint misfires x (`clean_fires`);
   - and x/g, pooled and per endpoint, with the exact 95% interval.

   The block is **consistent** with the test days' conditional rate if
   P[Bin(g, 5/168) ≥ x] ≥ 0.05, where 5 of 168 are the test days' joint misfires and clean
   gate openings. It is **not consistent** otherwise.
9. **Weekly cycle.** The binomial configuration's false alarms per day
   (`clean_fires_by_fold`), summed over the four weekend days (2026-09-26, 09-27, 10-03 and
   10-04) and over the ten weekdays. This metric is descriptive, with no test.
10. **Fingerprint churn.** `ja4_churn.py` on the block days, as in the paper. Per endpoint
    and day, it gives:
    - the fingerprints absent from the profile that reach k_min origins in some window;
    - the share of windows that hold one.

    This metric is descriptive. A day with many such fingerprints is reported together with
    the false alarms of that day. `ja4_churn.py` takes its endpoints from the run it is
    given, ordered by that run's median window, and has no option to keep the paper's. It
    is run with the block's base run, and its endpoints are matched to the paper's E1–E4 by
    their role in `roles.json`.

## Metric 7, amended before reading

Run on the paper's own test days, metric 7 as written compares the arms on a botnet that
no scope can name on the three small endpoints. There a tenth of the median window is 2 to
7 attackers, fewer than the botnet's 25 stacks, and every configuration stops 0.0 to 0.1%
of it. On E4 the rule as written would prefer configuration 4 for stopping 0.1% versus 0.0%
of a 2-attacker botnet. The amended rule:
- compares the tenth-size botnet on E1, where it holds about 300 attackers, and 100
  attackers on E2–E4, the other size Section VI of the paper names;
- prefers an arm on an endpoint only if it is within the budget there and stops at least
  one point more than the baseline on new or shared stacks.

Both versions are reported, and the amended one decides. The change was fixed on the
paper's test days alone, before any count of a block day was read.

## Code

The block is run from a checkout of commit `05ccc0e`, which added the protocol
(`git worktree add <dir> 05ccc0e`), and not from the branch head. Later commits changed
two files the run imports:
- the evidence chain's JSON-LD output, in `evidence_mitigation.py`;
- declarations in `ontology/ddos_ontology.owl`, which the run reads for the sub-relation
  weights.

Neither change alters a count, and running at the frozen commit removes the question. At
that commit, `make rule-production-block production-tables-block` gives the block's
reduction, and `ja4_churn.py`, with the arguments of the `ja4-churn-block` target, gives
metric 10.

The report, `scripts/block_report.py`, is new and runs from the commit that adds it, on
those two outputs (`make block-report`). It computes metrics 1 to 10 and applies their
rules. Before any count of the block is read, `make block-report-check` runs the same code
on the paper's own reduction, and it reproduces the numbers the paper prints (21 checks).

## Nothing is tuned on the block

Once any block day is read, nothing in the protocol changes, whatever the results. The post
hoc configurations 4 and 5 are evaluated only as the comparison that the protocol's metric 7
pre-registers.

## Export and hashes

Each part is written straight to its directory on the drive. Its results are not opened or
previewed. If the drive is not at hand when a part is due, the part is downloaded to a local
folder outside the repository, moved to the drive, and the local copy deleted. A move leaves
a file's SHA-256 unchanged, and the hash addendum says where each part was downloaded.
Before any count is read, an addendum gives each file's SHA-256, number of rows,
and first and last window (`heldout_block_protocol.md`, "After the export, before the
analysis"). That addendum is committed and pushed before reading. If a hash or a protocol
file also gets an RFC 3161 or OpenTimestamps token, the token is committed with it.
