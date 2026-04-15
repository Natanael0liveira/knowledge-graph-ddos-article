# Referências e Recursos para Detecção de DDoS com Grafos de Conhecimento

## Artigos Acadêmicos

### Grafos de Conhecimento - Trabalhos Fundamentais

1. **Ehrlinger, L., & Wöß, W. (2016).** "Towards a Definition of Knowledge Graphs." *SEMANTiCS 2016*.
   - DOI: 10.13140/RG.2.2.18223.41127
   - Contribuição-chave: Definição formal e taxonomia de grafos de conhecimento

2. **Hogan, A., Blomqvist, E., Cochez, M., d'Amato, C., Melo, G. D., Gutierrez, C., ... & Zimmermann, A. (2021).** "Knowledge Graphs." *ACM Computing Surveys*, 54(4), 1-37.
   - DOI: 10.1145/3447772
   - Survey abrangente de tecnologias de grafos de conhecimento

3. **Paulheim, H. (2017).** "Knowledge Graph Refinement: A Survey of Approaches and Evaluation Methods." *Semantic Web*, 8(3), 489-508.
   - DOI: 10.3233/SW-160218

### Grafos de Conhecimento em Cibersegurança

4. **Jia, Y., Qi, J., Shang, H., Jiang, R., & Li, A. (2018).** "A Practical Approach to Constructing a Knowledge Graph for Cybersecurity." *Engineering*, 4(4), 503-511.
   - DOI: 10.1016/j.eng.2018.07.012

5. **Noel, S., Harley, E., Tam, K. H., & Gyor, G. (2015).** "Cyber Graph Analytics for Security." *IEEE Military Communications Conference (MILCOM)*.
   - DOI: 10.1109/MILCOM.2015.7357601

6. **Husari, G., Al-Shaer, E., Ahmed, M., Khurshid, B., & Quinn, A. (2017).** "Using Data Provenance to Detect Cyber Threats in Security Operations Centers." *IEEE International Conference on Big Data*.
   - DOI: 10.1109/BigData.2017.8258337

7. **Liu, J., & Li, T. (2020).** "Knowledge Graph Construction for Cyber Security." *IEEE International Conference on Knowledge Graph (ICKG)*.
   - DOI: 10.1109/ICKG50412.2020.00021

8. **Pingle, A., Piplai, A., Ranjan, P., Mittal, S., & Joshi, A. (2019).** "Relext: Relation Extraction Using Deep Learning Approaches for Cybersecurity Knowledge Graph Improvement." *Proceedings of the 2019 IEEE/ACM International Conference on Advances in Social Networks Analysis and Mining*.

### Detecção de Ataques DDoS

9. **Bhuyan, M. H., Bhattacharyya, D. K., & Kalita, J. K. (2014).** "Survey on DDoS Attacks and Defense Mechanisms." *International Journal of Computer Science and Engineering*, 6(1), 1-30.
   - DOI: 10.1504/IJCSE.2014.057851

10. **Moustafa, N., & Slay, J. (2019).** "UNSW-NB15: A Comprehensive Data Set for Network Intrusion Detection Systems (UNSW-NB15 Network Data Set)." *IEEE Military Communications and Information Systems Conference (MilCIS)*.
    - DOI: 10.1109/MilCIS.2019.8927807

11. **Sharafaldin, I., Lashkari, A. H., & Ghorbani, A. A. (2019).** "CIC-DDoS2019: A Comprehensive Dataset for DDoS Attack Detection." *IEEE Canadian Conference of Electrical and Computer Engineering (CCECE)*.
    - DOI: 10.1109/CCECE.2019.8861865

12. **Zhou, L., Liao, M., & Yuan, L. (2020).** "Low-Rate DDoS Attack Detection Using Improved Autoencoder." *Security and Communication Networks*.
    - DOI: 10.1155/2020/8829285

### Redes Neurais em Grafos para Segurança

13. **Kipf, T. N., & Welling, M. (2017).** "Semi-Supervised Classification with Graph Convolutional Networks." *International Conference on Learning Representations (ICLR)*.
    - arXiv: 1609.02907

14. **Velickovic, P., Cucurull, G., Casanova, A., Romero, A., Lio, P., & Bengio, Y. (2018).** "Graph Attention Networks." *International Conference on Learning Representations (ICLR)*.
    - arXiv: 1710.10903

15. **Lo, W. W., Layeghy, S., Sarhan, M., Hajizadeh, M., & Portmann, M. (2022).** "Graph-based Network Intrusion Detection: A Survey." *IEEE Access*.
    - DOI: 10.1109/ACCESS.2022.3140576

### Segurança Semântica e Ontologias

16. **Obrst, L., Chase, P., & Markeloff, R. (2012).** "Developing an Ontology of the Cyber Security Domain." *Proceedings of the International Conference on Semantic Technologies for Intelligence, Defense, and Security (STIDS)*.

17. **Undercoffer, J., Joshi, A., Finin, T., & Pinkston, J. (2003).** "A Target-Centric Ontology for Intrusion Detection." *Proceedings of the IJCAI Workshop on Ontologies and Distributed Systems*.

18. **Syed, Z., Padia, A., & Finin, T. (2016).** "UCO: A Unified Cybersecurity Ontology." *Proceedings of the AAAI Workshop on Artificial Intelligence for Cyber Security*.

19. **Iannacone, M., Bohn, S., Nakamura, G., Gerth, J., Huffer, K., Bridges, R., ... & Goodall, J. (2015).** "Developing an Ontology for Cyber Security Knowledge Graphs." *Proceedings of the 10th Annual Cyber and Information Security Research Conference*.

---

## Padrões e Frameworks

### STIX 2.1 (Structured Threat Information Expression)
- **Organização:** OASIS Cyber Threat Intelligence (CTI) TC
- **URL:** https://oasis-open.github.io/cti-documentation/stix/intro
- **Propósito:** Linguagem padronizada para compartilhamento de inteligência de ameaças cibernéticas
- **Características Principais:**
  - Objetos: Attack Pattern, Campaign, Course of Action, Identity, Indicator, Intrusion Set, Malware, Observed Data, Report, Threat Actor, Tool, Vulnerability
  - Relações: related-to, targets, uses, indicates, etc.

### MITRE ATT&CK Framework
- **URL:** https://attack.mitre.org/
- **Propósito:** Base de conhecimento de táticas e técnicas de adversários
- **Características Principais:**
  - 14 Táticas (Enterprise)
  - 193+ Técnicas
  - 401+ Sub-técnicas
  - Mitigações, Grupos, Software

### CVE (Common Vulnerabilities and Exposures)
- **URL:** https://cve.mitre.org/
- **Propósito:** Dicionário de vulnerabilidades de segurança cibernética conhecidas publicamente

### CWE (Common Weakness Enumeration)
- **URL:** https://cwe.mitre.org/
- **Propósito:** Lista desenvolvida pela comunidade de tipos de fraquezas de software

### NIST Cybersecurity Framework
- **URL:** https://www.nist.gov/cyberframework
- **Versão:** 2.0 (2024)
- **Funções:** Identificar, Proteger, Detectar, Responder, Recuperar

### OCSF (Open Cybersecurity Schema Framework)
- **URL:** https://schema.ocsf.io/
- **Propósito:** Padrão aberto para schemas de eventos de cibersegurança

---

## Datasets para Pesquisa

### Datasets de Ataques DDoS

| Dataset | Ano | Tamanho | Tipos de Ataque | Link |
|---------|-----|---------|-----------------|------|
| CAIDA DDoS | 2007-2024 | ~50GB | Vários | https://www.caida.org/catalog/datasets/ddos-attack-dataset/ |
| CIC-DDoS2019 | 2019 | ~15GB | 12 tipos | https://www.unb.ca/cic/datasets/ddos-2019.html |
| UNSW-DDoS | 2019 | ~10GB | 10 tipos | https://research.unsw.edu.au/projects/ddos-dataset |
| CIC-DDoS2017 | 2017 | ~8GB | 5 tipos | https://www.unb.ca/cic/datasets/ddos-2017.html |
| BoT-IoT | 2019 | ~72GB | DDoS, Botnet | https://research.unsw.edu.au/projects/bot-iot-dataset |

### Datasets de Tráfego de Rede

| Dataset | Ano | Tamanho | Propósito | Link |
|---------|-----|---------|-----------|------|
| CIC-IDS2017 | 2017 | ~2GB | Avaliação IDS | https://www.unb.ca/cic/datasets/ids-2017.html |
| NSL-KDD | 2009 | ~100MB | Benchmark | https://www.unb.ca/cic/datasets/nsl.html |
| UNSW-NB15 | 2015 | ~2GB | Avaliação IDS | https://research.unsw.edu.au/projects/unsw-nb15-dataset |

---

## Ferramentas e Tecnologias

### Bancos de Dados de Grafos

| Ferramenta | Tipo | Licença | Melhor Para |
|------------|------|---------|-------------|
| Neo4j | Grafo de Propriedades | GPL/Comercial | Sistemas de produção |
| Apache Jena | RDF/OWL | Apache 2.0 | Aplicações web semânticas |
| JanusGraph | Grafo de Propriedades | Apache 2.0 | Grafos de grande escala |
| Amazon Neptune | Grafo de Propriedades | Comercial | Implantações em nuvem |
| TigerGraph | Grafo de Propriedades | Comercial | Analytics de alta performance |

### Frameworks de Processamento de Grafos

| Ferramenta | Linguagem | Propósito |
|------------|-----------|-----------|
| Apache Spark GraphX | Scala/Python | Processamento de grafos em larga escala |
| NetworkX | Python | Algoritmos de grafos |
| igraph | C/Python/R | Análise de redes |
| Gephi | Java | Visualização de grafos |
| Graph-tool | Python | Análise estatística |

### Bibliotecas de Redes Neurais em Grafos

| Biblioteca | Framework | Características Principais |
|------------|-----------|---------------------------|
| PyTorch Geometric | PyTorch | Camadas GNN, datasets, transforms |
| DGL (Deep Graph Library) | PyTorch/TF | Treinamento GNN escalável |
| GraphSAGE | TensorFlow | Aprendizado de representação indutivo |
| StellarGraph | TensorFlow | Graph ML para redes |

### Ferramentas de Ontologia

| Ferramenta | Propósito |
|------------|-----------|
| Protégé | Editor de ontologias |
| TopBraid Composer | IDE web semântica |
| OWL API | Biblioteca Java para OWL |
| RDFLib | Biblioteca Python RDF |

---

## Questões de Pesquisa para o Artigo

### Questões Primárias

1. **QP1:** Como os grafos de conhecimento podem modelar efetivamente o comportamento da rede para detecção de DDoS?
   - Sub-questões:
     - Quais entidades e relações são essenciais?
     - Como representar dinâmicas temporais?
     - Como incorporar inteligência de ameaças?

2. **QP2:** Qual estrutura de ontologia melhor representa os padrões de ataque DDoS?
   - Sub-questões:
     - Como alinhar com padrões existentes (STIX, ATT&CK)?
     - Como habilitar raciocínio e inferência?
     - Como lidar com incerteza?

3. **QP3:** Como o raciocínio semântico melhora a precisão da detecção?
   - Sub-questões:
     - Quais regras de raciocínio são mais eficazes?
     - Como equilibrar precisão e recall?
     - Como reduzir falsos positivos?

### Questões Secundárias

4. **QP4:** Como a abordagem se compara aos métodos tradicionais de ML/DL?
5. **QP5:** Quais são as limitações de escalabilidade?
6. **QP6:** Como habilitar decisões de detecção explicáveis?

---

## Potenciais Contribuições

1. **Ontologia Inovadora**
   - Ontologia específica para DDoS alinhada com STIX 2.1
   - Suporte para modelagem de ataques multi-vetor
   - Integração com feeds de inteligência de ameaças

2. **Metodologia de Detecção**
   - Regras de raciocínio semântico para detecção de DDoS
   - Escore de anomalia baseado em grafo
   - Detecção em múltiplos níveis (tráfego, comportamento, estrutura)

3. **Framework de Implementação**
   - Pipeline de construção de grafo de conhecimento open-source
   - Integração com ferramentas SIEM existentes
   - Capacidades de detecção em tempo real

4. **Validação Experimental**
   - Benchmark em datasets padrão
   - Comparação com métodos estado-da-arte
   - Estudos de ablação nos componentes

---

## Cronograma de Redação

| Fase | Duração | Tarefas |
|------|---------|---------|
| Revisão de Literatura | 2-3 semanas | Ler 30+ artigos, organizar referências |
| Design da Ontologia | 1-2 semanas | Formalizar ontologia em OWL |
| Implementação | 3-4 semanas | Construir sistema protótipo |
| Experimentos | 2-3 semanas | Executar experimentos, coletar resultados |
| Redação | 3-4 semanas | Escrever artigo, revisões |
| Revisão | 1-2 semanas | Revisão por pares, ajustes finais |

**Tempo Total Estimado:** 12-18 semanas

---

## Veículos-Alvo

### Conferências de Alto Nível
- IEEE S&P (Symposium on Security and Privacy)
- ACM CCS (Computer and Communications Security)
- USENIX Security Symposium
- NDSS (Network and Distributed System Security Symposium)

### Periódicos Reputados
- IEEE Transactions on Information Forensics and Security (TIFS)
- IEEE Transactions on Dependable and Secure Computing (TDSC)
- Computers & Security (Elsevier)
- Journal of Cybersecurity (Oxford)

### Veículos Especializados
- IEEE International Conference on Knowledge Graph (ICKG)
- Semantic Web Journal
- IEEE Military Communications Conference (MILCOM)

---

*Documento criado para fins de planejamento de pesquisa*
*Última atualização: Abril 2026*
