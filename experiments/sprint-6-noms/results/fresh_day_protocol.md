# Fresh production day: protocol, fixed before the day was read

Written 2026-09-26T02:43Z. The day's three exports had been opened only to check
their columns and row counts (E3: 44,601 rows; E4: 2,275; compiled query: 1,152).
No count of the day had been looked at. SHA-256 of the files analysed:

| Export | SHA-256 |
|---|---|
| E3, per host, window and JA4 | `b1d1737458ea6de3f07152cbee9752b0c5910f71ae3f602ac7628ef137504bf1` |
| E4, same-/24 pairs | `2520b8118fccf722f0000a0473a76ecd694175770f9eef87851216f54974fdf8` |
| Ontology-compiled count query | `6f43ef0f810003b61356196d0ec1b5ebff3e850d3b4108bd76b43fb0e82a8ee8` |

The exports stay on the data drive. Only the rates below enter the repository.

## The day

2026-09-25, 00:00–24:00 UTC. It was exported after every choice below had been
made and reported (Table VI and Appendix E of the paper, test days 2026-09-20 to
2026-09-24).

## The frozen configuration

Nothing below is tuned on the day.

- Unit: distinct origins (`--unit origin`), k_min = 5, W = 300 s.
- Calibration: rolling. The day is a sixth test fold, calibrated on every earlier
  day (2026-09-17 to 2026-09-24): profile, tau (p99 of Omega), the distinct-origin
  gate (p99 of distinct origins), and the scope's level lambda_e (1% budget,
  capped at 0.01), rho = 3.
- Known fleets at 5% (`--fleets 0.05`), the share chosen on the design days.
- Gate: distinct origins at or above their p99. Scope: the enrichment test united
  with the unseen-fingerprint filter.
- Injection: the canonical botnet (M = 25 stacks, 90% on stacks), `fresh` and
  `tail` stacks, A = 100 and 1,000 attackers per window, and botnets of 1x and 0.1x
  the endpoint's median calibration window. Flash crowds of 100 and 1,000 users
  are drawn from the endpoint's own test traffic. All as in the paper.

## Metrics, in the order they will be reported

1. **Primary: clean-window false alarms** of the frozen configuration, pooled over
   the endpoints the paper evaluates. Report count, windows and rate, and the 95%
   upper bound when the count is 0.
   - Decision rule: the test days gave 5 false alarms in 5,643 clean windows
     (r = 0.000886). The day is **consistent** with them if
     P[Bin(n_day, r) >= x_day] >= 0.05, and **not consistent** otherwise.
   - With about 1,150 windows this means consistent up to 3 false alarms.
   - The day's windows can at best bound the rate near 0.26% (rule of three); they
     cannot establish it.
2. Median share of a false alarm window's clients that the filter blocks.
3. Flash crowds of 100 users: share of windows where the configuration fires.
4. Blocked share of the injected botnet, pooled: new and shared stacks at A = 100
   and 1,000, 1x, and 0.1x.
5. E1 at 0.1x, new and shared stacks: the stealth-regime cell.
6. The same metrics for the base rule of Table VI (Omega gate, enrichment, no
   fleets) on the same day, for reference.
7. **Ontology path.** Agreement of the compiled query with the exports on the day:
   - share of windows whose distinct origins and same-/24 pairs are equal;
   - JA4 class sizes, in the windows where the WAF blocked no client.

Every metric is reported whatever its value. The day is reported as its own block,
and the test-day numbers of Table VI are not recomputed on it.
