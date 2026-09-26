# Fresh production day: addendum to the protocol

Written 2026-09-26, after the fresh day was analysed; revised the same day for the
paper's round-8 layout. `fresh_day_protocol.md` is left exactly as it was written
before the day was read; its SHA-256 is

    35ad212098ab890fa1bfbe1f8879c8c6692d9e8a39989f8aa30abd5cdd04fb4e

so a reader can check that it has not changed since this addendum.

## What changed around the protocol

- **Numbering.** The protocol refers to "Table VI and Appendix E", the paper's
  layout when it was written. The production results now sit in Section V-D, in
  Table III (the scope per endpoint, with the test days and the fresh day) and
  Table IV (calibration floor and WAF agreement).
- **Names.** In the protocol, E3 and E4 name two export queries (counts per host,
  window and JA4; same-/24 pairs). In the paper, E1 to E4 name the four evaluated
  endpoints. The two uses are unrelated.
- **Metric 6** (the base rule: Omega gate, enrichment, no known fleets) is reported
  in Table III's fresh-day block, as the protocol asks. It fired on the same two
  clean windows as the frozen configuration (`overlap_frozen_rule` in
  `production_tables.json`).
- **An addition the protocol did not list.** The calibrated z-score is also
  reported for the fresh day. It was already in the evaluation code when the day
  was first processed: the run that computed the day's windows started at
  2026-09-26T02:45Z, two minutes after the protocol was written, and its output
  carries the z-score's columns. Its threshold rule was therefore fixed before any
  count of the day was computed, but the protocol does not name it. It fired on the
  same two windows as the frozen configuration (`overlap_frozen_zcal`).
- **A variant built after the day was read.** The beta-binomial background
  (`--overdispersion`) was written after the fresh day had been analysed. Its
  fresh-day row is post hoc and marked as such in the paper; it is not covered by
  the protocol.
- **Wording.** The protocol is a local file, not an external registration, so the
  paper says the day was analysed with everything fixed in advance rather than
  that it was pre-registered.

No metric of the protocol was recomputed or dropped, and none of the frozen
configuration's choices changed.
