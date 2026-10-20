# Reference catalog

What each reference of the NOMS 2027 paper supports, and a small pool of verified candidates. The
paper is [`papers/http-session-noms/article.tex`](../papers/http-session-noms/article.tex), round 75.

## 0. How this file relates to references.bib

- [`papers/http-session-noms/references.bib`](../papers/http-session-noms/references.bib) is the
  file BibTeX reads. It holds 38 entries: the 37 the paper cites, and `lakhina2005mining`, which
  only the Portuguese translation cites.
- The translation, in `papers/http-session-noms-pt/`, follows round 74 and keeps an identical copy
  of the file. Round 74 cited `lakhina2005mining` in Section II: "feature distributions detect and
  classify traffic anomalies". Round 75 dropped that sentence and added `tripathi2021application`
  to the same section.
- [`shared/references.bib`](../shared/references.bib) is the master of the superseded manuscript
  (`papers/http-session/`), which `scripts/sync-bib.sh` copies. It does not feed the NOMS paper.
- This file feeds nothing. Section 1 records the claim each cited entry supports, in the paper's
  current wording, so that a rewrite can be checked against it. Section 2 is a pool of uncited
  works, each verified by its DOI or a stable page. Section 3 lists what the rebuild of 2026-10-20
  dropped, and why.
- A reference earns its place only through a specific claim. Before citing a candidate, read it and
  copy its verified data into `references.bib`.

## 1. Entries the paper cites, by argument

Each entry appears once, in the group of its main argument. The role quotes or closely follows the
sentence that cites it. "Table I" is the comparison with related work printed with Section II.

### 1.1 Motivation

| Key | Reference | Role in the paper | Section |
|---|---|---|---|
| `google2023rapidreset` | Snellman, Iamartino 2023, *How It Works: The Novel HTTP/2 'Rapid Reset' DDoS Attack*, Google Cloud Blog | High-volume attacks such as HTTP/2 Rapid Reset (CVE-2023-44487) "have reached peaks of 398 million requests per second", the contrast to the low-rate attacks the paper studies. | I |
| `cambiaso2013slowdos` | Cambiaso et al. 2013, *Slow DoS Attacks: Definition and Categorisation*, Int. J. Trust Management in Computing and Communications | Distributed Slow HTTP DoS can exhaust a server "without high per-source rates". | I |
| `odusami2020survey` | Odusami et al. 2020, *A Survey and Meta-Analysis of Application-Layer Distributed Denial-of-Service Attack*, Int. J. Communication Systems | "A survey of 75 application-layer DDoS studies found that 47% use request-stream and packet-pattern features." | I |

Section I also cites `sharafaldin2018cicids` (1.7), `kemp2023approach` (1.3), `belcastro2025klage`
(1.4) and five entries of 1.2.

### 1.2 Scoping a mitigation

| Key | Reference | Role in the paper | Section |
|---|---|---|---|
| `mahajan2002pushback` | Mahajan et al. 2002, *Controlling High Bandwidth Aggregates in the Network*, ACM SIGCOMM CCR | Aggregate-based defenses "group traffic by packet-header fields and rate-limit each group". In Section I, aggregate-based mitigations "use network and transport headers". | I, II, Table I |
| `alcoz2022accturbo` | Alcoz et al. 2022, *Aggregate-Based Congestion Control for Pulse-Wave DDoS Defense*, ACM SIGCOMM | Cited with `mahajan2002pushback` for the same claims. | I, II, Table I |
| `dietzel2018stellar` | Dietzel et al. 2018, *Stellar: Network Attack Mitigation Using Advanced Blackholing*, ACM CoNEXT | "Blackholing drops all traffic to attacked destinations, with finer header-based rules reducing the affected traffic." | II, Table I |
| `soldo2012filtering` | Soldo et al. 2012, *Optimal Source-Based Filtering of Malicious Traffic*, IEEE/ACM Trans. Networking | "Source-based filtering selects prefixes under a filter budget, balancing attack coverage against legitimate traffic." | I, II, Table I |
| `silveira2010urca` | Silveira, Diot 2010, *URCA: Pulling out Anomalies by their Root Causes*, IEEE INFOCOM | "Closer to our method, anomaly extraction isolates feature values over-represented in abnormal traffic." In Table I its cost to legitimate users is "None (diagnosis only)". | II, Table I |
| `brauckhoff2009extraction` | Brauckhoff et al. 2009, *Anomaly Extraction in Backbone Networks Using Association Rules*, ACM IMC | Cited with `silveira2010urca` for the same claims. | II, Table I |
| `li2006hamsa` | Li et al. 2006, *Hamsa: Fast Signature Generation for Zero-day Polymorphic Worms with Provable Attack Resilience*, IEEE S&P | "Signature generation checks candidate signatures against normal traffic." | II, Table I |
| `kandula2005botz` | Kandula et al. 2005, *Botz-4-Sale: Surviving Organized DDoS Attacks That Mimic Flash Crowds*, USENIX NSDI | Client puzzles impose "costs on legitimate users without selecting fingerprint filters". | II, Table I |
| `ranjan2009ddosshield` | Ranjan et al. 2009, *DDoS-Shield: DDoS-Resilient Scheduling to Counter Application Layer Attacks*, IEEE/ACM Trans. Networking | Defenses that "schedule requests by their deviation from normal workloads", with the same cost to legitimate users. | II |
| `dots2020data` | Boucadair, Reddy.K 2020, *DOTS Data Channel Specification*, RFC 8783 | Standard mitigation channels "filter on the same fields" (I). The DOTS data channel and BGP Flowspec "carry filters on network and transport fields, and their core rules cannot express JA4" (II). DOTS reuses the ACL model "without adopting the extension" of RFC 9761 (VI). | I, II, VI, Table I |
| `rfc8955flowspec` | Loibl et al. 2020, *Dissemination of Flow Specification Rules*, RFC 8955 | Cited with `dots2020data` in Sections I and II and in Table I. | I, II, Table I |

### 1.3 Layer-7 detection

| Key | Reference | Role in the paper | Section |
|---|---|---|---|
| `tripathi2021application` | Tripathi, Hubballi 2021, *Application Layer Denial-of-Service Attacks and Defense Mechanisms: A Survey*, ACM Computing Surveys | "Application-layer DDoS detectors use traffic profiles and session features." | II |
| `fernandes2015autonomous` | Fernandes Jr. et al. 2015, *Autonomous Profile-Based Anomaly Detection System Using Principal Component Analysis and Flow Analysis*, Applied Soft Computing | "Principal Component Analysis (PCA) over flow statistics" (II). Reimplemented as the PCA-profiling baseline (App. C). | II, App. C |
| `bharathi2012pca` | Bharathi, Sukanesh 2012, *A PCA Based Framework for Detection of Application Layer DDoS Attacks*, WSEAS Trans. Information Science and Applications | "Behavioral representations of sessions" (II). Reimplemented as "PCA with k-means over a behavioral matrix" (App. C). | II, App. C, Table I |
| `kemp2023approach` | Kemp et al. 2023, *An Approach to Application-Layer DoS Detection*, Journal of Big Data | The per-session signals that detectors use, "such as connection duration and packet rate" (I). "Learned models" (II). The supervised RF/SVM baseline over session features, built after it (App. C). | I, II, App. C, Table I |
| `xie2009monitoring` | Xie, Yu 2009, *Monitoring the Application-Layer DDoS Attacks for Popular Websites*, IEEE/ACM Trans. Networking | "Other work separates flash crowds from attacks by request patterns across a website." | II |
| `jung2002flash` | Jung et al. 2002, *Flash Crowds and Denial of Service Attacks: Characterization and Implications for CDNs and Web Sites*, WWW | "Per window, Ω ≥ τ_cluster alone also fires on flash crowds." | V-A |

Section II closes this group: none of these detectors "preserves relations across sessions", and a
verdict "does not say which fingerprint filter to apply or how many legitimate clients it would
block". Table I's detectors row cites `bharathi2012pca`, `kemp2023approach` and
`belcastro2025klage`.

### 1.4 Knowledge graphs and fingerprints

| Key | Reference | Role in the paper | Section |
|---|---|---|---|
| `kaloroumakis2021d3fend` | Kaloroumakis, Smith 2021, *Toward a Knowledge Graph of Cybersecurity Countermeasures*, MITRE | "Security knowledge graphs represent threats and countermeasures, including D3FEND's OWL-based model." | II |
| `liu2022recent` | Liu et al. 2022, *Recent Progress of Using Knowledge Graph for Cybersecurity*, Electronics | "...while their operational use remains unclear." | II |
| `belcastro2025klage` | Belcastro et al. 2026, *Enhancing Network Security Using Knowledge Graphs and Large Language Models for Explainable Threat Detection*, Future Generation Computer Systems (KLAGE) | "Graph-based detectors capture relations between network nodes but stop at a verdict" (I). "KLAGE classifies nodes in graphs built from network logs" (II). Section IV and App. C compare with its published results, an uncontrolled comparison, without citing it again. | I, II, Table I |
| `husak2016https` | Husák et al. 2016, *HTTPS Traffic Analysis and Client Identification Using Passive SSL/TLS Fingerprinting*, EURASIP J. Information Security | "Passive TLS fingerprinting identifies client software from its handshake." | II |
| `anderson2019tls` | Anderson, McGrew 2019, *TLS Beyond the Browser: Combining End Host and Network Data to Understand Application Behavior*, ACM IMC | "Applications built on one library often share a fingerprint." This sharing "enables fingerprint filtering and also creates collateral risk". | II |
| `li2021goodbot` | Li et al. 2021, *Good Bot, Bad Bot: Characterizing Automated Browsing Activity*, IEEE S&P | "Most bots that claim a browser identity expose TLS and header fingerprints of another tool." | II |
| `martinetti2024ja4signals` | Martinetti 2024, *Advancing Threat Intelligence: JA4 Fingerprints and Inter-Request Signals*, Cloudflare Blog | "One bot-management platform already aggregates JA4 signals across requests", but its published description "specifies no calibrated filter selection or collateral metric". In Table I, how it chooses filters and their cost to legitimate users are "Undisclosed". | II, Table I |

### 1.5 Threat model

| Key | Reference | Role in the paper | Section |
|---|---|---|---|
| `althouse2023ja4` | Althouse 2023, *JA4+ Network Fingerprinting*, FoxIO Blog | The defender computes a JA4 fingerprint from the ClientHello, "which summarizes the TLS version, cipher suites, extensions and ALPN". | III-A |
| `antonakakis2017mirai` | Antonakakis et al. 2017, *Understanding the Mirai Botnet*, USENIX Security | "Botnets span many router, camera and DVR models", next to the assumption that a bot keeps the fingerprint of its TLS stack. | III-A |
| `frolov2019tls` | Frolov, Wustrow 2019, *The Use of TLS in Censorship Circumvention*, NDSS | "Imitating a browser's ClientHello takes a full browser or an impersonation library kept in step with browser releases", so browser-imitating bots fall outside the threat model. | III-A |

### 1.6 Standards examined

| Key | Reference | Role in the paper | Section |
|---|---|---|---|
| `oasis2021stix` | OASIS 2021, *STIX Version 2.1*, OASIS Standard | The evidence chain is also exported as STIX 2.1, "using an indicator and a course-of-action linked by mitigates". Section VI names STIX 2.1 among the standards with no JA4 property in their core vocabulary. | III-E |
| `ocsf2025schema` | OCSF Project 2025, *Open Cybersecurity Schema Framework (OCSF), Version 1.4.0*, GitHub | "OCSF records JA4 fingerprints in network events and finding evidence but defines no filter or remediation over them." | VI |
| `ietf2025mudtls` | Reddy.K et al. 2025, *Manufacturer Usage Description (MUD) for TLS and DTLS Profiles for Internet of Things (IoT) Devices*, RFC 9761 | "A 2025 extension of the ACL model supports matching TLS client parameters but does not define a fingerprint match." | VI |
| `ietf2026ech` | Rescorla et al. 2026, *TLS Encrypted Client Hello*, RFC 9849 | "Encrypted Client Hello does not prevent a defender terminating TLS from observing the inner ClientHello, as assumed here." | VI |

### 1.7 Datasets

| Key | Reference | Role in the paper | Section |
|---|---|---|---|
| `sharafaldin2018cicids` | Sharafaldin et al. 2018, *Toward Generating a New Intrusion Detection Dataset and Intrusion Traffic Characterization*, ICISSP (CICIDS2017) | Flooding tools that hold connections open, "such as HULK and GoldenEye" (I). Its Slowloris, Slowhttptest, HULK and GoldenEye captures (App. C). Section IV and App. B use its benign sessions to calibrate the generator, without citing it again. | I, App. C |
| `neto2023ciciot` | Neto et al. 2023, *CICIoT2023: A Real-Time Dataset and Benchmark for Large-Scale Attacks in IoT Environment*, Sensors | CIC-IoT2023 (DDoS Slowloris, HTTP Flood), "on which KLAGE reports F1 = 0.841 for DDoS Slowloris", the basis of the uncontrolled comparison. | App. C |
| `shafi2024bccc` | Shafi et al. 2024, *Toward Generating a New Cloud-Based Distributed Denial of Service (DDoS) Dataset and Cloud Intrusion Traffic Characterization*, Information | "We found no independent capture of the stealthy regime": BCCC-cPacket-Cloud-DDoS-2024 "criticizes the application-layer coverage of earlier datasets and provides 17 TCP-based DDoS scenarios". | App. C |

## 2. Candidate pool

Uncited works, each checked on 2026-10-20 against its DOI or a stable publisher, W3C, CEUR-WS,
USENIX, JMLR or MITRE page. The notes say what each one could support. Read the source before
citing it for a claim.

### 2.1 Security knowledge graphs and ontologies (Section II)

| Entry | Identifier | Could support |
|---|---|---|
| Hogan et al. 2021, *Knowledge Graphs*, ACM Computing Surveys 54(4), 1–37 | [10.1145/3447772](https://doi.org/10.1145/3447772) | A general definition of the term, if the paper needs one. |
| Jia et al. 2018, *A Practical Approach to Constructing a Knowledge Graph for Cybersecurity*, Engineering 4(1), 53–60 | [10.1016/j.eng.2018.01.004](https://doi.org/10.1016/j.eng.2018.01.004) | A security knowledge graph built from text, with machine-learned entity extraction into an ontology and new rules derived by path ranking. |
| Bonagiri et al. 2024, *Practical Applications of Cyber security: A Research Paper on Knowledge Graphs for Real-World Security Solutions*, ASIANCON 2024, 1–6 | [10.1109/ASIANCON62057.2024.10837769](https://doi.org/10.1109/ASIANCON62057.2024.10837769) | Knowledge graphs in security practice. Only the record was checked, so read the paper before citing it for any claim. |
| Mavroeidis, Bromander 2017, *Cyber Threat Intelligence Model: An Evaluation of Taxonomies, Sharing Standards, and Ontologies within Cyber Threat Intelligence*, EISIC 2017, 91–98 | [10.1109/EISIC.2017.20](https://doi.org/10.1109/EISIC.2017.20) | A review of threat-intelligence taxonomies, sharing standards and ontologies, next to the exchange gap of Section VI. |
| Pingle et al. 2019, *RelExt: Relation Extraction Using Deep Learning Approaches for Cybersecurity Knowledge Graph Improvement*, IEEE/ACM ASONAM 2019, 879–886 | [10.1145/3341161.3343519](https://doi.org/10.1145/3341161.3343519) | Security knowledge graphs populated from text. |
| Iannacone et al. 2015, *Developing an Ontology for Cyber Security Knowledge Graphs*, CISR 2015, 1–4 | [10.1145/2746266.2746278](https://doi.org/10.1145/2746266.2746278) | An earlier ontology for security knowledge graphs. |
| Syed et al. 2016, *UCO: A Unified Cybersecurity Ontology*, AAAI Workshop on Artificial Intelligence for Cyber Security | [AAAI PDF](https://cdn.aaai.org/ocs/ws/ws0163/12574-57427-1-PB.pdf) | An ontology that integrates security schemas and sharing standards and maps them to general ontologies. |
| Obrst et al. 2012, *Developing an Ontology of the Cyber Security Domain*, STIDS 2012, 49–56 | [CEUR-WS Vol-966](https://ceur-ws.org/Vol-966/) | An ontology architecture for the cyber-security domain. |
| Pinkston et al. 2003, *A Target-Centric Ontology for Intrusion Detection*, IJCAI-03 Workshop on Ontologies and Distributed Systems | [CEUR-WS Vol-71](https://ceur-ws.org/Vol-71/) | An early intrusion-detection ontology, organized around what an attack targets. |

### 2.2 Application-layer DDoS and botnets (Sections I, II and III-A)

| Entry | Identifier | Could support |
|---|---|---|
| Sreeram, Vuppala 2019, *HTTP Flood Attack Detection in Application Layer Using Machine Learning Metrics and Bio Inspired Bat Algorithm*, Applied Computing and Informatics 15(1), 59–66 | [10.1016/j.aci.2017.10.003](https://doi.org/10.1016/j.aci.2017.10.003) | A learned HTTP-flood detector, next to the detectors of Section II. |
| Hoque et al. 2015, *Botnet in DDoS Attacks: Trends and Challenges*, IEEE Communications Surveys & Tutorials 17(4), 2242–2270 | [10.1109/COMST.2015.2457491](https://doi.org/10.1109/COMST.2015.2457491) | A survey of botnets in DDoS attacks, next to `antonakakis2017mirai`. |
| Pa Pa et al. 2015, *IoTPOT: Analysing the Rise of IoT Compromises*, USENIX WOOT 2015 | [USENIX page](https://www.usenix.org/conference/woot15/workshop-program/presentation/pa) | IoT compromises observed with a honeypot, next to `antonakakis2017mirai`. |
| Wang et al. 2014, *DDoS Attack Protection in the Era of Cloud Computing and Software-Defined Networking*, IEEE ICNP 2014, 624–629; extended in Computer Networks 81 (2015), 308–319 | [10.1109/ICNP.2014.99](https://doi.org/10.1109/ICNP.2014.99), [10.1016/j.comnet.2015.02.026](https://doi.org/10.1016/j.comnet.2015.02.026) | DDoS protection for cloud and SDN deployments. |

### 2.3 TLS and client fingerprinting (Sections II and VI)

| Entry | Identifier | Could support |
|---|---|---|
| Althouse, Atkinson, Atkins 2017, *JA3*, Salesforce | [GitHub repository](https://github.com/salesforce/ja3), archived on May 1, 2025 | The origin of the JA3 fingerprint. Its successor JA4 (`althouse2023ja4`) sorts the cipher suites and extensions before hashing. |
| Anderson, McGrew 2017, *Machine Learning for Encrypted Malware Traffic Classification: Accounting for Noisy Labels and Non-Stationarity*, ACM KDD 2017, 1723–1732 | [10.1145/3097983.3098163](https://doi.org/10.1145/3097983.3098163) | Discusses TLS handshake features in an operational setting, relevant to keeping profiles current (VI). |
| Yen et al. 2009, *Browser Fingerprinting from Coarse Traffic Summaries: Techniques and Implications*, DIMVA 2009, 157–175 | [10.1007/978-3-642-02918-9_10](https://doi.org/10.1007/978-3-642-02918-9_10) | Client identification from traffic summaries, next to `husak2016https`. |
| Vastel et al. 2018, *FP-STALKER: Tracking Browser Fingerprint Evolutions*, IEEE S&P 2018, 728–741 | [10.1109/SP.2018.00008](https://doi.org/10.1109/SP.2018.00008) | Browser fingerprints change over time, one reason profiles must stay current (VI). |

### 2.4 Ontology and query languages (Section III-E and App. D)

| Entry | Identifier | Could support |
|---|---|---|
| McGuinness, van Harmelen (eds.) 2004, *OWL Web Ontology Language Overview*, W3C Recommendation, 10 February 2004 | [W3C](https://www.w3.org/TR/owl-features/) | The ontology's language. The page points to OWL 2 as its newer version. |
| Harris, Seaborne (eds.) 2013, *SPARQL 1.1 Query Language*, W3C Recommendation, 21 March 2013 | [W3C](https://www.w3.org/TR/sparql11-query/) | The aggregation query that App. D times. |
| Horrocks et al. 2004, *SWRL: A Semantic Web Rule Language Combining OWL and RuleML*, W3C Member Submission, 21 May 2004 | [W3C](https://www.w3.org/submissions/SWRL/) | The pairwise rules of the artifact (`experiments/pillar2-symbolic-reasoning/`). The paper does not mention SWRL. |

### 2.5 Datasets (Section IV-A and App. C)

| Entry | Identifier | Could support |
|---|---|---|
| Engelen et al. 2021, *Troubleshooting an Intrusion Detection Dataset: the CICIDS2017 Case Study*, IEEE S&P Workshops 2021, 7–12 | [10.1109/SPW53761.2021.00009](https://doi.org/10.1109/SPW53761.2021.00009) | An important warning about noisy labels in CICIDS2017. Cite it whenever the paper uses the dataset as a secondary source, as the generator does with its benign sessions. |
| Sharafaldin et al. 2019, *Developing Realistic Distributed Denial of Service (DDoS) Attack Dataset and Taxonomy*, ICCST 2019, 1–8 (CIC-DDoS2019) | [10.1109/CCST.2019.8888419](https://doi.org/10.1109/CCST.2019.8888419) | A DDoS dataset of reflection- and exploitation-based attacks. Its dataset page lists one low-volume WebDDoS class, and no Slowloris, slowhttptest, HULK or GoldenEye attack. |
| Moustafa, Slay 2015, *UNSW-NB15: A Comprehensive Data Set for Network Intrusion Detection Systems*, MilCIS 2015, 1–6 | [10.1109/MilCIS.2015.7348942](https://doi.org/10.1109/MilCIS.2015.7348942) | A general intrusion-detection dataset. |

### 2.6 Statistical comparison (App. C)

App. C compares configurations with paired Wilcoxon tests, Bonferroni-corrected.

| Entry | Identifier | Could support |
|---|---|---|
| Demšar 2006, *Statistical Comparisons of Classifiers over Multiple Data Sets*, JMLR 7, 1–30 | [JMLR](https://www.jmlr.org/papers/v7/demsar06a.html) | The Wilcoxon signed-rank test for comparing two classifiers. |
| García, Herrera 2008, *An Extension on "Statistical Comparisons of Classifiers over Multiple Data Sets" for all Pairwise Comparisons*, JMLR 9, 2677–2694 | [JMLR](https://www.jmlr.org/papers/v9/garcia08a.html) | Corrections when many pairs are compared. |
| Bouckaert, Frank 2004, *Evaluating the Replicability of Significance Tests for Comparing Learning Algorithms*, PAKDD 2004, 3–12 | [10.1007/978-3-540-24775-3_3](https://doi.org/10.1007/978-3-540-24775-3_3) | How replicable the usual significance tests are across repeated runs. |

### 2.7 Threat taxonomy

| Entry | Identifier | Could support |
|---|---|---|
| MITRE ATT&CK, *Endpoint Denial of Service: Service Exhaustion Flood*, T1499.002 (tactic: Impact) | [MITRE page](https://attack.mitre.org/techniques/T1499/002/) | The ATT&CK technique for HTTP floods; its page describes a simple HTTP flood. The ontology carries no ATT&CK mapping. |

## 3. Dropped entries

The numbers refer to the catalog before this rebuild, which is in the git history.

### 3.1 Not found

A search of Crossref and the web found no record of these entries as listed. They may be
fabricated. Do not cite them.

| # | Entry as listed | What the search found |
|---|---|---|
| 6 | Gao et al. 2021, *A Systematic Survey of Knowledge Graph Construction for Cybersecurity*, IEEE Access 9 | Not found. |
| 13 | Husari et al. 2017, *Using Data Provenance to Detect Cyber Threats in SOCs*, IEEE BigData | Not found. The group's TTPDrill (ACSAC 2017) is a different work. |
| 14 | Fernandes Jr. et al. 2019, *Autonomous Profile-Based Anomaly Detection System for DDoS Attacks*, IEEE Systems Journal 13(2) | Not found. The author list matches the same group's survey in Telecommunication Systems 70(3), 447–489 ([10.1007/s11235-018-0475-8](https://doi.org/10.1007/s11235-018-0475-8)). The paper cites their 2015 work, `fernandes2015autonomous`. |
| 15 | Kumar, Selvakumar 2019, *Detection of Application Layer DDoS Attacks Using Information Theory*, Computers & Security 84 | Not found. |
| 16 | Singh, Singh 2020, *Detection of Application Layer DDoS Attacks Using Information Theoretic Entropy*, Computers & Security 97 | Not found. |
| 18 | Sahoo, Gupta 2019, *Multiple Features Based Approach for Detection of Application Layer DDoS Attacks*, IEEE ICIT | Not found. The same authors' 2021 paper with this title prefix is about fake news. |
| 19 | Vijayalakshmi, Selvakumar 2020, *Application Layer DDoS Attack Detection Using Ensemble Learning*, J. Network and Computer Applications 166 | Not found. |
| 20 | Thapa et al. 2020, *Application Layer DDoS Detection Using Machine Learning*, IEEE DASC | Not found. |
| 21 | Raj, Singh 2022, *Detection of HTTP Flood Attacks Using Deep Learning*, Computers & Security 115 | Not found. |
| 22 | Cui et al. 2021, *Application Layer DDoS Attack Detection Using Deep Neural Networks*, IEEE Access 9 | Not found. |
| 23 | Das, Sharma 2021, *Application Layer DDoS Attack Detection Using Hybrid ML Approach*, J. Information Security and Applications 61 | Not found. A 2017 paper with a similar title by other authors is in the Int. J. Security and Its Applications. |
| 24 | Bhuyan et al. 2014, *Survey on DDoS Attacks and Defense Mechanisms*, IJCSE 6(1) | Not found. |
| 26 | Xiao, Zhang 2021, *A Survey on Application Layer DDoS Attack Detection Techniques*, IEEE Access 9 | Not found. Its pages, 45678–45695, look like a placeholder. |
| 29 | Wang et al. 2018, *Credential Spraying: A Quantitative Study*, ACM AsiaCCS | Not found. |
| 31 | Zhou et al. 2020, *Low-Rate DDoS Attack Detection Using Improved Autoencoder*, Security and Communication Networks | Not found. The same authors published *Low-Rate DDoS Attack Detection Using Expectation of Packet Size* there in 2017 ([10.1155/2017/3691629](https://doi.org/10.1155/2017/3691629)). |
| 32 | Zhou, Li 2021, *Slow HTTP DoS Attack Detection Based on Network Traffic Analysis*, Security and Communication Networks | Not found. |
| 33 | Zhang, Wang 2022, *Low-Rate Application Layer DDoS Attack Detection Using Adaptive Threshold*, IEEE TIFS 17 | Not found. Its pages, 1234–1247, look like a placeholder. |
| 34 | Tellenbach et al. 2016, *Beyond the Hype: API Abuse in the Wild*, DIMVA | Not found. |

### 3.2 Real, but tied to no current argument

| # | Entry | Why dropped |
|---|---|---|
| 2–5 | Ehrlinger, Wöß 2016 (SEMANTiCS); Paulheim 2017 (Semantic Web 8(3)); Noy et al. 2019 (ACM Queue 17(2)); Hitzler et al. 2009 (CRC book) | Knowledge-graph foundations: the paper no longer argues them. Hogan et al. (2.1) cover a definition, and the W3C documents (2.4) cover OWL. |
| 28 | Thomas et al. 2019, *Protecting Accounts from Credential Stuffing with Password Breach Alerting*, USENIX Security | The paper no longer discusses credential stuffing. |
| 30 | Tian et al. 2018, *Needle in a Haystack: Tracking Down Elite Phishing Domains in the Wild*, ACM IMC | Same argument. It is about phishing domains, so it never supported credential stuffing. The old entry gave 2019. |
| 44–46 | Glimm et al. 2014 (HermiT); Sirin et al. 2007 (Pellet); Musen 2015 (Protégé) | No reasoner or ontology editor is part of the evaluation (III-E). |
| 47–51 | Ribeiro et al. 2016 (LIME); Lundberg, Lee 2017 (SHAP); Carvalho et al. 2019; Mohseni et al. 2021; Warnecke et al. 2020 | The paper no longer argues about explainability. The third author of Mohseni et al. is E. D. Ragan, which the old entry gave as M. A. Ragan. |
| 61 | OWASP Top 10 (2021) | No claim of the paper needs it, and its URL now redirects to the 2025 edition. |

### 3.3 Moved to section 1

These entries of the old catalog are now cited, so section 1 holds them: Tripathi and Hubballi
2021, Odusami et al. 2020, Kemp et al. 2023, Fernandes Jr. et al. 2015, Bharathi and Sukanesh 2012
and Liu et al. 2022 (its old core list); the JA4+ post (#40, `althouse2023ja4`); CICIDS2017 (#52,
`sharafaldin2018cicids`); and STIX 2.1 (#59, `oasis2021stix`, an OASIS Standard, which the old entry
called a Committee Specification). Two more entries of the old core list, Jia et al. 2018 and
Bonagiri et al. 2024, are not cited and moved to 2.1.
