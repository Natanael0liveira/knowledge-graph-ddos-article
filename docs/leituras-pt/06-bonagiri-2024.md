# Aplicações Práticas de Cibersegurança: Grafos de Conhecimento para Soluções de Segurança do Mundo Real

> **Tradução integral em português** de *"Practical Applications of Cyber security: A Research Paper on Knowledge Graphs for Real-World Security Solutions"*, Bonagiri, Priyadharshini, PanneerSelvi, Sahitya, Swamy, Varalakshmi (2024), 4th Asian Conference on Innovation in Technology (ASIANCON), IEEE.
>
> **PDF original:** [`docs/pdfs/Practical_Applications_of_Cyber_security_A_Research_Paper_on_Knowledge_Graphs_for_Real-World_Security_Solutions.pdf`](../pdfs/) — 6 páginas
> **DOI:** 10.1109/ASIANCON62057.2024.10837769
> **Status:** ✅ Tradução completa
> **Tier:** 2 (Importante — KG mais recente em cibersegurança; competidor direto da nossa contribuição em construção de KG)

---

## Autores

- **Krishna Bonagiri** — Vice-Presidente de Engenharia, Quadrant Technologies, EUA
- **L. Priyadharshini** — Department of Saveetha School of Law, Saveetha Institute of Medical and Technical Science, Chennai, Índia
- **R. PanneerSelvi** — Department of CSE, Vel Tech Rangarajan Dr. Sagunthala R&D Institute of Science and Technology, Chennai, Índia
- **Pinnamaraju Sahitya** — Department of ECE, MLR Institute of Technology, Dundigal Hyderabad, Índia
- **Hemanth Swamy** — Senior Software Engineer, Motorola Solutions
- **Varalakshmi P.** — Department of AI & DS, Dhanalakshmi College of Engineering, Chennai, Índia

---

## Resumo

O reino da cibersegurança está repleto de atividades de ciberataque intrincadas e em constante evolução, apresentando obstáculos formidáveis para profissionais de cibersegurança. Ao incorporar grafos de conhecimento neste campo, pode-se ajudar com identificação de ameaças e consciência situacional visualizando o intrincado cenário de cibersegurança. Mas criar esses grafos de conhecimento pode adicionar ruído e conflitos, o que pode resultar em conclusões incorretas. O objetivo deste trabalho é abordar as dificuldades envolvidas em criar e avaliar grafos de conhecimento de cibersegurança. Para oferecer um *framework* mais flexível adequado para diferentes propriedades de dados, melhoramos a ontologia atual de cibersegurança e montamos um *dataset* de grafo de conhecimento de cibersegurança (CS13K). O grafo de conhecimento de cibersegurança é feito com **Neo4j**. Adicionalmente, desenvolvemos um modelo **AttTucker** para avaliar qualidade do grafo de conhecimento, baseado em arquitetura Transformer. Para reduzir a dimensionalidade dos *embeddings* de conhecimento e capturar ligações latentes entre entidades e relações, este modelo usa múltiplas cabeças de auto-atenção, produzindo resultados de avaliação que são similares aos de *embedding* de maior dimensionalidade. Adicionalmente, no procedimento de avaliação baseado em AttTucker, incorporamos dados de nível de caminho de entidades de grafo de conhecimento. Nosso método melhora significativamente o valor F1 e acurácia, superando modelos atuais em tarefas de avaliação de qualidade de grafo de conhecimento, segundo uma investigação experimental usando *datasets* de cibersegurança e gerais.

## Palavras-chave

Grafo de conhecimento, Cibersegurança, Construção de ontologia, Mecanismo de atenção, Avaliação de qualidade.

---

## I. Introdução

Uma infinidade de conhecimento de cibersegurança inestimável se espalhou pela Internet nos últimos anos, dispersa entre numerosas plataformas como bases de dados de vulnerabilidade, fóruns de segurança e arquivos de informação. Apesar de sua abundância, esses fragmentos de conhecimento de cibersegurança permanecem amplamente desconectados, falhando em alavancar o potencial completo de *insights* de *big data*. Adicionalmente, a natureza em constante evolução das ciberameaças demanda mais que mecanismos passivos de defesa; análise proativa de dados de cibersegurança tornou-se imperativa.

Entram os grafos de conhecimento, aclamados como uma solução potente em meio à complexidade e diversidade de ciberameaças. Esses grafos servem como repositórios dinâmicos de conhecimento interconectado, automaticamente revelando associações entre entidades de ameaça, facilitando consciência situacional de cibersegurança, avaliação de risco, e até auxiliando em visualização de caminho de ataque durante análise forense. Minerando essas associações, profissionais de cibersegurança ganham *insights* mais profundos sobre vulnerabilidades e vetores de ataque.

Apesar das ontologias de propósito geral existentes, sua aplicabilidade frequentemente fica aquém devido a focos variados em elementos de cibersegurança. Para preencher essa lacuna, **apresentamos uma ontologia de cibersegurança nova adaptada para acomodar fontes diversas de dados e apoiar o desenvolvimento de grafos de conhecimento abrangentes e precisos.**

Garantir a integridade do conteúdo desses grafos é primordial. Imprecisões nesses grafos têm o potencial de se espalhar para aplicações mais avançadas, resultando em inferência e julgamento errôneos. Métodos tradicionais de inspeção manual são impraticáveis para repositórios de conhecimento em larga escala, sublinhando a necessidade de **técnicas automatizadas de avaliação de qualidade**.

---

## II. Revisão da Literatura

Pesquisa em *datasets* de grafo de conhecimento de cibersegurança tem sido escassa porque dados de cibersegurança são muito sensíveis e especializados, e porque há poucos *corpora* especializados em larga escala. Robert et al. usaram técnicas de anotação automática para criar um *dataset* de reconhecimento de entidade de cibersegurança. Eles usaram o esquema de rotulagem "BIO" e 15.192 enunciados de cibersegurança. Este *dataset* de 498.000 palavras gerou uma pontuação F1 de **75,05%** usando Bi-LSTM-CRF.

**Rastogi et al. coletaram dados de 1.100 relatórios de inteligência de ameaças usando métodos automatizados de extração para gerar o *dataset* de grafo de conhecimento de malware MT40K. Há 40.000 triplas neste *dataset*, consistindo de 27.354 itens e 34 tipos diferentes de relações.** No entanto, devido à extração automatizada, a acurácia das triplas do *dataset* não é ótima.

O passo fundacional na criação de um grafo de conhecimento de cibersegurança é criar uma ontologia. Mas porque foram projetadas com diferentes prioridades em mente, ontologias atuais de cibersegurança frequentemente fornecem dificuldades para integração completa entre muitas fontes de dados. Uma ontologia para cibersegurança foi criada por **Iannacone et al. e inclui 115 propriedades e 15 categorias de entidade**. A **Universal Cybersecurity Ontology (UCO)**, que vincula vários padrões de cibersegurança e ontologias incluindo CVE, CCE, CVSS e outros, foi posteriormente desenvolvida por Syed et al. construindo sobre este trabalho. O formato STIX é compatível com a UCO. **As oito principais categorias de entidade que compõem UCO são Attacker, Attack-Pattern, Consequences e Indicator.**

A **Security Asset Vulnerability Ontology (SAVO)** foi desenvolvida por Vorobiev et al. para caracterizar as características, ideias e conexões entre ameaças de rede, vulnerabilidades e riscos. A adição de Pingle et al. de classes cruciais incluindo Campaign, Tool e Course-of-Action, bem como o alargamento de relações, melhorou a ontologia de cibersegurança UCO.

---

## III. Implementação do Sistema

Sistemas inteligentes de busca e recomendação frequentemente empregam grafos de conhecimento gerais. Instâncias notáveis de repositórios genéricos de conhecimento são Wikidata, YAGO, DBpedia e Freebase. Inversamente, dentro de domínios particulares de conhecimento, **grafos de conhecimento específicos de domínio** destacam conhecimento especializado e atendem a necessidades particulares de consulta e análise.

Cygraph ajuda com coisas como identificar superfícies de ataque e descobrir como defender contra ataques para proteger ativos importantes.

O propósito da **avaliação de qualidade de grafo de conhecimento** é avaliar o conteúdo de conhecimento de um grafo de conhecimento quantitativamente. Estratégias de detecção que dependem dos dados internos do grafo de conhecimento usualmente modelam o grafo e identificam relacionamentos entre itens usando abordagens de *random walk*. Uma alta probabilidade de ligações entre coisas no grafo de conhecimento é mostrada por múltiplos caminhos entre eles. Para encontrar entidades e relações falsas, vários pesquisadores usaram técnicas de aprendizado de representação de conhecimento. Sua habilidade de capturar tanto informação estrutural local quanto global para avaliação de confiança de tripla foi mostrada por achados experimentais.

Usando o *dataset* FB15K, **Jia et al. avaliaram com sucesso a confiança de triplas em grafos de conhecimento** avaliando a confiança de tripla das perspectivas de entidade, relação e global. Usando tecnologia de aprendizado de máquina automatizado (AutoML), Zhang et al. criaram sistemas de pontuação apropriados para o problema de classificação de tripla de grafo de conhecimento.

### 📌 Figura 1: Estrutura para Construção de Grafos de Conhecimento de Cibersegurança e Avaliação de Sua Qualidade

> **Descrição:** Diagrama do *pipeline* completo: fontes de dados → extração de informação → construção da ontologia → grafo de conhecimento em Neo4j → modelo AttTucker para avaliação de qualidade.
>
> 📌 *Ver Figura 1 na página 2 do PDF original.*

---

## IV. Dataset

Os aspectos técnicos e sociológicos de incidentes de ciberataque são apresentados em relatórios de ameaça de cibersegurança como texto não-estruturado. Extrair informação importante desses relatórios é o primeiro passo na criação de um grafo de conhecimento de cibersegurança, e não é uma tarefa fácil. **Os *datasets* de grafo de conhecimento de cibersegurança agora disponíveis como recursos de código aberto foram coletados via extração automática, e como resultado, a acurácia das triplas é baixa, não refletindo o estado real da cibersegurança.**

Para superar esse problema, pessoal de segurança com forte expertise no assunto de cibersegurança montou um *dataset* manualmente. **Este *dataset* é conhecido como CS13K (Cybersecurity 13K).** Eles continuarão atualizando CS13K para refletir o estado real de cibersegurança e ampliar seu alcance.

**As doze categorias de relações são:**
1. *indicate* (indica)
2. *mitigates* (mitiga)
3. *targets* (visa)
4. *use* (usa)
5. *associate* (associa)
6. *belongTo* (pertence a)
7. *cause* (causa)
8. *exploits* (explora)
9. *hasAttackLocation* (tem localização de ataque)
10. *hasAttackTime* (tem tempo de ataque)
11. *hasCharacteristics* (tem características)
12. *hasVulnerability* (tem vulnerabilidade)

**Com 13.027 triplas no total e documentos e palavras correspondentes, o *dataset* serve como uma fonte de dados para projetos de pesquisa futuros em poucos campos.**

Exemplos de relacionamentos com a notação "*belongTo*" incluem aqueles entre Threat Actor e Hacker Group, Malware e Malware Family, software prejudicial e seu tipo, e vulnerabilidades e seu tipo. "*Cause*" se refere ao relacionamento entre vulnerabilidades e as consequências de um ataque, o relacionamento entre sistemas operacionais, software e hardware. **Até onde sabemos, nenhum modelo tentou avaliar a qualidade do grafo de conhecimento enquanto sendo limitado por *embeddings* de baixa dimensionalidade.**

Enquanto os modelos atuais para representação de conhecimento performaram excepcionalmente bem com *embeddings* de alta dimensionalidade em muitas tarefas *downstream*, eles ainda performam pobremente com *embeddings* de baixa dimensionalidade, o que apresenta questões de escalabilidade em *datasets* em larga escala.

### Sobre Extração de Conhecimento

Dois métodos primários de extração de conhecimento:

1. **Engenharia de Conhecimento (baseada em regras):** depende fortemente de regras de extração. Pinkston et al. concebeu um sistema alavancando ontologia para extrair informação de ataque. Rehman e Mustafa similarmente empregou um sistema baseado em regras para extrair informação de vulnerabilidade de descrições de texto, utilizando pontuações TFIDF. Lowis e Accorsi empregou casamento de string em CVEs.

2. **Aprendizado de Máquina:** um modelo de extração de informação é primeiramente treinado completamente em um *dataset* grande.

### 📌 Figura 2 e 3: Arquitetura da Base de Conhecimento e Ontologia de Cibersegurança

> **Descrição:** Figura 2 mostra três ontologias separadas (Attack, Vulnerability, Assets) com DDoS como sub-conceito. Figura 3 mostra a ontologia de cibersegurança detalhada com classes e relacionamentos.
>
> 📌 *Ver Figuras 2 e 3 na página 3 do PDF original.*

A arquitetura é composta de três ontologias separadas:
- **Attack** (ataque)
- **Vulnerability** (vulnerabilidade)
- **Assets** (ativos)

**O modelo completo da base de conhecimento de cibersegurança proposto neste trabalho é organizado em torno de cinco componentes-chave: ideia, instância, relação, propriedades e regras.**

---

## V. Resultados e Discussão

Para treinar NER1, inicialmente, escolheram atributos sem *gazettes*. A performance média de reconhecimento de NER1 para o objeto 'consequence' mostra uma precisão notavelmente alta. Adicionalmente, a medida F1 mostra que as taxas de reconhecimento de "vulnerability" e "software" são positivamente correlacionadas e maiores que as de outros tipos de entidade.

### Tabela I: Resultados de Reconhecimento para NER1

| Entidade | Precisão | Recall | F1 |
|---|---|---|---|
| Vulnerability | 0.835 | 0.701 | 0.721 |
| OS | 0.781 | 0.702 | 0.719 |
| **Total** | **0.762** | **0.751** | **0.716** |
| Attack | 0.851 | 0.601 | 0.703 |
| Software | 0.697 | 0.802 | 0.757 |

### Tabela II: Resultados de Reconhecimento de NER2 e NER3

| Modelo | Entidade | Precisão | Recall | F1 |
|---|---|---|---|---|
| **NER2 (clean Gazette)** | OS | 0.602 | 0.821 | 0.754 |
| | Attack | 0.838 | 0.512 | 0.632 |
| | Vulnerability | 0.702 | 0.578 | 0.635 |
| | Software | 0.753 | 0.789 | 0.783 |
| | **Total** | **0.752** | **0.741** | **0.748** |
| **NER3 (sloppy Gazette)** | Attack | 0.821 | 0.483 | 0.612 |
| | OS | 0.786 | 0.851 | 0.811 |
| | Vulnerability | 0.726 | 0.587 | 0.639 |
| | Software | 0.821 | 0.789 | 0.801 |
| | **Total** | **0.801** | **0.751** | **0.785** |

NER3 supera NER2 em reconhecimento de 'software' e 'OS', sugerindo que a opção *sloppy Gazette* contribui para melhor reconhecimento de entidades relacionadas à cibersegurança. No entanto, tanto NER2 quanto NER3 ainda exibem medidas F1 baixas para 'consequence' e 'mean', ambas caindo abaixo de 70%.

### 📌 Figuras 4-9: Resultados de Reconhecimento

> **Descrição:** Gráficos comparativos NER1/NER2/NER3 com curvas de precisão, recall e F1 para diferentes entidades.
>
> 📌 *Ver Figuras 4-9 nas páginas 4-5 do PDF original.*

---

## VI. Conclusão

Este artigo representa uma contribuição significativa à busca contínua por soluções efetivas de cibersegurança, apresentando um *framework* abrangente para construir sistemas de conhecimento baseados em ontologia adaptados às intrincações do domínio de cibersegurança. Em seu núcleo, o *framework* gira em torno do conceito de vulnerabilidade, reconhecendo-o como um pivô central em torno do qual ciberameaças giram e estratégias defensivas se aglutinam.

O desenvolvimento da ontologia de cibersegurança representa um passo fundamental em direção a melhorar nosso entendimento de ciberameaças e vulnerabilidades. Organizando conhecimento em um *framework* estruturado de conceitos, entidades e relacionamentos, a ontologia fornece uma linguagem comum para *stakeholders* comunicarem e colaborarem efetivamente.

Em conclusão, o desenvolvimento de um sistema de conhecimento baseado em ontologia para cibersegurança representa um passo crítico em direção a fortalecer defesas digitais e salvaguardar ativos críticos em um mundo cada vez mais interconectado.

---

## VII. Escopo Futuro

- **Inteligência de Ameaça e Compartilhamento de Informação:** sistemas de conhecimento baseados em ontologia podem facilitar agregação, análise e disseminação de inteligência de ameaça entre fronteiras organizacionais.
- **Educação e Treinamento em Cibersegurança:** podem servir como ferramentas poderosas para educação e treinamento.
- **Gerenciamento de Risco Cibernético e Conformidade:** podem assistir organizações em gerenciar risco cibernético e garantir conformidade com requisitos regulatórios.

---

## Referências (32 total)

Mais relevantes para nosso paper:

- **[10] Iannacone M, Bohn S, Nakamura G, Gerth J, Goodall J (2015)** — Developing an ontology for cyber security knowledge graphs. 10th Annual Cyber and Information Security Research Conference.
- **[8] Rastogi N, Dutta S, Christian R, Gridley J, Zaki M, Gittens A (2021)** — Predicting malware threat intelligence using KGs. arXiv:2102.05571.
- **[12] Vorobiev A, Bekmamedova N (2007)** — An ontological approach applied to information security and trust. ACIS 2007.
- **[13] Pingle A, Piplai A, Mittal S, Joshi A, Holt J, Zak R (2019)** — Relext: relation extraction using deep learning approaches for cybersecurity knowledge graph improvement. *2019 IEEE/ACM International Conference on Advances in Social Networks Analysis and Mining*.
- **[25] Harley E, Purdy S, Limiero M, Lu T, Mathews W (2018)** — CyGraph: big-data graph analysis for cybersecurity and mission resilience. MITRE.

> Lista completa nas páginas 5-6 do [PDF original](../pdfs/Practical_Applications_of_Cyber_security_A_Research_Paper_on_Knowledge_Graphs_for_Real-World_Security_Solutions.pdf).

---

## Resumo dos pontos-chave para o nosso paper

### Por que este paper importa para nós

**Bonagiri 2024 é o trabalho mais recente em KG-cibersegurança no escopo da literatura revista** (até a data da nossa elaboração). É a referência canônica do estado-da-arte atual em construção de KG de cibersegurança.

### Como nosso paper se diferencia

| Dimensão | Bonagiri 2024 | Nosso Paper (http-session) |
|---|---|---|
| **Fonte de dados para KG** | Texto extraído de relatórios CTI (relatórios de ameaça, *blogs*, fóruns) | Eventos de tráfego HTTP em tempo de execução |
| **Tipo de KG** | KG estático construído offline (CS13K — 13.027 triplas) | KG dinâmico em tempo de execução |
| **Objeto de avaliação** | Qualidade do KG construído (via AttTucker baseado em Transformer) | Performance de detecção de ataques (via regras semânticas) |
| **Classes principais** | Attack, Vulnerability, Assets, Threat Actor, Malware | ApplicationSession (entidade de primeira classe), Endpoint, Identity, BotBehavior, três especializações de ataque |
| **Relação "sessão"** | Ausente — não modelam sessão | Central — sessão como entidade de primeira classe |
| **Foco de raciocínio** | Avaliação de qualidade de triplas | Detecção de campanhas coordenadas via cross-session reasoning |

### Citação no nosso artigo

Já citado em `\cite{bonagiri2024practical}`:
- **§1.2 gap 3:** "KGs construídos estaticamente a partir de texto, não como runtime"
- **§1.4 Contribuição 2:** "em contraste com grafos de cibersegurança anteriores"
- **§2.1 (Grafos de Conhecimento em Cibersegurança):** quando desenvolvermos Related Work, será referência primária do estado-da-arte recente

### O dataset CS13K como benchmark de comparação

CS13K (13.027 triplas, 12 tipos de relação) é o *dataset* mais recente de cibersegurança-KG. Se nosso paper precisar de comparação numérica de tamanho/cobertura, podemos referenciar CS13K como ordem de magnitude. **Importante:** CS13K **não** inclui sessão como tipo de entidade — confirma nossa novidade.

### Admissão dos autores que sustenta nosso argumento

> *"Os datasets de grafo de conhecimento de cibersegurança agora disponíveis como recursos de código aberto foram coletados via extração automática, e como resultado, a acurácia das triplas é baixa, não refletindo o estado real da cibersegurança."*

Esta admissão dos próprios autores justifica nossa escolha de operar sobre **eventos de tráfego estruturados** (não sobre texto extraído de relatórios), evitando o problema de baixa acurácia de extração automatizada.
