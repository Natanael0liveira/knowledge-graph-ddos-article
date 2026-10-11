# Where the held-out day's metrics are, after the block

Written 2026-10-10. The held-out day's protocol (`fresh_day_protocol.md`) asks that every
metric be reported whatever its value and that the day be reported as its own block. The paper
first reported it as a block of rows in its per-configuration table, and
`fresh_day_protocol_addendum.md` refers to that block. When the 14-day held-out block got its
own table (Table VII, `heldout_block_protocol.md`), those rows left the paper's Table IV, for
space. The day is still reported apart, never pooled with the test days. This note says where
each metric now is. The frozen addendum is left as it was.

All values are in `production_tables.json`, section `fresh_day`, for the binomial configuration
(`fleets`, `union|origins`) unless stated. Rates are over the day's 1,152 clean windows.

| Metric of `fresh_day_protocol.md` | Value | In the paper | In the repository |
|---|---|---|---|
| 1. False alarms, pooled, and the decision rule | 2 of 1,152, consistent (P = 0.27) | V-D | `clean_fires`, `clean_windows` |
| 2. Median share a false alarm blocks | 41.2% | no | `clean_collateral_median` |
| 3. Flash crowds of 100 users | 1.1% of windows | no | `flash100` |
| 4. Blocked share, pooled: new A = 100, 1,000, 1x, 0.1x | 38.9, 73.4, 20.4, 0.0% | no | `new:A100`, `new:A1000`, `new:x1`, `new:x0.1` |
| 4. The same on shared stacks | 21.5, 60.9, 17.0, 0.0% | no | `shared:A100`, `shared:A1000`, `shared:x1`, `shared:x0.1` |
| 5. E1 at 0.1x, new and shared stacks | 0.0 and 0.0% | Table VI, "held" columns | `per_endpoint.E1`, `new:x0.1`, `shared:x0.1` |
| 6. The base rule (`base`, `enrichment\|omega`): false alarms | 2 of 1,152, the same two windows | no | `clean_fires`; `overlap_frozen_rule` |
| 6. The base rule: median share blocked, crowds of 100 | 41.2%, 1.0% | no | `clean_collateral_median`, `flash100` |
| 6. The base rule: blocked, new A = 100, 1,000, 1x, 0.1x | 26.3, 72.5, 17.3, 0.0% | no | as in metric 4 |
| 6. The base rule: blocked, shared | 21.5, 59.9, 16.6, 0.0% | no | as in metric 4 |
| 7. Compiled query against the exports | origins and /24 pairs equal in 1,152 of 1,152 windows; JA4 pairs in 288 of 288 without WAF blocks | App. F | `compile_production_check_fresh.json` |

The paper's Appendix F says that the repository holds every metric both protocols name.
`block_report.json` holds the block's.
