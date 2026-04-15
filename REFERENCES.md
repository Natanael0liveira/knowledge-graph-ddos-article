# References and Resources for Knowledge Graph-Based DDoS Detection

## Academic Papers

### Knowledge Graphs - Foundational Works

1. **Ehrlinger, L., & Wöß, W. (2016).** "Towards a Definition of Knowledge Graphs." *SEMANTiCS 2016*.
   - DOI: 10.13140/RG.2.2.18223.41127
   - Key contribution: Formal definition and taxonomy of knowledge graphs

2. **Hogan, A., Blomqvist, E., Cochez, M., d'Amato, C., Melo, G. D., Gutierrez, C., ... & Zimmermann, A. (2021).** "Knowledge Graphs." *ACM Computing Surveys*, 54(4), 1-37.
   - DOI: 10.1145/3447772
   - Comprehensive survey of knowledge graph technologies

3. **Paulheim, H. (2017).** "Knowledge Graph Refinement: A Survey of Approaches and Evaluation Methods." *Semantic Web*, 8(3), 489-508.
   - DOI: 10.3233/SW-160218

### Knowledge Graphs in Cybersecurity

4. **Jia, Y., Qi, J., Shang, H., Jiang, R., & Li, A. (2018).** "A Practical Approach to Constructing a Knowledge Graph for Cybersecurity." *Engineering*, 4(4), 503-511.
   - DOI: 10.1016/j.eng.2018.07.012

5. **Noel, S., Harley, E., Tam, K. H., & Gyor, G. (2015).** "Cyber Graph Analytics for Security." *IEEE Military Communications Conference (MILCOM)*.
   - DOI: 10.1109/MILCOM.2015.7357601

6. **Husari, G., Al-Shaer, E., Ahmed, M., Khurshid, B., & Quinn, A. (2017).** "Using Data Provenance to Detect Cyber Threats in Security Operations Centers." *IEEE International Conference on Big Data*.
   - DOI: 10.1109/BigData.2017.8258337

7. **Liu, J., & Li, T. (2020).** "Knowledge Graph Construction for Cyber Security." *IEEE International Conference on Knowledge Graph (ICKG)*.
   - DOI: 10.1109/ICKG50412.2020.00021

8. **Pingle, A., Piplai, A., Ranjan, P., Mittal, S., & Joshi, A. (2019).** "Relext: Relation Extraction Using Deep Learning Approaches for Cybersecurity Knowledge Graph Improvement." *Proceedings of the 2019 IEEE/ACM International Conference on Advances in Social Networks Analysis and Mining*.

### DDoS Attack Detection

9. **Bhuyan, M. H., Bhattacharyya, D. K., & Kalita, J. K. (2014).** "Survey on DDoS Attacks and Defense Mechanisms." *International Journal of Computer Science and Engineering*, 6(1), 1-30.
   - DOI: 10.1504/IJCSE.2014.057851

10. **Moustafa, N., & Slay, J. (2019).** "UNSW-NB15: A Comprehensive Data Set for Network Intrusion Detection Systems (UNSW-NB15 Network Data Set)." *IEEE Military Communications and Information Systems Conference (MilCIS)*.
    - DOI: 10.1109/MilCIS.2019.8927807

11. **Sharafaldin, I., Lashkari, A. H., & Ghorbani, A. A. (2019).** "CIC-DDoS2019: A Comprehensive Dataset for DDoS Attack Detection." *IEEE Canadian Conference of Electrical and Computer Engineering (CCECE)*.
    - DOI: 10.1109/CCECE.2019.8861865

12. **Zhou, L., Liao, M., & Yuan, L. (2020).** "Low-Rate DDoS Attack Detection Using Improved Autoencoder." *Security and Communication Networks*.
    - DOI: 10.1155/2020/8829285

### Graph Neural Networks for Security

13. **Kipf, T. N., & Welling, M. (2017).** "Semi-Supervised Classification with Graph Convolutional Networks." *International Conference on Learning Representations (ICLR)*.
    - arXiv: 1609.02907

14. **Velickovic, P., Cucurull, G., Casanova, A., Romero, A., Lio, P., & Bengio, Y. (2018).** "Graph Attention Networks." *International Conference on Learning Representations (ICLR)*.
    - arXiv: 1710.10903

15. **Lo, W. W., Layeghy, S., Sarhan, M., Hajizadeh, M., & Portmann, M. (2022).** "Graph-based Network Intrusion Detection: A Survey." *IEEE Access*.
    - DOI: 10.1109/ACCESS.2022.3140576

### Semantic Security and Ontologies

16. **Obrst, L., Chase, P., & Markeloff, R. (2012).** "Developing an Ontology of the Cyber Security Domain." *Proceedings of the International Conference on Semantic Technologies for Intelligence, Defense, and Security (STIDS)*.

17. **Undercoffer, J., Joshi, A., Finin, T., & Pinkston, J. (2003).** "A Target-Centric Ontology for Intrusion Detection." *Proceedings of the IJCAI Workshop on Ontologies and Distributed Systems*.

18. **Syed, Z., Padia, A., & Finin, T. (2016).** "UCO: A Unified Cybersecurity Ontology." *Proceedings of the AAAI Workshop on Artificial Intelligence for Cyber Security*.

19. **Iannacone, M., Bohn, S., Nakamura, G., Gerth, J., Huffer, K., Bridges, R., ... & Goodall, J. (2015).** "Developing an Ontology for Cyber Security Knowledge Graphs." *Proceedings of the 10th Annual Cyber and Information Security Research Conference*.

---

## Standards and Frameworks

### STIX 2.1 (Structured Threat Information Expression)
- **Organization:** OASIS Cyber Threat Intelligence (CTI) TC
- **URL:** https://oasis-open.github.io/cti-documentation/stix/intro
- **Purpose:** Standardized language for sharing cyber threat intelligence
- **Key Features:**
  - Objects: Attack Pattern, Campaign, Course of Action, Identity, Indicator, Intrusion Set, Malware, Observed Data, Report, Threat Actor, Tool, Vulnerability
  - Relationships: related-to, targets, uses, indicates, etc.

### MITRE ATT&CK Framework
- **URL:** https://attack.mitre.org/
- **Purpose:** Knowledge base of adversary tactics and techniques
- **Key Features:**
  - 14 Tactics (Enterprise)
  - 193+ Techniques
  - 401+ Sub-techniques
  - Mitigations, Groups, Software

### CVE (Common Vulnerabilities and Exposures)
- **URL:** https://cve.mitre.org/
- **Purpose:** Dictionary of publicly known cybersecurity vulnerabilities

### CWE (Common Weakness Enumeration)
- **URL:** https://cwe.mitre.org/
- **Purpose:** Community-developed list of software weakness types

### NIST Cybersecurity Framework
- **URL:** https://www.nist.gov/cyberframework
- **Version:** 2.0 (2024)
- **Functions:** Identify, Protect, Detect, Respond, Recover

### OCSF (Open Cybersecurity Schema Framework)
- **URL:** https://schema.ocsf.io/
- **Purpose:** Open standard for cybersecurity event schemas

---

## Datasets for Research

### DDoS Attack Datasets

| Dataset | Year | Size | Attack Types | Link |
|---------|------|------|--------------|------|
| CAIDA DDoS | 2007-2024 | ~50GB | Various | https://www.caida.org/catalog/datasets/ddos-attack-dataset/ |
| CIC-DDoS2019 | 2019 | ~15GB | 12 types | https://www.unb.ca/cic/datasets/ddos-2019.html |
| UNSW-DDoS | 2019 | ~10GB | 10 types | https://research.unsw.edu.au/projects/ddos-dataset |
| CIC-DDoS2017 | 2017 | ~8GB | 5 types | https://www.unb.ca/cic/datasets/ddos-2017.html |
| BoT-IoT | 2019 | ~72GB | DDoS, Botnet | https://research.unsw.edu.au/projects/bot-iot-dataset |

### Network Traffic Datasets

| Dataset | Year | Size | Purpose | Link |
|---------|------|------|---------|------|
| CIC-IDS2017 | 2017 | ~2GB | IDS evaluation | https://www.unb.ca/cic/datasets/ids-2017.html |
| NSL-KDD | 2009 | ~100MB | Benchmark | https://www.unb.ca/cic/datasets/nsl.html |
| UNSW-NB15 | 2015 | ~2GB | IDS evaluation | https://research.unsw.edu.au/projects/unsw-nb15-dataset |

---

## Tools and Technologies

### Graph Databases

| Tool | Type | License | Best For |
|------|------|---------|----------|
| Neo4j | Property Graph | GPL/Commercial | Production systems |
| Apache Jena | RDF/OWL | Apache 2.0 | Semantic web applications |
| JanusGraph | Property Graph | Apache 2.0 | Large-scale graphs |
| Amazon Neptune | Property Graph | Commercial | Cloud deployments |
| TigerGraph | Property Graph | Commercial | High-performance analytics |

### Graph Processing Frameworks

| Tool | Language | Purpose |
|------|----------|---------|
| Apache Spark GraphX | Scala/Python | Large-scale graph processing |
| NetworkX | Python | Graph algorithms |
| igraph | C/Python/R | Network analysis |
| Gephi | Java | Graph visualization |
| Graph-tool | Python | Statistical analysis |

### Graph Neural Network Libraries

| Library | Framework | Key Features |
|---------|-----------|--------------|
| PyTorch Geometric | PyTorch | GNN layers, datasets, transforms |
| DGL (Deep Graph Library) | PyTorch/TF | Scalable GNN training |
| GraphSAGE | TensorFlow | Inductive representation learning |
| StellarGraph | TensorFlow | Graph ML for networks |

### Ontology Tools

| Tool | Purpose |
|------|---------|
| Protégé | Ontology editor |
| TopBraid Composer | Semantic web IDE |
| OWL API | Java library for OWL |
| RDFLib | Python RDF library |

---

## Key Research Questions for the Article

### Primary Questions

1. **RQ1:** How can knowledge graphs effectively model network behavior for DDoS detection?
   - Sub-questions:
     - What entities and relationships are essential?
     - How to represent temporal dynamics?
     - How to incorporate threat intelligence?

2. **RQ2:** What ontology structure best represents DDoS attack patterns?
   - Sub-questions:
     - How to align with existing standards (STIX, ATT&CK)?
     - How to enable reasoning and inference?
     - How to handle uncertainty?

3. **RQ3:** How does semantic reasoning improve detection accuracy?
   - Sub-questions:
     - What reasoning rules are most effective?
     - How to balance precision and recall?
     - How to reduce false positives?

### Secondary Questions

4. **RQ4:** How does the approach compare to traditional ML/DL methods?
5. **RQ5:** What are the scalability limitations?
6. **RQ6:** How to enable explainable detection decisions?

---

## Potential Contributions

1. **Novel Ontology**
   - DDoS-specific ontology aligned with STIX 2.1
   - Support for multi-vector attack modeling
   - Integration with threat intelligence feeds

2. **Detection Methodology**
   - Semantic reasoning rules for DDoS detection
   - Graph-based anomaly scoring
   - Multi-level detection (traffic, behavior, structure)

3. **Implementation Framework**
   - Open-source knowledge graph construction pipeline
   - Integration with existing SIEM tools
   - Real-time detection capabilities

4. **Experimental Validation**
   - Benchmark on standard datasets
   - Comparison with state-of-the-art methods
   - Ablation studies on components

---

## Writing Timeline

| Phase | Duration | Tasks |
|-------|----------|-------|
| Literature Review | 2-3 weeks | Read 30+ papers, organize references |
| Ontology Design | 1-2 weeks | Formalize ontology in OWL |
| Implementation | 3-4 weeks | Build prototype system |
| Experiments | 2-3 weeks | Run experiments, collect results |
| Writing | 3-4 weeks | Draft paper, revisions |
| Review | 1-2 weeks | Peer review, final edits |

**Total Estimated Time:** 12-18 weeks

---

## Target Venues

### Top-Tier Conferences
- IEEE S&P (Symposium on Security and Privacy)
- ACM CCS (Computer and Communications Security)
- USENIX Security Symposium
- NDSS (Network and Distributed System Security Symposium)

### Reputable Journals
- IEEE Transactions on Information Forensics and Security (TIFS)
- IEEE Transactions on Dependable and Secure Computing (TDSC)
- Computers & Security (Elsevier)
- Journal of Cybersecurity (Oxford)

### Specialized Venues
- IEEE International Conference on Knowledge Graph (ICKG)
- Semantic Web Journal
- IEEE Military Communications Conference (MILCOM)

---

*Document created for research planning purposes*
*Last updated: April 2026*
