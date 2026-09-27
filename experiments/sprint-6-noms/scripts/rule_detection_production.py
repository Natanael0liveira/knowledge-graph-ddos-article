#!/usr/bin/env python3
"""Sprint 6 (NOMS) — the rule per window on production traffic, with an injected botnet.

rule_detection.py evaluates Omega(S) >= tau per five-minute window on generated
traffic. This script runs the same rule on days of production traffic from a CDN,
exported as aggregates so that no address or URI leaves the log store:

  E1  sessions per (host, 5-min window, JA4), and how many of them the WAF blocked;
  E2  pairs of sessions sharing a /24 (/48 for IPv6) per (host, window), over the
      requests the WAF did not block;
  E3  E1 with distinct client addresses counted next to sessions;
  E4  E2 over distinct client addresses.

A session is a client connection (address, port) and a host is an endpoint.
``--unit origin`` makes the client address the rule's unit instead, from E3 and
E4: one client opening many connections then counts once (the paper's method). The three
sub-relations the rule reads are equivalence relations, so Omega is a function of
class sizes and the counts suffice:

  Omega = w_tls * sum_f C(n_f, 2) + w_ep * C(n, 2) + w_net * P_24

Protocol:

- clean traffic is every session with no WAF-blocked request;
- each host's windows are split in two. The calibration part gives the host's JA4
  profile and tau, a percentile of Omega over its windows; the test part is where
  the rule is evaluated. ``--split hours`` (default) alternates UTC hours, so both
  parts cover the daily cycle; ``halves`` calibrates on the first twelve hours and
  ``days`` on every day but the last. ``rolling`` tests each day on every day
  before it. ``crossfit`` does the same, but when it fits the scope's level, the
  z-score thresholds and the known fleets it judges each earlier day against a
  profile of the other earlier days, so that no calibration window is part of the
  profile it is judged against, as no test window is (tau, the origin gate and
  the test day's profile are as in ``rolling``);
- false alarms: the rule on the clean test windows;
- detection: A attacker sessions injected into each test window, built as the
  generator builds them (scenario_stealth.yaml). With probability 0.9 a session
  takes one of M stack fingerprints, uniformly, otherwise a fingerprint of its
  own, and it comes from one of 2,000 /24s. The stack fingerprints are ``fresh``
  (absent from the traffic, the generator's default), ``tail`` (drawn from the
  host's profile outside its ten most common, so real users share them), or
  ``adversarial`` (the host's M most common fingerprints);
- relative size (``--attackers-rel``): the same botnet sized as a fraction of the
  host's median calibration window, on a separate random stream;
- baseline scopes, under the same Omega >= tau: a per-fingerprint z-score against
  the profile (z > 3), a filter of fingerprints absent from the profile, and the
  union of that filter with the enrichment test; and two baselines calibrated to
  the enrichment test's budget (a filter in at most 1% of the endpoint's
  attack-free calibration windows): the same z-score with its threshold raised to
  that budget (``zcal``), and a z-score of each fingerprint against its own counts
  over the calibration windows (``zhist``);
- a second trigger, the number of distinct origins at or above its 99th percentile
  over the calibration windows, under which every scope is reported again;
- flash crowd: N legitimate sessions drawn from the host's own test traffic added
  to one window, with the host's rate of same-/24 pairs;
- WAF diagnostic: the scope on the full test windows, blocked sessions included,
  compared with the WAF's verdict. By default the profile excludes the clients the
  WAF blocked, so a fingerprint the WAF blocks is rare in it by construction;
  ``--waf-in-profile`` builds everything from all clients instead.

Three rules are compared, as in rule_detection.py, with condition (iv) off:
``omega`` (|S| >= k_min and Omega >= tau), ``pipeline`` (omega, then a non-empty
enrichment scope) and ``enrichment`` (|S| >= k_min and a non-empty scope).

Approximations, all conservative or negligible:
- the scope is judged on JA4 alone. The /24 conjunct of derive_scope_enriched
  needs per-session prefixes, which the export does not carry, and it can only
  narrow a filter;
- E2 drops blocked requests, not blocked connections, so a connection with both
  kinds stays in P_24 (a median difference of 0 sessions per window);
- injected sessions draw their /24s from a pool disjoint from real prefixes, so
  they add pairs among themselves only.

The exports are third-party operational data: keep them, and this script's
outputs, on the data drive, outside the repository.

Usage:
    python rule_detection_production.py --data-dir $DATA_ROOT/azion \\
        --out-dir $DATA_ROOT/azion/results --significance 0.01
"""
import argparse
import json
import logging
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import logsumexp
from scipy.stats import betabinom, binom

HERE = Path(__file__).resolve()
EXP = HERE.parents[2]
sys.path[:0] = [str(EXP / "pillar4-evidence-mitigation" / "scripts"), str(EXP / "common")]
from evidence_mitigation import derive_scope_enriched  # noqa: E402  (self-check)
from kg_ontology import WEIGHTS  # noqa: E402  (coordinationWeight, read from the ontology)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)
W_TLS, W_EP, W_NET = (WEIGHTS[r] for r in ("relatedByTLSFingerprint", "relatedByEndpointConvergence",
                                           "relatedByNetworkProximity"))
NO_TLS = "-"                                # the log's JA4 field on plain-HTTP requests
# Export column names (the queries were written in Portuguese) -> ours, per unit.
# Internally "sessions" counts whichever unit the rule reads.
COLS = {"session": {"janela": "window", "sessoes": "sessions",
                     "sessoes_bloqueadas_waf": "waf_sessions",
                     "pares_mesmo_prefixo": "net_pairs"},
        "origin": {"janela": "window", "clientes": "sessions",
                    "clientes_bloqueados_waf": "waf_sessions",
                    "pares_mesmo_prefixo": "net_pairs"}}


def c2(counts):
    counts = np.asarray(counts, dtype=float)
    return float((counts * (counts - 1) / 2).sum())


def load_day(day, unit):
    """The fingerprint and prefix exports of one day, in the rule's unit.

    Files are Metabase downloads (JSON or CSV), told apart by their columns. E3
    carries E1's columns too, so it serves either unit.
    """
    found = {}
    for f in sorted(day.iterdir()):
        if f.name.startswith("._") or f.suffix not in (".json", ".csv"):
            continue                        # AppleDouble files macOS writes on exFAT
        df = (pd.DataFrame(json.loads(f.read_text())) if f.suffix == ".json"
              else pd.read_csv(f))
        if "ja4" in df:
            key = "e3" if "clientes" in df else "e1"
        elif "pares_mesmo_prefixo" in df:
            key = "e4" if "clientes" in df else "e2"
        else:
            continue
        if key in found:
            raise SystemExit(f"{day}: more than one {key.upper()} export")
        found[key] = df
    fp = found.get("e3") if unit == "origin" else found.get("e1", found.get("e3"))
    pr = found.get("e4") if unit == "origin" else found.get("e2")
    if fp is None or pr is None:
        need = "E3 and E4" if unit == "origin" else "E1 (or E3) and E2"
        raise SystemExit(f"{day}: --unit {unit} needs {need}, found {sorted(found)}")
    fp, pr = (d[[c for c in d if c in COLS[unit] or c in ("host", "ja4")]]
              .rename(columns=COLS[unit]) for d in (fp, pr))
    for df in (fp, pr):
        df["window"] = pd.to_datetime(df["window"], utc=True)
    return fp, pr


def build_windows(e1, e2, waf_in_profile=False):
    """One record per (host, window) with the counts the rule reads.

    ``clean`` is every client the WAF did not block, the traffic the profile, the
    calibration and the clean test windows are built from. With ``waf_in_profile``
    it is every client, blocked ones included: the profile then holds whatever the
    WAF blocks, for scoring the scope against the WAF's verdicts without the
    profile having seen them removed (waf_labels.py). The same-/24 pairs of the
    export still exclude blocked requests, which moves Omega only.
    """
    e1 = e1.assign(clean=e1["sessions"] - (0 if waf_in_profile else e1["waf_sessions"]))
    p24 = e2.set_index(["host", "window"])["net_pairs"]
    recs = []
    for (host, win), g in e1.groupby(["host", "window"], sort=True):
        tls = g[g["ja4"] != NO_TLS].set_index("ja4")
        clean = tls["clean"][tls["clean"] > 0].sort_values(ascending=False)
        recs.append({"host": host, "window": win,
                     "clean": clean, "n": int(g["clean"].sum()),
                     "p24": float(p24.get((host, win), 0.0)),
                     "all": tls["sessions"], "waf": tls["waf_sessions"],
                     "n_all": int(g["sessions"].sum()),
                     "n_nontls": int(g.loc[g["ja4"] == NO_TLS, "clean"].sum())})
    return recs


def part_of(win, how, last_day):
    if how == "hours":
        return "calib" if win.hour % 2 == 0 else "test"
    if how == "halves":
        return "calib" if win.hour < 12 else "test"
    return "calib" if win.date() < last_day else "test"


def log_tail(dist, c, n, *params):
    """log P[X >= c] for each c, X ~ dist on 0..n.

    The log of dist.sf where that is a float, and the tail summed from dist.logpmf
    where sf underflows to 0: the counts of fleets and of large botnets reach far
    beyond a float's range, and a p-value of 0 would set a calibrated level to 0.
    """
    c = np.asarray(c, dtype=float)
    params = [np.broadcast_to(np.asarray(p, dtype=float), c.shape) for p in params]
    with np.errstate(divide="ignore"):
        out = np.log(dist.sf(c - 1, n, *params))
    for i in np.flatnonzero(np.isneginf(out)):
        k = np.arange(int(c[i]), int(n) + 1)
        out[i] = logsumexp(dist.logpmf(k, n, *(p[i] for p in params)))
    return out


def adjusted_p(counts, profile, rho, exclude=frozenset()):
    """Natural log of the Bonferroni-adjusted binomial p-value of each fingerprint
    of a window.

    ``counts`` holds a window's TLS sessions per fingerprint, most common first;
    ``profile`` the host's prevalence per fingerprint, with its session count in
    ``attrs["n"]``. A fingerprint below the enrichment ratio ``rho``, or in
    ``exclude`` (the host's known fleets), gets inf. With ``profile.attrs["phi"]``
    (``--overdispersion``), a fingerprint of the profile with intra-window
    correlation phi > 0 is tested against a beta-binomial of the same mean instead.
    Levels are compared in logs too (log_tail).
    """
    counts = counts[counts > 0]
    n = int(counts.sum())
    if not n:
        return counts.index, np.array([])
    eps = 1.0 / max(profile.attrs["n"], 1)
    family = len(profile.index.union(counts.index))
    bf = profile.reindex(counts.index).fillna(0.0).to_numpy() + eps
    c = counts.to_numpy(dtype=float)
    lp = log_tail(binom, c, n, np.minimum(bf, 1.0))
    phi = profile.attrs.get("phi")
    if phi is not None:
        ph = phi.reindex(counts.index).fillna(0.0).to_numpy()
        od = ph > 1e-9
        if od.any():
            bb = np.minimum(bf[od], 1.0 - 1e-12)
            shape = (1.0 - ph[od]) / ph[od]
            lp[od] = log_tail(betabinom, c[od], n, bb * shape, (1.0 - bb) * shape)
    adj = np.where(c / n / bf >= rho, lp + np.log(family), np.inf)
    if exclude:
        adj = np.where(counts.index.isin(list(exclude)), np.inf, adj)
    return counts.index, adj


def scope(counts, profile, rho, log_alpha, max_values=256, exclude=frozenset()):
    """The JA4 branch of derive_scope_enriched(significance=exp(log_alpha)), on
    class sizes. The self-check compares both on expanded windows.
    """
    idx, adj = adjusted_p(counts, profile, rho, exclude)
    return set(idx[adj < log_alpha][:max_values])


def known_fleets(cal, prof, args):
    """Fingerprints the test names, at the nominal level, in at least a share
    ``args.fleets`` of the calibration windows: legitimate fleets that switch on
    together and would otherwise set the calibrated level. They leave the scope
    and the level's calibration; an attacker presenting one is not scoped."""
    if args.fleets is None:
        return frozenset()
    el = [r for r in cal if r["n"] >= args.k_min]
    named = {}
    for r in el:
        idx, adj = adjusted_p(r["clean"], prof(r), args.rho)
        for f in idx[adj < np.log(args.significance)]:
            named[f] = named.get(f, 0) + 1
    return frozenset(f for f, c in named.items() if el and c / len(el) >= args.fleets)


def judge(legit, n_legit, p24, profile, args, bot=None, log_alpha=None, exclude=frozenset(), cal=None):
    """Omega, scope, coverage and collateral of one window.

    ``legit`` counts the TLS sessions of legitimate users per fingerprint and
    ``n_legit`` all of them, plain-HTTP ones included; ``bot`` counts the injected
    attacker sessions per fingerprint.
    """
    total = legit if bot is None else legit.add(bot, fill_value=0)
    n = n_legit + (int(bot.sum()) if bot is not None else 0)
    omega = W_TLS * c2(total.to_numpy()) + W_EP * c2([n]) + W_NET * p24
    la = np.log(args.significance) if log_alpha is None else log_alpha
    named = (scope(total.sort_values(ascending=False), profile, args.rho, la, exclude=exclude)
             if n >= args.k_min else set())
    coll = float(legit[legit.index.isin(named)].sum() / n_legit) if named and n_legit else 0.0
    cov = (float(bot[bot.index.isin(named)].sum() / bot.sum())
           if bot is not None and named else 0.0)
    out = {"size": n, "omega": omega, "scope_named": bool(named), "n_named": len(named),
           "scope_recall": cov, "scope_collateral": coll}
    picks = baseline_scopes(total, profile, args, cal)
    # The union of the enrichment test and the unseen filter: the calibrated level is
    # set by fleets, which present fingerprints of the profile, and no fleet presents
    # one absent from it.
    picks["union"] = named | picks["unseen"]
    for name, picked in picks.items():
        out[f"{name}_named"] = bool(picked) and n >= args.k_min
        out[f"{name}_recall"] = (float(bot[bot.index.isin(picked)].sum() / bot.sum())
                                 if bot is not None and picked else 0.0)
        out[f"{name}_collateral"] = (float(legit[legit.index.isin(picked)].sum() / n_legit)
                                     if picked and n_legit else 0.0)
    return out, total, named


def baseline_scopes(counts, profile, args, cal=None):
    """Simple scopes an operator could derive instead of the enrichment test.

    ``zscore``  every fingerprint whose count exceeds its expectation under the
                profile by more than three standard deviations (normal approximation,
                no multiple-testing correction, no calibration);
    ``unseen``  every fingerprint absent from the profile seen in at least k_min
                units, the case the injected botnet stacks fall in;
    ``zcal``    the ``zscore`` scope with its threshold calibrated per endpoint to the
                enrichment test's budget (``cal["zcal"]``, see calibrate_baselines);
    ``zhist``   every fingerprint whose count exceeds its own mean over the calibration
                windows by more than ``cal["zhist"]`` of its own standard deviations
                (at least one unit), the same budget.
    """
    counts = counts[counts > 0]
    n = float(counts.sum())
    empty = {"zscore": set(), "unseen": set()} | ({"zcal": set(), "zhist": set()} if cal else {})
    if not n:
        return empty
    b = profile.reindex(counts.index).fillna(0.0).to_numpy() + 1.0 / max(profile.attrs["n"], 1)
    z = (counts.to_numpy(dtype=float) - n * b) / np.sqrt(n * b * (1 - np.minimum(b, 0.999999)))
    unseen = ~counts.index.isin(profile.index) & (counts.to_numpy() >= args.k_min)
    out = {"zscore": set(counts.index[z > 3]), "unseen": set(counts.index[unseen])}
    if cal:
        out["zcal"] = set(counts.index[z > cal["zcal"]])
        out["zhist"] = set(counts.index[history_z(counts, cal) > cal["zhist"]])
    return out


def history_z(counts, cal):
    """z of each fingerprint's count against its own calibration history."""
    mu = cal["mu"].reindex(counts.index).fillna(0.0).to_numpy()
    sd = cal["sd"].reindex(counts.index).fillna(0.0).to_numpy()
    return (counts.to_numpy(dtype=float) - mu) / np.maximum(sd, 1.0)


def history(windows, k_min):
    """Mean and standard deviation of each fingerprint's count over the windows."""
    hist = pd.DataFrame([r["clean"] for r in windows
                         if r["n"] >= k_min and r["clean"].sum() > 0]).fillna(0.0)
    return {"mu": hist.mean(), "sd": hist.std(ddof=0)}


def calibrate_baselines(cal, prof, args, hist_of=None):
    """Thresholds of the two calibrated baselines, at the enrichment test's budget.

    Over the endpoint's attack-free calibration windows of at least k_min units, the
    threshold is the p-th percentile (p the first --percentiles value) of the window's
    largest z, so either scope names a filter in at most (100 - p)% of them, as the
    test's level is set; never below 3, the uncalibrated threshold. ``hist_of`` maps
    a calibration window to the history its historical z-score is taken against
    (default: that of all of ``cal``, which the test windows are scored against).
    """
    el = [r for r in cal if r["n"] >= args.k_min and r["clean"].sum() > 0]
    out = history(cal, args.k_min)
    hist_of = hist_of or (lambda r: out)
    zmax, hmax = [], []
    for r in el:
        c = r["clean"][r["clean"] > 0]
        n, P = float(c.sum()), prof(r)
        b = P.reindex(c.index).fillna(0.0).to_numpy() + 1.0 / max(P.attrs["n"], 1)
        zmax.append(float(((c.to_numpy(dtype=float) - n * b)
                           / np.sqrt(n * b * (1 - np.minimum(b, 0.999999)))).max()))
        hmax.append(float(history_z(c, hist_of(r)).max()))
    p = args.percentiles[0]
    out["zcal"] = max(3.0, float(np.percentile(zmax, p, method="higher")))
    out["zhist"] = max(3.0, float(np.percentile(hmax, p, method="higher")))
    return out


def botnet(A, stacks, args, rng):
    """A attacker sessions per fingerprint, and the same-/24 pairs among them."""
    on = rng.random(A) < args.ja4_share
    stack = np.bincount(rng.integers(0, len(stacks), on.sum()), minlength=len(stacks))
    bot = pd.concat([pd.Series(stack, index=stacks),
                     pd.Series(1, index=[f"bot_unique_{i}" for i in range((~on).sum())])])
    return bot[bot > 0], c2(np.bincount(rng.integers(0, args.prefix_pool, A)))


def stacks_for(source, M, profile, rng):
    if source == "fresh":
        return [f"bot_stack_{k:03d}" for k in range(M)]
    if source == "adversarial":
        return list(profile.index[:M]) if len(profile) >= M else None
    tail = profile.index[10:]
    return list(rng.choice(tail, M, replace=False)) if len(tail) >= M else None


def self_check(samples, args):
    """The count-based scope against derive_scope_enriched on expanded windows.

    derive_scope_enriched implements the binomial only, so the check is skipped
    under --overdispersion.
    """
    if args.overdispersion:
        return {"windows": 0, "mismatches": 0, "skipped": "overdispersion"}
    bad = 0
    for total, n_nontls, profile, alpha, named, fleets in samples:
        ja4 = np.repeat(total.index.to_numpy(dtype=object), total.to_numpy().astype(int))
        df = pd.DataFrame({"ja4": np.concatenate([ja4, np.full(n_nontls, None, dtype=object)])})
        df["dst_ip_first"], df["dst_port_first"], df["src_ip_first"] = "198.51.100.1", 443, "192.0.2.1"
        ref = derive_scope_enriched(df, profile, min_enrichment=args.rho, min_support=0.0,
                                    max_values=256, significance=alpha)
        bad += set(ref.get("tlsJa4", set())) - set(fleets) != named
    return {"windows": len(samples), "mismatches": bad}


def dispersion(cal, profile, k_min, lo=0, hi=20):
    """Pearson dispersion of the profile's fingerprints of rank lo..hi across windows.

    Under the binomial model the test assumes, a fingerprint of prevalence b seen
    c times among a window's n TLS sessions has E[c] = nb and Var[c] = nb(1 - b),
    so the mean of (c - nb)^2 / nb(1 - b) over windows is about 1. Connections
    that arrive in bursts from one client inflate it.
    """
    fps = profile.index[lo:hi]
    if not len(fps):
        return None
    cal = [r for r in cal if r["n"] >= k_min and r["clean"].sum() > 0]
    n = np.array([r["clean"].sum() for r in cal], dtype=float)[:, None]
    c = np.array([r["clean"].reindex(fps).fillna(0).to_numpy(dtype=float) for r in cal])
    b = profile[fps].to_numpy()
    phi = ((c - n * b) ** 2 / (n * b * (1 - b))).mean(axis=0)
    return {"fingerprints": int(len(fps)), "median": float(np.median(phi)),
            "min": float(phi.min()), "max": float(phi.max())}


def intra_window_correlation(cal, profile, k_min, cap=0.99):
    """Moment estimate of each profile fingerprint's intra-window correlation phi.

    Under a beta-binomial with mean b and correlation phi, a fingerprint's count
    among a window's n units has Var[c] = n b (1 - b) (1 + (n - 1) phi). Over the
    calibration windows of at least k_min units,
        phi = sum[(c - n b)^2 - n b (1 - b)] / sum[n (n - 1) b (1 - b)],
    clipped to [0, cap]. A fleet of clients that switch on together gets a large
    phi; a fingerprint absent from the profile gets none (the binomial).
    """
    el = [r for r in cal if r["n"] >= k_min and r["clean"].sum() > 0]
    if not el:
        return pd.Series(0.0, index=profile.index)
    n = np.array([r["clean"].sum() for r in el], dtype=float)[:, None]
    c = np.array([r["clean"].reindex(profile.index).fillna(0).to_numpy(dtype=float) for r in el])
    b = profile.to_numpy(dtype=float)[None, :]
    num = ((c - n * b) ** 2 - n * b * (1 - b)).sum(axis=0)
    den = (n * (n - 1) * b * (1 - b)).sum(axis=0)
    phi = np.clip(np.divide(num, den, out=np.zeros_like(num), where=den > 0), 0.0, cap)
    return pd.Series(phi, index=profile.index)


def summarize(d, k_min):
    """Fire rates of the three rules, and coverage and collateral where they fire.

    Every scope is also reported under a second trigger, ``origins``: the number of
    distinct origins at or above its 99th percentile over the calibration windows,
    in place of Omega >= tau.
    """
    d = d[d["size"] >= k_min]
    om = d["omega"] >= d["tau"]
    fires = {"omega": om, "pipeline": om & d["scope_named"], "enrichment": d["scope_named"]}
    out = {"windows": int(len(d)), "median_size": float(d["size"].median()) if len(d) else None}
    for rule, f in fires.items():
        out[rule] = float(f.mean()) if len(d) else None
        if rule == "omega":
            continue
        x = d[f]
        # Share of the attackers the rule stops, averaged over all windows (0 where
        # it does not fire): a firing that names only legitimate fleets counts 0.
        out[f"blocked_{rule}"] = float((d["scope_recall"] * f).mean()) if len(d) else None
        out[f"coverage_{rule}"] = float(x["scope_recall"].median()) if len(x) else None
        out[f"collateral_{rule}_median"] = float(x["scope_collateral"].median()) if len(x) else None
        out[f"collateral_{rule}_max"] = float(x["scope_collateral"].max()) if len(x) else None
    for base in ("zscore", "unseen", "union", "zcal", "zhist"):
        if f"{base}_named" not in d:
            continue
        f = om & d[f"{base}_named"].astype(bool)
        x = d[f]
        out[f"{base}_pipeline"] = float(f.mean()) if len(d) else None
        out[f"{base}_blocked"] = float((d[f"{base}_recall"] * f).mean()) if len(d) else None
        out[f"{base}_collateral_median"] = float(x[f"{base}_collateral"].median()) if len(x) else None
        out[f"{base}_collateral_max"] = float(x[f"{base}_collateral"].max()) if len(x) else None
    if "tau_origins" in d:
        org = d["size"] >= d["tau_origins"]
        out["origins"] = float(org.mean()) if len(d) else None
        for base, col in (("enrichment", "scope"), ("zscore", "zscore"), ("unseen", "unseen"),
                          ("union", "union"), ("zcal", "zcal"), ("zhist", "zhist")):
            if f"{col}_named" not in d:
                continue
            f = org & d[f"{col}_named"].astype(bool)
            x = d[f]
            out[f"origins_{base}_pipeline"] = float(f.mean()) if len(d) else None
            out[f"origins_{base}_blocked"] = float((d[f"{col}_recall"] * f).mean()) if len(d) else None
            out[f"origins_{base}_collateral_median"] = (float(x[f"{col}_collateral"].median())
                                                        if len(x) else None)
    return out


def prepare_hosts(recs, part, args):
    """Profile, flash-crowd pool and /24 pair rate per host, for one calibration/test split."""
    hosts, excluded = {}, {}
    for host in sorted({r["host"] for r in recs}):
        cal = [r for r in recs if r["host"] == host and part(r["window"]) == "calib"]
        test = [r for r in recs if r["host"] == host and part(r["window"]) == "test" and r["n"] > 0]
        eligible = sum(r["n"] >= args.k_min for r in cal)
        bg = pd.concat([r["clean"] for r in cal]).groupby(level=0).sum() if cal else pd.Series(dtype=float)
        if bg.sum() == 0:
            excluded[host] = "no TLS sessions"
            continue
        if eligible < args.min_calib_windows:
            excluded[host] = f"{eligible} calibration windows with >= {args.k_min} sessions"
            continue
        if np.median([r["n"] for r in cal]) < args.k_min:
            # The rule needs |S| >= k_min: a host whose typical window is smaller
            # has no window-level decision to evaluate.
            excluded[host] = f"median calibration window below {args.k_min} units"
            continue
        if not test:
            excluded[host] = "no test windows"
            continue
        profile = (bg / bg.sum()).sort_values(ascending=False)
        profile.attrs["n"] = int(bg.sum())
        if args.overdispersion:
            profile.attrs["phi"] = intra_window_correlation(cal, profile, args.k_min)
        xprofile = xhist = None
        if args.split == "crossfit":
            # Leave one calibration day out: each is judged against a profile, and a
            # history, of the other calibration days.
            xprofile, xhist = {}, {}
            for day in sorted({r["window"].date() for r in cal}):
                rest = [r for r in cal if r["window"].date() != day]
                b = pd.concat([r["clean"] for r in rest]).groupby(level=0).sum() if rest else pd.Series(dtype=float)
                if b.sum() == 0:
                    xprofile = None
                    break
                xprofile[day] = (b / b.sum()).sort_values(ascending=False)
                xprofile[day].attrs["n"] = int(b.sum())
                if args.overdispersion:
                    xprofile[day].attrs["phi"] = intra_window_correlation(rest, xprofile[day], args.k_min)
                xhist[day] = history(rest, args.k_min)
            if xprofile is None:
                excluded[host] = "a calibration day holds all of the host's TLS traffic"
                continue
        hourly = None
        if args.profile_by_hour is not None:
            # One profile per UTC hour, from the calibration windows within
            # +-profile_by_hour hours of it: fleets that switch on at set hours
            # are then part of the normal traffic of those hours.
            hourly = {}
            for hr in range(24):
                near = [r for r in cal if min(abs(r["window"].hour - hr),
                                              24 - abs(r["window"].hour - hr)) <= args.profile_by_hour]
                b = pd.concat([r["clean"] for r in near]).groupby(level=0).sum()
                hp = (b / b.sum()).sort_values(ascending=False)
                hp.attrs["n"] = int(b.sum())
                hourly[hr] = hp
        pool = pd.concat([r["clean"] for r in test]).groupby(level=0).sum()
        pool[NO_TLS] = sum(r["n_nontls"] for r in test)
        pool = pool[pool > 0]
        hosts[host] = {"calib": cal, "test": test, "profile": profile, "hourly": hourly,
                       "xprofile": xprofile, "xhist": xhist,
                       "pool": (pool.index.to_numpy(dtype=object), (pool / pool.sum()).to_numpy()),
                       "pair_rate": (sum(r["p24"] for r in cal)
                                     / max(sum(c2([r["n"]]) for r in cal), 1.0)),
                       "median_origins": float(np.median([r["n"] for r in cal])),
                       "rng_rel": np.random.default_rng([20260925, sum(map(ord, host))]),
                       "dispersion": {"head": dispersion(cal, profile, args.k_min, 0, 20),
                                      "tail": dispersion(cal, profile, args.k_min, 20, 100)}}
    return hosts, excluded


def scope_calibration(H, prof):
    """The profile, and the history, each calibration window of the scope is judged
    against when its level, thresholds and known fleets are fitted: the test's own,
    or under --split crossfit those of the other calibration days."""
    if H.get("xprofile") is not None:
        return (lambda r: H["xprofile"][r["window"].date()]), (lambda r: H["xhist"][r["window"].date()])
    return prof, None


def evaluate_host(host, H, fold, args, rng, add):
    """Every window kind of one host in one fold: calibration, clean, WAF, flash, attack."""
    P, la = H["profile"], np.log(args.significance)
    prof = (lambda r: H["hourly"][r["window"].hour]) if H["hourly"] else (lambda r: P)
    xprof, xhist = scope_calibration(H, prof)
    fl = H["fleets"] = known_fleets(H["calib"], xprof, args)
    H["level_named_calibration"] = None
    if args.calibrate_level:
        t = [min(adjusted_p(r["clean"], xprof(r), args.rho, fl)[1], default=np.inf)
             for r in H["calib"] if r["n"] >= args.k_min]
        la = min(la, float(np.percentile(t, 100 - args.percentiles[0], method="lower")))
        H["level_named_calibration"] = float(np.mean(np.array(t) < la))
    H["log_alpha"], H["alpha"] = la, float(np.exp(la))
    a = H["alpha"]
    cb = H["baselines"] = calibrate_baselines(H["calib"], xprof, args, hist_of=xhist)
    base = {"fold": fold, "host": host, "alpha": a}
    for r in H["calib"]:
        res, total, named = judge(r["clean"], r["n"], r["p24"], prof(r), args, log_alpha=la, exclude=fl, cal=cb)
        add({"kind": "calib", **base, "window": r["window"], **res}, total, named, prof(r), r["n_nontls"])
    for r in H["test"]:
        base = {"fold": fold, "host": host, "alpha": a, "window": r["window"]}
        Pr = prof(r)
        res, total, named = judge(r["clean"], r["n"], r["p24"], Pr, args, log_alpha=la, exclude=fl, cal=cb)
        add({"kind": "clean", **base, **res, "named": ";".join(sorted(named))},
            total, named, Pr, r["n_nontls"])
        # WAF diagnostic: every session, blocked or not; P_24 still clean-only.
        res, total, named = judge(r["all"], r["n_all"], r["p24"], Pr, args, log_alpha=la, exclude=fl, cal=cb)
        hit = r["all"].index.isin(named)
        hit_u = r["all"].index.isin(named | baseline_scopes(total, Pr, args)["unseen"])
        add({"kind": "waf", **base, **res, "named": ";".join(sorted(named)),
             "waf_sessions": int(r["waf"].sum()), "matched": int(r["all"][hit].sum()),
             "matched_waf": int(r["waf"][hit].sum()),
             "matched_union": int(r["all"][hit_u].sum()),
             "matched_waf_union": int(r["waf"][hit_u].sum())}, total, named, Pr)
        for N in args.flash:
            idx, p = H["pool"]
            drawn = pd.Series(np.bincount(rng.choice(len(idx), N, p=p), minlength=len(idx)), index=idx)
            crowd = drawn.drop(NO_TLS, errors="ignore")
            legit = r["clean"].add(crowd[crowd > 0], fill_value=0)
            p24 = r["p24"] + H["pair_rate"] * (c2([r["n"] + N]) - c2([r["n"]]))
            res, total, named = judge(legit, r["n"] + N, p24, Pr, args, log_alpha=la, exclude=fl, cal=cb)
            add({"kind": "flash", **base, "flash": N, **res, "named": ";".join(sorted(named))},
                total, named, Pr, r["n_nontls"] + int(drawn.get(NO_TLS, 0)))
        for source in args.sources:
            for M in args.stacks:
                stacks = stacks_for(source, M, P, rng)
                if stacks is None:
                    continue
                for A in args.attackers:
                    bot, bot_p24 = botnet(A, stacks, args, rng)
                    res, total, named = judge(r["clean"], r["n"], r["p24"] + bot_p24, Pr, args,
                                              bot, log_alpha=la, exclude=fl, cal=cb)
                    add({"kind": "attack", **base, "source": source, "stacks": M,
                         "attackers": A, **res}, total, named, Pr, r["n_nontls"])
        # Botnets sized as a fraction of the endpoint's typical window, so a small
        # endpoint is not flooded by an absolute size (separate random stream, so
        # the absolute grid above is unchanged).
        for source in args.sources_rel:
            stacks = stacks_for(source, 25, P, H["rng_rel"])
            if stacks is None:
                continue
            for frac in args.attackers_rel:
                A = max(1, int(round(frac * H["median_origins"])))
                bot, bot_p24 = botnet(A, stacks, args, H["rng_rel"])
                res, total, named = judge(r["clean"], r["n"], r["p24"] + bot_p24, Pr, args,
                                          bot, log_alpha=la, exclude=fl, cal=cb)
                add({"kind": "attack_rel", **base, "source": source, "stacks": 25,
                     "fraction": frac, "attackers": A, **res}, total, named, Pr, r["n_nontls"])


def pct(v):
    return "    --" if v is None else f"{v * 100:6.1f}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", required=True, type=Path,
                    help="directory with one subdirectory per export, named YYYY-MM-DD for a "
                         "day or YYYY-MM-DD_YYYY-MM-DD for a range of days")
    ap.add_argument("--days", nargs="+", default=None, help="subset of days (default: all)")
    ap.add_argument("--out-dir", required=True, type=Path)
    ap.add_argument("--split", choices=["hours", "halves", "days", "rolling", "crossfit"], default="hours")
    ap.add_argument("--min-calib-days", type=int, default=3,
                    help="rolling and crossfit splits: days of history before the first test day")
    ap.add_argument("--unit", choices=["session", "origin"], default="session",
                    help="what the rule counts: connections (E1, E2) or client addresses (E3, E4)")
    ap.add_argument("--k-min", type=int, default=5)
    ap.add_argument("--percentiles", type=float, nargs="+", default=[99])
    ap.add_argument("--significance", type=float, default=0.01,
                    help="family-wise level of the binomial over-representation test")
    ap.add_argument("--rho", type=float, default=3.0, help="minimum enrichment (effect size)")
    ap.add_argument("--profile-by-hour", type=int, default=None, metavar="SPAN",
                    help="one profile per UTC hour, from calibration windows within SPAN hours "
                         "of it (default: one profile per host)")
    ap.add_argument("--fleets", type=float, default=None, metavar="SHARE",
                    help="known fleets: fingerprints the test names at the nominal level in at least "
                         "SHARE of the calibration windows leave the scope and the level's calibration")
    ap.add_argument("--overdispersion", action="store_true",
                    help="test each fingerprint of the profile against a beta-binomial whose "
                         "intra-window correlation is estimated on the calibration windows, "
                         "instead of the binomial (a fingerprint absent from the profile keeps the binomial)")
    ap.add_argument("--calibrate-level", action="store_true",
                    help="lower each host's test level until the scope names a filter in at "
                         "most (100 - p)%% of its calibration windows, p the first percentile, "
                         "as tau is calibrated (the paper's method; default: the nominal level)")
    ap.add_argument("--attackers", type=int, nargs="+", default=[25, 50, 100, 250, 1000],
                    help="attacker sessions injected per window")
    ap.add_argument("--stacks", type=int, nargs="+", default=[1, 5, 25, 100])
    ap.add_argument("--sources", nargs="+", default=["fresh", "tail", "adversarial"],
                    choices=["fresh", "tail", "adversarial"])
    ap.add_argument("--flash", type=int, nargs="+", default=[25, 50, 100, 250, 1000])
    ap.add_argument("--attackers-rel", type=float, nargs="+", default=[0.1, 0.5, 1.0],
                    help="botnet sizes as fractions of the endpoint's median calibration window")
    ap.add_argument("--sources-rel", nargs="+", default=["fresh", "tail"],
                    choices=["fresh", "tail", "adversarial"])
    ap.add_argument("--ja4-share", type=float, default=0.9,
                    help="share of attacker sessions on a stack fingerprint (generator: 0.9)")
    ap.add_argument("--prefix-pool", type=int, default=2000,
                    help="distinct /24s the botnet draws from (generator: 2000)")
    ap.add_argument("--min-calib-windows", type=int, default=50,
                    help="a host is evaluated only with this many calibration windows of >= k_min sessions")
    ap.add_argument("--waf-in-profile", action="store_true",
                    help="build the profile, the calibration and the test windows from every client, "
                         "WAF-blocked ones included (for scoring the scope against the WAF's verdicts)")
    ap.add_argument("--checks", type=int, default=60, help="windows in the scope self-check")
    ap.add_argument("--tag", default="", help="suffix for the output files")
    args = ap.parse_args()
    if args.overdispersion and args.profile_by_hour is not None:
        raise SystemExit("--overdispersion is implemented for one profile per host only")
    if args.split == "crossfit" and args.profile_by_hour is not None:
        raise SystemExit("--split crossfit is implemented for one profile per host only")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(20260924)

    days = sorted(p for p in args.data_dir.iterdir()
                  if p.is_dir() and re.fullmatch(r"\d{4}-\d{2}-\d{2}(_\d{4}-\d{2}-\d{2})?", p.name)
                  and (args.days is None or p.name in args.days))
    if not days:
        raise SystemExit(f"no day directories under {args.data_dir}")
    recs = []
    for day in days:
        recs += build_windows(*load_day(day, args.unit), waf_in_profile=args.waf_in_profile)
    dup = pd.Series([(r["host"], r["window"]) for r in recs]).duplicated()
    if dup.any():
        raise SystemExit(f"{int(dup.sum())} host-windows appear in two exports; "
                         "the directories under --data-dir must not overlap in time")
    dates = sorted({r["window"].date() for r in recs})
    if args.split in ("rolling", "crossfit"):
        if len(dates) <= args.min_calib_days:
            raise SystemExit(f"--split {args.split} needs more than {args.min_calib_days} days")
        # One fold per test day, calibrated on every earlier day: as the rule would run.
        folds = [(d.isoformat(), lambda w, d=d: "calib" if w.date() < d else
                  "test" if w.date() == d else None) for d in dates[args.min_calib_days:]]
    else:
        folds = [(args.split, lambda w: part_of(w, args.split, dates[-1]))]
    log.info("%d days, %d host-windows, split by %s (%d folds), unit %s",
             len(dates), len(recs), args.split, len(folds), args.unit)

    rows, samples, seen, fleet_of = [], [], [0], [frozenset()]
    pick = np.random.default_rng(1)          # own stream, so the check leaves results alone

    def add(row, total, named, profile, n_nontls=0):
        """Keep the row, and a uniform sample of windows for the self-check."""
        rows.append(row)
        if row["size"] < args.k_min:
            return
        seen[0] += 1
        item = (total, n_nontls, profile, row["alpha"], named, fleet_of[0])
        if len(samples) < args.checks:
            samples.append(item)
        elif (j := int(pick.integers(seen[0]))) < args.checks:
            samples[j] = item

    info, excluded = {}, {}
    for fold, part in folds:
        hosts, excluded[fold] = prepare_hosts(recs, part, args)
        for h, why in excluded[fold].items():
            log.info("fold %s: host %s excluded: %s", fold, h, why)
        for host, H in hosts.items():
            fleet_of[0] = known_fleets(H["calib"], scope_calibration(
                H, (lambda r, H=H: H["hourly"][r["window"].hour]) if H["hourly"]
                else (lambda r, H=H: H["profile"]))[0], args)
            evaluate_host(host, H, fold, args, rng, add)
        info[fold] = hosts
        log.info("fold %s evaluated (%d hosts)", fold, len(hosts))

    df = pd.DataFrame(rows)
    for col in ("flash", "stacks", "attackers"):
        if col not in df:
            continue
        df[col] = df[col].astype("Int64")
    df.to_csv(args.out_dir / f"rule_production_windows{args.tag}.csv", index=False)
    check = self_check(samples, args)
    log.info("scope self-check: %d windows, %d mismatches", check["windows"], check["mismatches"])

    cal = df[(df["kind"] == "calib") & (df["size"] >= args.k_min)]
    out = {"config": {k: (str(v) if isinstance(v, Path) else v) for k, v in vars(args).items()},
           "days": [d.name for d in days], "dates": [d.isoformat() for d in dates],
           "self_check": check, "excluded_hosts": excluded, "folds": {}, "hosts": {},
           "by_percentile": {}}
    for fold, hosts in info.items():
        for host, H in hosts.items():
            c = cal[(cal["fold"] == fold) & (cal["host"] == host)]
            t = df[(df["kind"] == "clean") & (df["fold"] == fold) & (df["host"] == host)]
            out["folds"].setdefault(fold, {})[host] = {
                "calibration_windows": int(len(c)), "test_windows": int(len(t)),
                "profile_sessions": H["profile"].attrs["n"],
                "profile_fingerprints": int(len(H["profile"])),
                "top1_share": float(H["profile"].iloc[0]), "pair_rate": H["pair_rate"],
                "dispersion": H["dispersion"], "scope_level": H["alpha"],
                "scope_log10_level": H["log_alpha"] / np.log(10),
                "fleets": len(H["fleets"]),
                "phi_head_median": (float(H["profile"].attrs["phi"].iloc[:20].median())
                                    if "phi" in H["profile"].attrs else None),
                "phi_fleets_median": (float(H["profile"].attrs["phi"].reindex(list(H["fleets"])).median())
                                      if "phi" in H["profile"].attrs and H["fleets"] else None),
                "fleet_share": float(H["profile"].reindex(list(H["fleets"])).fillna(0).sum()),
                "scope_named_calibration": float(c["scope_named"].mean()),
                "level_named_calibration": H["level_named_calibration"],
                "crossfit_profile_days": len(H["xprofile"]) if H["xprofile"] is not None else None,
                "median_origins": H["median_origins"],
                "tail_prevalence_median": (float(H["profile"].iloc[10:].median())
                                           if len(H["profile"]) > 10 else None),
                "zcal_threshold": H["baselines"]["zcal"], "zhist_threshold": H["baselines"]["zhist"],
                "tau": {str(p): float(np.percentile(c["omega"], p)) for p in args.percentiles},
                "tau_origins": {str(p): float(np.percentile(c["size"], p)) for p in args.percentiles}}
    for host in sorted({h for f in out["folds"].values() for h in f}):
        v = [f[host] for f in out["folds"].values() if host in f]
        t = df[(df["kind"] == "clean") & (df["host"] == host)]
        med = lambda key: float(np.median([x[key] for x in v]))
        out["hosts"][host] = {
            "folds": len(v), "calibration_windows": sum(x["calibration_windows"] for x in v),
            "test_windows": sum(x["test_windows"] for x in v),
            "median_test_size": float(t["size"].median()),
            "profile_sessions": med("profile_sessions"), "profile_fingerprints": med("profile_fingerprints"),
            "top1_share": med("top1_share"), "scope_level": med("scope_level"),
            "dispersion_head": float(np.median([x["dispersion"]["head"]["median"] for x in v])),
            "dispersion_tail": float(np.median([x["dispersion"]["tail"]["median"] for x in v
                                                if x["dispersion"]["tail"]] or [np.nan])),
            "scope_named_calibration": float(cal.loc[cal["host"] == host, "scope_named"].mean()),
            "tau": {str(p): float(np.median([x["tau"][str(p)] for x in v])) for p in args.percentiles}}
    hosts = out["hosts"]

    for p in args.percentiles:
        taus = {(f, h): v["tau"][str(p)] for f, fh in out["folds"].items() for h, v in fh.items()}
        tors = {(f, h): v["tau_origins"][str(p)] for f, fh in out["folds"].items() for h, v in fh.items()}
        keys = list(zip(df["fold"], df["host"]))
        d = df.assign(tau=[taus[k] for k in keys], tau_origins=[tors[k] for k in keys])
        res = {"clean": {}, "flash": {}, "attack": {}, "waf": {}}
        for h in [*hosts, "all"]:
            dh = d if h == "all" else d[d["host"] == h]
            res["clean"][h] = summarize(dh[dh["kind"] == "clean"], args.k_min)
            w = dh[(dh["kind"] == "waf") & (dh["size"] >= args.k_min)]
            m = w[w["scope_named"]]
            res["waf"][h] = {
                "windows": int(len(w)), "windows_with_waf": int((w["waf_sessions"] > 0).sum()),
                "omega": float((w["omega"] >= w["tau"]).mean()) if len(w) else None,
                "enrichment": float(w["scope_named"].mean()) if len(w) else None,
                "matched_sessions": int(m["matched"].sum()),
                "matched_waf_share": float(m["matched_waf"].sum() / m["matched"].sum())
                if m["matched"].sum() else None,
                "waf_covered_share": float(m["matched_waf"].sum() / w["waf_sessions"].sum())
                if w["waf_sessions"].sum() else None}
            if "matched_union" in w:
                mu_ = w[w["union_named"].astype(bool)]
                res["waf"][h].update({
                    "union": float(w["union_named"].astype(bool).mean()) if len(w) else None,
                    "union_matched_waf_share": (float(mu_["matched_waf_union"].sum() / mu_["matched_union"].sum())
                                                if mu_["matched_union"].sum() else None),
                    "union_waf_covered_share": (float(mu_["matched_waf_union"].sum() / w["waf_sessions"].sum())
                                                if w["waf_sessions"].sum() else None)})
            for N, g in dh[dh["kind"] == "flash"].groupby("flash"):
                res["flash"].setdefault(str(N), {})[h] = summarize(g, args.k_min)
            for (s, M, A), g in dh[dh["kind"] == "attack"].groupby(["source", "stacks", "attackers"]):
                res["attack"].setdefault(f"{s}:M{M}:A{A}", {})[h] = summarize(g, args.k_min)
            for (s, fr), g in dh[dh["kind"] == "attack_rel"].groupby(["source", "fraction"]):
                res.setdefault("attack_rel", {}).setdefault(f"{s}:M25:x{fr:g}", {})[h] = summarize(g, args.k_min)
        out["by_percentile"][str(p)] = res
    (args.out_dir / f"rule_production{args.tag}.json").write_text(json.dumps(out, indent=2))

    p = str(args.percentiles[0])
    res = out["by_percentile"][p]
    print("\n" + "=" * 100)
    print(f"RULE PER 5-MIN WINDOW ON PRODUCTION TRAFFIC ({out['dates'][0]} to {out['dates'][-1]}, split by "
          f"{args.split}, unit {args.unit}), tau = p{p} per host. Rates in %.")
    print("=" * 100)
    print(f"\nper host, medians over {len(out['folds'])} fold(s)")
    print(f"{'host':<24}{'calib':>6}{'test':>6}{'med|S|':>8}{'profile':>9}{'fps':>5}{'phi.h':>7}"
          f"{'phi.t':>7}{'tau':>12}{'level':>9}{'calib:enr':>10}{'clean:Omega':>12}{'pipe':>7}{'enrich':>7}")
    for h, v in out["hosts"].items():
        c = res["clean"][h]
        print(f"{h:<24}{v['calibration_windows']:>6}{v['test_windows']:>6}{v['median_test_size']:>8.0f}"
              f"{v['profile_sessions']:>9.0f}{v['profile_fingerprints']:>5.0f}"
              f"{v['dispersion_head']:>7.1f}{v['dispersion_tail']:>7.1f}"
              f"{v['tau'][p]:>12.0f}{v['scope_level']:>9.1e}"
              f"{pct(v['scope_named_calibration']):>10}"
              f"{pct(c['omega']):>12}{pct(c['pipeline']):>7}{pct(c['enrichment']):>7}")
    for key in [k for k in res["attack"] if k.startswith("fresh:M25:")]:
        print(f"\nattack {key:<18}{'n':>5}{'Omega':>7}{'pipe':>7}{'enrich':>7}{'cov.p':>7}{'cov.e':>7}{'coll.max':>9}")
        for h, r in res["attack"][key].items():
            print(f"  {h:<23}{r['windows']:>5}{pct(r['omega']):>7}{pct(r['pipeline']):>7}"
                  f"{pct(r['enrichment']):>7}{pct(r['coverage_pipeline']):>7}"
                  f"{pct(r['coverage_enrichment']):>7}{pct(r['collateral_enrichment_max']):>9}")
    print(f"\nall hosts, attack grid{'':<3}{'n':>5}{'Omega':>7}{'pipe':>7}{'enrich':>7}{'cov.e':>7}"
          f"{'coll.med':>9}{'coll.max':>9}")
    for key, v in res["attack"].items():
        r = v["all"]
        print(f"  {key:<23}{r['windows']:>5}{pct(r['omega']):>7}{pct(r['pipeline']):>7}"
              f"{pct(r['enrichment']):>7}{pct(r['coverage_enrichment']):>7}"
              f"{pct(r['collateral_enrichment_median']):>9}{pct(r['collateral_enrichment_max']):>9}")
    print(f"\nflash crowd{'':<21}{'n':>5}{'Omega':>7}{'pipe':>7}{'enrich':>7}{'coll.med':>9}{'coll.max':>9}")
    for N, v in res["flash"].items():
        for h, r in v.items():
            print(f"  N={N:<5}{h:<24}{r['windows']:>5}{pct(r['omega']):>7}{pct(r['pipeline']):>7}"
                  f"{pct(r['enrichment']):>7}{pct(r['collateral_enrichment_median']):>9}"
                  f"{pct(r['collateral_enrichment_max']):>9}")
    print(f"\nWAF diagnostic (all sessions)  {'n':>5}{'w/WAF':>6}{'Omega':>7}{'enrich':>7}"
          f"{'matched':>9}{'WAF share':>10}{'WAF cov.':>9}")
    for h, r in res["waf"].items():
        print(f"  {h:<29}{r['windows']:>5}{r['windows_with_waf']:>6}{pct(r['omega']):>7}"
              f"{pct(r['enrichment']):>7}{r['matched_sessions']:>9}{pct(r['matched_waf_share']):>10}"
              f"{pct(r['waf_covered_share']):>9}")
    print(f"\nscope self-check: {check['windows']} windows, {check['mismatches']} mismatches")
    print(f"OK: {args.out_dir}/rule_production{args.tag}.json")
    if check["mismatches"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
