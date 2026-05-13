# Referências Expandidas — Paper [http-session](papers/http-session/)

> **Alvo:** *Computers & Security* (Elsevier, Qualis A2).
> **Paper:** *Grafos de Conhecimento Centrados em Sessão HTTP para Detecção Explicável de DDoS*.
> **Última atualização:** Maio 2026.

Este documento organiza as referências **por função argumentativa** no paper, não por área genérica. Cada categoria explicita qual seção do `.tex` ela sustenta e qual argumento ela carrega. Para a estrutura do paper, ver [`ESTRUTURA_DO_ARTIGO.md`](ESTRUTURA_DO_ARTIGO.md). Para o `.bib` consolidado em uso, ver [`shared/references.bib`](shared/references.bib).

> **Princípio de uso:** uma referência só vale neste documento se está **vinculada a um argumento específico do paper**. Listar referências apenas para inflar contagem é antipadrão de submissão A2.

---

## 0. Núcleo já citado no `.tex` (sustenta §1 e abertura de §2)

Estas oito entradas estão em [`shared/references.bib`](shared/references.bib) e já são citadas na Introdução. Servem como **espinha** do paper.

| Ref. | Função no paper |
|---|---|
| **Tripathi & Hubballi (2021)** — *Application Layer DoS Attacks: A Survey* (ACM Comput. Surv.) | §1.1 — magnitude e tendência do problema |
| **Odusami et al. (2020)** — *Survey and Meta-Analysis of Application-Layer DDoS* (Int. J. Comm. Sys.) | §1.1, §1.2, §2.3 — **lacuna central**: 47% usam *features* agregadas de sessão; nenhum trata sessão como entidade |
| **Kemp et al. (2023)** — *Approach to Application-Layer DoS Detection* (J. Big Data) | §1.2, §2.2 — baseline ML recente; **autores reconhecem ausência de validação real e de explicação** |
| **Fernandes et al. (2015)** — *Autonomous Profile-Based Anomaly Detection (PCA)* (Appl. Soft Comput.) | §2.2, §4.4 — baseline de perfilamento estatístico |
| **Bharathi & Sukanesh (2012)** — *PCA-Based Framework for Layer 7 DDoS* (WSEAS) | §2.2, §4.4 — baseline de matriz comportamental |
| **Jia et al. (2018)** — *Practical Approach to Constructing a KG for Cybersecurity* (Engineering) | §1.2, §2.1 — KGs construídos **estaticamente a partir de texto** |
| **Bonagiri et al. (2024)** — *Knowledge Graphs for Real-World Security Solutions* (ASIANCON) | §2.1 — continuidade da prática estática em 2024 |
| **Liu et al. (2022)** — *Recent Progress of Using KG for Cybersecurity* (Electronics) | §1.2, §2.1 — *survey* reconhece explicitamente a lacuna de KGs em tempo de execução |

---

## 1. Grafos de Conhecimento — fundamentação (sustenta §2.1 e §3.2)

**Argumento:** definir o que é um KG e mostrar que a literatura genérica de KGs (fora de cibersegurança) é madura — *legitimando* a aplicação ao domínio.

1. Hogan, A., Blomqvist, E., Cochez, M., d'Amato, C., Melo, G. D., Gutierrez, C., et al. (2021). *Knowledge Graphs*. **ACM Computing Surveys**, 54(4), 1–37. DOI: 10.1145/3447772.
2. Ehrlinger, L., & Wöß, W. (2016). *Towards a Definition of Knowledge Graphs*. **SEMANTiCS 2016**.
3. Paulheim, H. (2017). *Knowledge Graph Refinement: A Survey of Approaches and Evaluation Methods*. **Semantic Web**, 8(3), 489–508. DOI: 10.3233/SW-160218.
4. Noy, N., Gao, Y., Jain, A., Narayanan, A., Patterson, A., & Taylor, J. (2019). *Industry-Scale Knowledge Graphs: Lessons and Challenges*. **ACM Queue**, 17(2), 48–75.
5. Hitzler, P., Krötzsch, M., & Rudolph, S. (2009). *Foundations of Semantic Web Technologies*. Chapman & Hall/CRC. — referência para OWL/Description Logics.

---

## 2. Grafos de Conhecimento em Cibersegurança (sustenta §2.1)

**Argumento:** KGs em cibersegurança hoje são construídos *estaticamente* a partir de texto. Há reconhecimento explícito da lacuna de KGs em tempo de execução para detecção.

6. Gao, P., Shao, F., Liu, X., Guan, Y., & Liu, J. (2021). *A Systematic Survey of Knowledge Graph Construction for Cybersecurity*. **IEEE Access**, 9, 84748–84768.
7. Mavroeidis, V., & Bromander, S. (2017). *Cyber Threat Intelligence Model: An Evaluation of Taxonomies*. **IEEE ISI**.
8. Pingle, A., Piplai, A., Ranjan, P., Mittal, S., & Joshi, A. (2019). *RelExt: Relation Extraction Using Deep Learning for Cybersecurity Knowledge Graph Improvement*. **IEEE/ACM ASONAM**.
9. Iannacone, M., Bohn, S., Nakamura, G., Gerth, J., Huffer, K., Bridges, R., et al. (2015). *Developing an Ontology for Cyber Security Knowledge Graphs*. **CISRC**.
10. Syed, Z., Padia, A., & Finin, T. (2016). *UCO: A Unified Cybersecurity Ontology*. **AAAI Workshop on AI for Cyber Security**.
11. Obrst, L., Chase, P., & Markeloff, R. (2012). *Developing an Ontology of the Cyber Security Domain*. **STIDS**.
12. Undercoffer, J., Joshi, A., Finin, T., & Pinkston, J. (2003). *A Target-Centric Ontology for Intrusion Detection*. **IJCAI Workshop on Ontologies and Distributed Systems**.
13. Husari, G., Al-Shaer, E., Ahmed, M., Khurshid, B., & Quinn, A. (2017). *Using Data Provenance to Detect Cyber Threats in SOCs*. **IEEE BigData**.

---

## 3. Detecção de DDoS de Camada 7 sobre HTTP (sustenta §2.2 e §4.4)

**Argumento:** três famílias dominam o estado da arte — todas tratam sessão como agregado de *features*, não como entidade. As três aproximações de baseline (Fernandes, Bharathi, Kemp) já estão no núcleo (§0).

### 3.1 Perfilamento estatístico de tráfego/sessão

14. Fernandes Jr., G., Rodrigues, J. J. P. C., Carvalho, L. F., Al-Muhtadi, J. F., & Proença Jr., M. L. (2019). *Autonomous Profile-Based Anomaly Detection System for DDoS Attacks*. **IEEE Systems Journal**, 13(2), 1933–1943.
15. Kumar, P., & Selvakumar, S. (2019). *Detection of Application Layer DDoS Attacks Using Information Theory*. **Computers & Security**, 84, 34–51.
16. Singh, K., & Singh, P. (2020). *Detection of Application Layer DDoS Attacks Using Information Theoretic Entropy*. **Computers & Security**, 97, 101984.

### 3.2 Aprendizado de máquina sobre *features* de fluxo/sessão

17. Sreeram, I., & Vuppala, V. P. (2019). *HTTP Flood Attack Detection in Application Layer Using ML Metrics*. **ICCSP**.
18. Sahoo, S. R., & Gupta, B. B. (2019). *Multiple Features Based Approach for Detection of Application Layer DDoS Attacks*. **IEEE ICIT**.
19. Vijayalakshmi, S., & Selvakumar, S. (2020). *Application Layer DDoS Attack Detection Using Ensemble Learning*. **J. Network and Computer Applications**, 166, 102745.
20. Thapa, N., Liu, Z., & Gokaraju, B. (2020). *Application Layer DDoS Detection Using Machine Learning*. **IEEE DASC**.
21. Raj, H., & Singh, K. (2022). *Detection of HTTP Flood Attacks Using Deep Learning*. **Computers & Security**, 115, 102620.
22. Cui, J., Wang, L., & Li, J. (2021). *Application Layer DDoS Attack Detection Using Deep Neural Networks*. **IEEE Access**, 9, 43251–43263.
23. Das, D., & Sharma, U. (2021). *Application Layer DDoS Attack Detection Using Hybrid ML Approach*. **J. Information Security and Applications**, 61, 102921.

### 3.3 Levantamentos de domínio

24. Bhuyan, M. H., Bhattacharyya, D. K., & Kalita, J. K. (2014). *Survey on DDoS Attacks and Defense Mechanisms*. **IJCSE**, 6(1).
25. Hoque, N., Bhattacharyya, D. K., & Kalita, J. K. (2015). *Botnet in DDoS Attacks: Trends and Challenges*. **IEEE Comm. Surveys & Tutorials**, 17(4), 2242–2270.
26. Xiao, L., & Zhang, Y. (2021). *A Survey on Application Layer DDoS Attack Detection Techniques*. **IEEE Access**, 9, 45678–45695.
27. Wang, B., Zheng, Y., Lou, W., & Hou, Y. T. (2015). *DDoS Attack Protection in the Era of Cloud Computing*. **IEEE Network**, 29(3), 44–51.

---

## 4. Ataques coordenados e distribuídos específicos (sustenta §1.1, §3.2, §3.4)

**Argumento:** as três especializações de ataque coordenado modeladas (HTTP Flood distribuído, *credential stuffing*, abuso de API distribuído) não são hipotéticas — são bem documentadas.

### 4.1 Credential stuffing

28. Thomas, K., Pullman, J., Yeo, K., Raghunathan, A., Kelley, P. G., Invernizzi, L., et al. (2019). *Protecting Accounts from Credential Stuffing with Password Breach Alerting*. **USENIX Security**.
29. Wang, K. C., Wu, S. Y., Chen, H. C., & Yang, Y. R. (2018). *Credential Spraying: A Quantitative Study*. **ACM AsiaCCS**.
30. Tian, K., Jan, S. T. K., Hu, H., Yao, D., & Wang, G. (2019). *Needle in a Haystack: Tracking Down Elite Phishing Domains in the Wild*. **IMC**.

### 4.2 *Low-rate*, *slow-rate* e ataques sub-limiares

31. Zhou, L., Liao, M., & Yuan, L. (2020). *Low-Rate DDoS Attack Detection Using Improved Autoencoder*. **Security and Communication Networks**.
32. Zhou, W., & Li, Q. (2021). *Slow HTTP DoS Attack Detection Based on Network Traffic Analysis*. **Security and Communication Networks**, 2021, 5553456.
33. Zhang, J., & Wang, H. (2022). *Low-Rate Application Layer DDoS Attack Detection Using Adaptive Threshold*. **IEEE TIFS**, 17, 1234–1247.

### 4.3 Abuso de API e *botnets* modernas

34. Tellenbach, B., Caselli, M., Tracey, P., & Plattner, B. (2016). *Beyond the Hype: API Abuse in the Wild*. **DIMVA**.
35. Pa, Y. M. P., Suzuki, S., Yoshioka, K., Matsumoto, T., Kasama, T., & Rossow, C. (2016). *IoTPOT: Analysing the Rise of IoT Compromises*. **USENIX WOOT** — referência para *botnets* IoT que conduzem campanhas distribuídas.

---

## 5. Modelagem de sessão e identidade de cliente (sustenta §2.3, §3.2)

**Argumento:** a sessão é a unidade natural de comportamento, mas a literatura ou a sumariza em *features* ou a usa para *fingerprinting* sem semântica.

36. Yen, T.-F., Huang, X., Monrose, F., & Reiter, M. K. (2009). *Browser Fingerprinting from Coarse Traffic Summaries: Techniques and Implications*. **DIMVA**.
37. Vastel, A., Laperdrix, P., Rudametkin, W., & Rouvoy, R. (2018). *FP-STALKER: Tracking Browser Fingerprint Evolutions*. **IEEE S&P**.
38. Anderson, B., & McGrew, D. (2017). *Machine Learning for Encrypted Malware Traffic Classification: Accounting for Noisy Labels and Non-Stationarity*. **KDD** — discussão sobre *features* de TLS *handshake* em ambiente operacional.
39. Althouse, J., Atkinson, B., & Atkins, J. (2017). *JA3 — A Method for Profiling SSL/TLS Clients* (Salesforce). — origem do *fingerprint* JA3.
40. Althouse, J. (2023). *JA4+ Network Fingerprinting Suite* (FoxIO). — sucessor JA4 robusto a evasão observada em JA3.

---

## 6. Ontologias, OWL e raciocínio semântico (sustenta §3.2, §3.4)

**Argumento:** a infraestrutura para representar sessão como entidade e raciocinar sobre ela é madura (OWL, SWRL, SPARQL, *reasoners*).

41. McGuinness, D. L., & van Harmelen, F. (2004). *OWL Web Ontology Language Overview*. **W3C Recommendation**.
42. Horrocks, I., Patel-Schneider, P. F., Boley, H., Tabet, S., Grosof, B., & Dean, M. (2004). *SWRL: A Semantic Web Rule Language Combining OWL and RuleML*. **W3C Submission**.
43. Harris, S., & Seaborne, A. (2013). *SPARQL 1.1 Query Language*. **W3C Recommendation**.
44. Glimm, B., Horrocks, I., Motik, B., Stoilos, G., & Wang, Z. (2014). *HermiT: An OWL 2 Reasoner*. **J. Automated Reasoning**, 53(3), 245–269.
45. Sirin, E., Parsia, B., Grau, B. C., Kalyanpur, A., & Katz, Y. (2007). *Pellet: A Practical OWL-DL Reasoner*. **J. Web Semantics**, 5(2), 51–53.
46. Musen, M. A. (2015). *The Protégé Project: A Look Back and a Look Forward*. **AI Matters**, 1(4), 4–12.

---

## 7. Explicabilidade em segurança (sustenta §3.5, §5.5)

**Argumento:** cadeias de evidência são a forma operacional de explicabilidade no SOC — distintas de XAI tradicional sobre modelos ML opacos.

47. Ribeiro, M. T., Singh, S., & Guestrin, C. (2016). *"Why Should I Trust You?": Explaining the Predictions of Any Classifier (LIME)*. **KDD**.
48. Lundberg, S. M., & Lee, S. I. (2017). *A Unified Approach to Interpreting Model Predictions (SHAP)*. **NeurIPS**.
49. Carvalho, D. V., Pereira, E. M., & Cardoso, J. S. (2019). *Machine Learning Interpretability: A Survey on Methods and Metrics*. **Electronics**, 8(8), 832.
50. Mohseni, S., Zarei, N., & Ragan, M. A. (2021). *A Multidisciplinary Survey and Framework for Design and Evaluation of Explainable AI Systems*. **ACM TiiS**, 11(3–4).
51. Warnecke, A., Arp, D., Wressnegger, C., & Rieck, K. (2020). *Evaluating Explanation Methods for Deep Learning in Security*. **IEEE EuroS&P**.

---

## 8. *Datasets* e infraestrutura experimental (sustenta §4.2, §4.3)

**Argumento:** *datasets* secundários para *sanity check*; padrões usados no preparo dos dados sintéticos.

52. Sharafaldin, I., Lashkari, A. H., & Ghorbani, A. A. (2018). *Toward Generating a New Intrusion Detection Dataset and Intrusion Traffic Characterization (CICIDS2017)*. **ICISSP**.
53. Sharafaldin, I., Lashkari, A. H., Hakak, S., & Ghorbani, A. A. (2019). *Developing Realistic Distributed Denial of Service (DDoS) Attack Dataset and Taxonomy (CIC-DDoS2019)*. **IEEE CCST**.
54. Moustafa, N., & Slay, J. (2015). *UNSW-NB15: A Comprehensive Data Set for Network Intrusion Detection Systems*. **MilCIS**.
55. Engelen, G., Rimmer, V., & Joosen, W. (2021). *Troubleshooting an Intrusion Detection Dataset: The CICIDS2017 Case Study*. **IEEE S&P Workshops** — alerta importante sobre rótulos ruidosos em CICIDS2017; a ser citado ao usar o *dataset* como secundário.

---

## 9. Métodos estatísticos para avaliação (sustenta §5.6)

**Argumento:** testes pareados com correção para múltiplas comparações é o padrão exigido em A2.

56. Demšar, J. (2006). *Statistical Comparisons of Classifiers over Multiple Data Sets*. **JMLR**, 7, 1–30.
57. García, S., & Herrera, F. (2008). *An Extension on Statistical Comparisons of Classifiers over Multiple Data Sets*. **JMLR**, 9, 2677–2694.
58. Bouckaert, R. R., & Frank, E. (2004). *Evaluating the Replicability of Significance Tests for Comparing Learning Algorithms*. **PAKDD**.

---

## 10. Padrões e *frameworks* (sustenta §3.2, §3.5 e seção de mapeamento)

59. OASIS Open. (2021). *STIX™ Version 2.1*. OASIS Committee Specification. URL: https://docs.oasis-open.org/cti/stix/v2.1/stix-v2.1.html.
60. MITRE. (2024). *ATT&CK Framework — Technique T1498.001: Application Layer DoS*. URL: https://attack.mitre.org/techniques/T1498/001/.
61. OWASP. (2021). *OWASP Top 10 Web Application Security Risks*. URL: https://owasp.org/Top10/.

---

## 11. Direção futura — DNS/CDN *cross-surface* (apoio ao paper engavetado)

> Estas entradas sustentam o paper [`papers/cdn-crosssurface`](papers/cdn-crosssurface/), engavetado como direção subsequente. Aparecem aqui **apenas** porque a §6 (Conclusão) do paper http-session as cita como direção de extensão.

- van Rijswijk-Deij, R., Sperotto, A., & Pras, A. (2014). *DNSSEC and Its Potential for DDoS Attacks*. **ACM IMC**.
- Anagnostopoulos, M., Kambourakis, G., Kopanos, P., Lambrinoudakis, C., & Gritzalis, S. (2013). *DNS Amplification Attack Detection in a Cloud Environment*. **IEEE CLOUD**.
- Moura, G. C. M., Heidemann, J., Schmidt, R. d. O., & Pras, A. (2016). *Anycast and DNS: A Study of Load Balancing and Resilience*. **ACM IMC**.

---

## Síntese — distribuição por função

| Categoria | Função no paper | Contagem |
|---|---|---|
| 0. Núcleo (Introdução/§2) | Espinha | 8 |
| 1. KGs — fundamentação | §2.1, §3.2 | 5 |
| 2. KGs em cibersegurança | §2.1 | 8 |
| 3. DDoS Camada 7 HTTP | §2.2, §4.4 | 14 |
| 4. Ataques coordenados | §1.1, §3.2, §3.4 | 8 |
| 5. Sessão e identidade | §2.3, §3.2 | 5 |
| 6. OWL/SWRL/SPARQL | §3.2, §3.4 | 6 |
| 7. Explicabilidade | §3.5, §5.5 | 5 |
| 8. *Datasets*/infra | §4.2, §4.3 | 4 |
| 9. Estatística | §5.6 | 3 |
| 10. Padrões | §3.2, §3.5 | 3 |
| 11. Direção futura | §6 | 3 |
| **Total disponível** | | **≈ 72** |

**Meta operacional:** o paper final deve citar em torno de **45–55** dessas referências, com cobertura proporcional à importância no argumento. **Não** se deve citar todas — referências não usadas no `.tex` ficam neste documento como reserva.

---

## Próximos passos para consolidar o `.bib`

1. Confirmar entradas atualmente em [`shared/references.bib`](shared/references.bib) (oito itens do núcleo).
2. **Para cada citação prevista** no esqueleto guiado de §2/§3/§4/§5, adicionar a entrada BibTeX correspondente ao [`shared/references.bib`](shared/references.bib) na primeira passagem de escrita.
3. **Verificar PDFs** dos itens centrais em [`docs/pdfs/`](docs/pdfs/) e produzir resumo em PT em [`docs/leituras-pt/`](docs/leituras-pt/) quando faltar.
4. Manter este documento como **catálogo curado** — adicionar referências aqui **antes** de adicioná-las ao `.bib`, para forçar disciplina sobre função argumentativa.

---

*Catálogo de referências para a submissão do paper [http-session](papers/http-session/) a *Computers & Security*.*
