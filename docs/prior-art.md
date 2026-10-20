# Positioning

How the NOMS paper in [`papers/http-session-noms`](../papers/http-session-noms/) places itself
against related work and against the exchange standards it examined, and the framing rules that
follow. The definitions are in [`concepts.md`](concepts.md), and the results in prose in
[`experiments/FINDINGS.md`](../experiments/FINDINGS.md).

**Pointers.** "II" or "App. C" is a section of the paper and "Table I" one of its tables. Keys in
backticks are entries of [`references.bib`](../papers/http-session-noms/references.bib). "§26" is a
numbered section of the lab notebook,
[`experiments/sprint-6-noms/README.md`](../experiments/sprint-6-noms/README.md), and result files
are in [`experiments/sprint-6-noms/results/`](../experiments/sprint-6-noms/results/).

---

## The open question

Existing detectors at most flag an attack, leaving the choice of whom to block open (I).
Mitigations that do choose a filter work on packet headers or source prefixes, and the standard
mitigation channels filter on the same fields (I). The paper's question is therefore narrow: when
a TLS-fingerprint filter can stop an attack without excessive collateral, and when it cannot (I).
Its answer is conditional. Calibrated scoping provides selective mitigation when attack
fingerprints are rare among legitimate clients, botnets pass the calibration floor, and the trigger
fires (VII).

## Table I in prose

Table I compares approaches by what the filter matches, how it is chosen and what it costs
legitimate users.

**Header aggregates and prefixes.** Aggregate rate control groups traffic by packet-header fields
and rate-limits each group, chosen by congestion or an aggregate score. Legitimate traffic in the
aggregate is rate-limited with it (`mahajan2002pushback`, `alcoz2022accturbo`). Blackholing drops
the traffic to an attacked destination prefix, chosen by the attacked network, and finer
header-based rules reduce the traffic lost (`dietzel2018stellar`). Source-based filtering selects
source prefixes under a filter budget, balancing attack coverage against the legitimate traffic of
those prefixes (`soldo2012filtering`). These approaches show how filter granularity affects
collateral, but none selects clients by TLS fingerprint (II).

**Over-representation, for diagnosis or signatures.** Anomaly extraction isolates flow feature
values over-represented in anomalous traffic, and it stops at diagnosis
(`silveira2010urca`, `brauckhoff2009extraction`). Signature generation chooses payload tokens by
their coverage against a pool of normal traffic, at the cost of false positives on that traffic
(`li2006hamsa`). The paper's test asks the same question of TLS fingerprints, relative to each
endpoint's normal traffic (II).

**Costs on every client.** Client puzzles make every client under attack pay a puzzle
(`kandula2005botz`). DDoS-Shield schedules requests by their deviation from normal workloads
(`ranjan2009ddosshield`). Both impose costs on legitimate users without selecting fingerprint
filters (II).

**Signaling channels.** The IETF DOTS data channel and BGP Flow Specification carry filters on
network and transport fields, chosen by the requesting party, at the cost of whatever filter they
carry (`dots2020data`, `rfc8955flowspec`). Their core rules cannot express JA4 (II, and the
standards below).

**Detectors.** Application-layer detectors use traffic profiles and session features
(`tripathi2021application`): PCA over flow statistics (`fernandes2015autonomous`), behavioral
representations of sessions (`bharathi2012pca`) and learned models (`kemp2023approach`).
Graph-based detection classifies nodes in graphs built from network logs (`belcastro2025klage`,
KLAGE). These approaches stop at a verdict and report detection FPR only. A verdict does not say
which fingerprint filter to apply or how many legitimate clients it would block (II). Other work
separates flash crowds from attacks by request patterns across a website (`xie2009monitoring`).

**Knowledge graphs and fingerprints.** Security knowledge graphs represent threats and
countermeasures, D3FEND's OWL-based model among them (`kaloroumakis2021d3fend`), and their
operational use remains unclear (`liu2022recent`). Passive TLS fingerprinting identifies client
software from its handshake (`husak2016https`), although applications built on one library often
share a fingerprint (`anderson2019tls`). Most bots that claim a browser identity expose TLS and
header fingerprints of another tool (II, `li2021goodbot`).

**Fingerprint-based bot management.** One bot-management platform already aggregates JA4 signals
across requests (`martinetti2024ja4signals`). Its published description specifies no calibrated
filter selection or collateral metric, so Table I lists both as undisclosed (II).

**This work.** The filter matches TLS fingerprints (JA4). It is chosen by calibrated enrichment
against the endpoint's profile, and its cost to legitimate users is measured per alarm and window
(Table I). The ontology specifies the evidence and the selected scope, and the statistical test
decides which fingerprints to block (II).

## The closest work and what it leaves open

| Work | What it does | What it leaves open |
|---|---|---|
| Anomaly extraction (`silveira2010urca`, `brauckhoff2009extraction`) | Isolates flow feature values over-represented in anomalous traffic | A filter, its cost to legitimate users, and TLS fingerprints |
| Signature generation (`li2006hamsa`) | Checks candidate payload signatures against normal traffic | Fingerprints, and a calibration per endpoint |
| Source-based filtering (`soldo2012filtering`) | Trades attack coverage against legitimate traffic under a filter budget | Selection by client software |
| JA4 bot management (`martinetti2024ja4signals`) | Aggregates JA4 signals across requests | A published, calibrated filter selection and a collateral metric |
| KLAGE (`belcastro2025klage`) | Classifies the nodes of graphs built from network logs, and explains its verdicts with a large language model | Which clients to block, and a controlled comparison (below) |

KLAGE is the closest system (IV). It models the network node (port, address, flow), and this work
models the HTTP session and counts its classes per endpoint and window. KLAGE reports F₁ = 0.841 on
CIC-IoT2023 DDoS Slowloris (App. C).

## The exchange standards examined

Section VI states what exchange loses. The standards examined do not express this JA4 filter in
their core vocabulary (I, VI). The rows come from the paper, from the ingestion runs and from the
notebook's checks at each source (§10, §21, §26).

| Standard | JA4 in its vocabulary | A filter or remediation over JA4 | Source |
|---|---|---|---|
| STIX 2.1 | No core property, so the exporter carries JA4 in an extension | No | `oasis2021stix`; VI |
| MISP, through its STIX 2.1 importer (misp-stix 2026.9.16) | A JA4 object, to which the importer does not map the extension's fingerprints | No: all 26 fingerprints are dropped, and the endpoint and the course-of-action are kept | VI, App. F; `stix_ingest.json` |
| DOTS data channel (RFC 8783) | No | Filters on network and transport fields, through the ACL model | `dots2020data`; II, VI |
| BGP Flowspec (RFC 8955) | No | Filters on network and transport fields | `rfc8955flowspec`; II |
| MUD TLS and DTLS profiles (RFC 9761, 2025), an extension of the ACL model | Matches TLS client parameters | Defines no fingerprint match, and DOTS reuses the ACL model without this extension | `ietf2025mudtls`; VI |
| OCSF | A JA4 fingerprint object in network events (1.3.0, August 2024) and in finding evidence (1.4.0, January 2025) | No: its remediation classes carry D3FEND countermeasures and nothing over JA4 | `ocsf2025schema`; VI; §26 |

The reference TAXII 2.1 server (medallion 3.0.0) transports the bundles unchanged, except for the
extension definition it fails to serve (App. F, §10). A consumer fed by the MISP event sees only the
endpoint, so it would widen a fingerprint scope to the whole endpoint (§10). Exchanging fingerprint
rules would therefore need a JA4 match in DOTS filters and a JA4 property in STIX (VI).

What the ontology adds is narrower. It is the deployable specification of the evidence and the
selected scope, compiled into log-store queries. Those queries reproduced the evaluated exports'
address and /24-pair counts, and the JA4 pair counts on the endpoint where the WAF blocked no client
(VI, App. F). The ontology does not improve detection accuracy or trigger sensitivity (VI).

## Framing rules in force

1. **Claim no "first".** KLAGE precedes this work on graphs built from network logs, and a
   bot-management platform already aggregates JA4 signals across requests. The paper's claim is the
   open question above and the conditions of its answer.
2. **Name what was examined, and check each "no standard" or "no published" claim at its source.**
   An earlier draft said that no exchange standard has a JA4 property. OCSF's CHANGELOG and schema
   showed otherwise, so the paper now says "of the standards examined" and names them (§26). The
   same check applies to "No published measurement shows how botnets are distributed across TLS
   stacks" (IV-A) and to "We found no independent capture of the stealthy regime" (App. C).
3. **The ontology is a specification.** It specifies the evidence and the selected scope, and the
   log-store query compiles from it (III-E). No reasoner runs in the evaluation (III-E), and the
   statistical test decides which fingerprints to block (II). The ontology adds nothing to detection
   accuracy or trigger sensitivity (VI).
4. **The KLAGE comparison is uncontrolled.** On CIC-IoT2023 DDoS Slowloris, three flow attributes
   plus cross-session evidence reach F₁ = 0.911, versus KLAGE's published 0.841. A strong
   per-session baseline on nine flow attributes also exceeds it, at 0.900, so the margin cannot be
   credited to the cross-session representation. A controlled rerun is impossible: the released
   code starts from a graph of unpublished construction and provides no weights (App. C;
   [`METHODOLOGY.md`](../experiments/METHODOLOGY.md), Sprint 5).
5. **The collateral metric is a measurement and is not claimed as a contribution.** Prior work
   reports the cost of its own filters (Table I, last column). The paper measures it for its own
   scope, per alarm and window.
6. **Every result keeps its status and its regime.** Post hoc analyses say so (Tables II and
   IV–VII mark them). Claims about when something was fixed are checked against git. The held-out
   day's protocol was committed 17 hours after its stated time, so no external timestamp attests its
   order, and the paper says so (App. F). The generator isolates the selection mechanism under
   mimicry imposed by design. Production traffic measures false alarms on real clients, and attack
   coverage only for injected botnets with a fixed 25-stack structure (VI).

## History

This file began in May 2026 as a novelty sweep for the session-centric framing of the earlier
manuscript, [`papers/http-session/`](../papers/http-session/), and was revised after reading KLAGE
in full. Its verdicts claimed the HTTP session as a first-class OWL entity, a verdict that is its own
derivation, a mitigation scope derived from the evidence chain and a collateral metric as
contributions. The NOMS paper claims none of these. Its contributions are profile-relative scoping,
its calibration and floor, and the ontology as a specification, and it cites close work the sweep
did not list: anomaly extraction, signature generation, source-based filtering and JA4 bot
management. The sweep's vendor claims had no sources and were dropped. The sweep is in git:
`git show a057319:docs/prior-art.md`.
