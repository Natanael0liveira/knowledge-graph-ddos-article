# Held-out block: protocol, fixed before the block is exported

Written 2026-09-28. This file is committed and pushed to the public repository before
any day of the block is exported, and the push time on GitHub is its external
timestamp. No day of the block has been exported or read. The only production days
read so far are 2026-09-17 to 2026-09-25: the paper's eight days and its held-out day.

A first draft chose the 30 days before the paper's data, but the operator's log store
no longer holds them. On 2026-09-28 the export queries for 2026-08-18 to 2026-08-24,
and a list of the days held from 2026-08-01 to 2026-09-16, returned no rows. Nothing
was read, and the block became the 14 days after the paper's data.

## The block

- **Days.** The 14 days after the held-out day, 2026-09-26 to 2026-10-09, 00:00–24:00
  UTC, for the same four endpoints (E1–E4), with no new endpoint selection. They make
  two full weeks, so every weekday appears twice.
- **History and test.** The paper's nine days, 2026-09-17 to 2026-09-25, are history
  only. Every block day is a test day, calibrated on all earlier days: the paper's
  rolling split, with `--min-calib-days 9`. The cross-fitted runs use the same days
  with `--split crossfit`.
- **Endpoints.** E1–E4 are the paper's four hosts, in the paper's order. The reduction
  takes them from the paper's own run (`--endpoints-from`), so a change in volume, or a
  fifth host that qualifies on every block day, does not renumber them.
- **Queries.** The queries that produced the held-out day's exports E3 and E4, with
  only their date range changed. They stay on the data drive, since they carry the log
  store's table and column names; `bindings/exports_clickhouse_example.sql` documents
  them with placeholder names.
- **Export.** The log store keeps between 8 and 12 days: the paper's first day was
  still there 8 days later, and on 2026-09-28 nothing before 2026-09-17 was left. The
  block is therefore exported in three parts, each into its own directory and within a
  week of its first day: 2026-09-26 to 09-30, 10-01 to 10-05 and 10-06 to 10-09. How
  the days are split into parts changes no result.
- **Missing days.** A test day the log store no longer holds at its export is left out
  and reported. The block is run only if at least 7 test days remain.
- **Size.** The 14 test days hold about 15,800 endpoint windows. At the test days' rate
  about 14 false alarms are expected, and the consistency test below fails from about
  21, which a doubled rate reaches with probability 0.93. On one endpoint, 4,032 windows
  can show a configuration within the budget with up to 27 false alarms (0.67%).
- **Data directory.** The block has its own directory on the drive, with copies of the
  nine history days, so the paper's runs never read it. `make rule-production-block`
  and `make production-tables-block` run the block.

## Frozen code and configuration

- **Code.** The repository at the commit that adds this file, including the two make
  targets above. Only the data change.
- **Parameters, as in the paper.** Unit: distinct origins. k_min = 5, W = 300 s, ρ = 3.
  The gates sit at their 99th percentile. The level λ_e is calibrated to the 1% budget
  and capped at 0.01. Known fleets are exempted at a 5% share.
- **Configurations, from Tables II and VI of the paper:**
  1. the binomial configuration: distinct-origin gate, the test united with the unseen
     filter, known fleets exempt (primary);
  2. the base rule, Ω gate (reference);
  3. the unseen filter as its own trigger (the baseline of the next test);
  4. the cross-fitted beta-binomial behind the seasonal gate;
  5. the binomial scope with known fleets as its own trigger, on E1;
  6. the calibrated z-score (reference).
- **Injection and flash crowds.** As in the paper:
  - the 25-stack botnet on new, shared and adversarial stacks, with 100 and 1,000
    attackers per window and 0.1× and 1× the median window;
  - flash crowds of 100 and 1,000 users drawn from each day's own clients.
- **Reduction.** `production_tables.py`, with the 14 block days as its test folds. The
  tests below are computed from its output.

## Metrics, in the order they will be reported

1. **Primary A: the binomial configuration's false alarms**, pooled over the four
   endpoints. Report the count, the windows, the rate and the exact 95% interval.
   - The block is **consistent** with the test days if P[Bin(n, r) ≥ x] ≥ 0.05, where
     r = 5/5,643 = 0.000886 is the test days' rate. It is **not consistent** otherwise.
2. **Primary B: the budget of configurations 3 to 5**, per endpoint. Report the
   false-alarm count, the rate and the exact 95% upper bound.
   - A configuration is **within the budget** on an endpoint if its rate is at most 1%.
   - It is **shown within the budget** if its upper bound is at most 1%.
3. **Detection.** Blocked share of the injected botnets for every configuration, pooled and
   per endpoint:
   - new and shared stacks;
   - A = 100 and 1,000 attackers;
   - 0.1× and 1× the median window.

   Also report E1's tenth-size botnet on new and shared stacks, per day.
4. **Flash crowds** of 100 and 1,000 users: the firing rate and the median share of the
   window's clients blocked.
5. **Cost of a false alarm:** the median share of the window's clients blocked.
6. **Clustering:** false alarms per day and endpoint.
7. **The comparison Section VI of the paper asks for.** On each endpoint, the baseline
   (3) against the arms (4 and 5): which are within the budget, and how much of the
   tenth-size botnet each stops on new and shared stacks. An arm is preferred on an
   endpoint only if it is within the budget there and stops more on new or shared stacks.

Every metric is reported whatever its value. The block is reported as its own table, and
the paper's test days and held-out day are not recomputed on it. The paper reports the
block as a pre-specified test and revises the recommendation of Section VI by metric 7.

## After the export, before the analysis

- An addendum gives the SHA-256 of every exported file before any count is read, next to
  those of the history copies, which must equal the paper's files. It also gives each
  file's number of rows and its first and last window, to show that no part was cut short.
- The exports stay on the data drive. Only the rates enter the repository.
