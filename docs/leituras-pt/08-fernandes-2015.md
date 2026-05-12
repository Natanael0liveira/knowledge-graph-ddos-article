# Sistema Autônomo de Detecção de Anomalias Baseado em Perfil Usando Análise de Componentes Principais e Análise de Fluxo

> **Tradução em português** de *"Autonomous profile-based anomaly detection system using principal component analysis and flow analysis"*, Fernandes Jr., Rodrigues, Proença Jr. (2015), Applied Soft Computing 34:513-525.
>
> **PDF original:** [`docs/pdfs/1-s2.0-S1568494615003191-main.pdf`](../pdfs/1-s2.0-S1568494615003191-main.pdf) — 13 páginas
> **DOI:** 10.1016/j.asoc.2015.05.019
> **Status:** ✅ Tradução resumida (apenas seções essenciais — Tier 3)
> **Tier:** 3 (Baseline — referência metodológica para perfilamento estatístico)

---

## Autores

- **Gilberto Fernandes Jr.** (*correspondência*: gil.fernandes6@gmail.com) — Instituto de Telecomunicações, University of Beira Interior (UBI), Covilhã, Portugal
- **Joel J. P. C. Rodrigues** — UBI / University of Fortaleza (UNIFOR), Fortaleza, Brasil
- **Mario Lemes Proença Jr.** — Computer Science Department, State University of Londrina (UEL), Londrina, Brasil

---

## Resumo

Diferentes técnicas e métodos têm sido amplamente usados na área de detecção automática de anomalias em redes de computador. Ataques, problemas e falhas internas, quando não detectados cedo, podem prejudicar gravemente um sistema de Rede inteiro. Assim, um sistema autônomo de detecção de anomalias baseado no método estatístico **análise de componentes principais (PCA)** é proposto. Esta abordagem cria um perfil de rede chamado **Digital Signature of Network Segment using Flow Analysis (DSNSF)** que denota o comportamento normal predito de uma atividade de tráfego de rede através de análise de dados históricos. Essa assinatura digital é usada como um limiar para detecção de anomalia de volume para detectar disparidades na tendência normal de tráfego.

O sistema proposto usa **sete atributos de fluxo de tráfego**: bits, pacotes e número de fluxos para detectar problemas, e endereços IP de origem e destino e Portas, para fornecer ao administrador de rede informação necessária para resolvê-los. Via técnicas de avaliação realizadas neste artigo usando dados de tráfego de rede reais, resultados mostraram boa predição de tráfego pelo DSNSF e geração encorajadora de falso alarme e acurácia de detecção no esquema de detecção usando limiares.

## Palavras-chave

Gerenciamento de rede, Caracterização de tráfego, Detecção de anomalia, Análise de Componentes Principais, Fluxos.

---

## 1. Introdução

Hoje em dia, todos os tipos de redes são alvos diários de ataques e atividades maliciosas que buscam interromper ou desabilitar tráfego e serviços de Internet, ameaçando sua disponibilidade e operabilidade. Por exemplo, **ataques DDoS podem levar a uma sobrecarga séria de servidor**, congestionando uma rede com tráfego e requisições indesejadas. *Worms*, distribuição de *spam*, *spoofing* e cibercrime são outros exemplos de ameaças que podem prejudicar redes de computador. No entanto, não são apenas ataques que afetam a operação normal da rede. Como redes estão crescendo em tamanho e complexidade, problemas como falha de servidor, *bugs*, congestionamento de *link*, falhas de *software* e aleatoriedade de tráfego podem gerar ruído nos padrões estatísticos do fluxo da rede.

**Detecção de anomalia pode ser classificada de duas maneiras:**

1. **Baseada em assinatura** (*signature-based*), na qual conhecimento prévio sobre as características de cada tipo de anomalia é usado. Tem uma desvantagem clara: é pré-requisito que assinaturas de anomalia sejam conhecidas com antecedência, dificultando o reconhecimento de novas anomalias. Também, **métodos baseados em assinatura podem ser evitados por fontes maliciosas alterando assinaturas de anomalia**.

2. **Baseada em perfil** (*profile-based*), que apresenta um histórico do comportamento normal da rede através de um perfil de rede e trata qualquer atividade que desvie dele como uma possível intrusão. Cria um perfil de *baseline* da atividade normal da rede, eliminando a necessidade de conhecimento prévio sobre a natureza e propriedades de anomalias.

O sistema proposto neste artigo é chamado **PCADS-AD (principal component analysis for digital signature and anomaly detection)**, e é dividido em dois passos: caracterização de tráfego e detecção de anomalia.

### Contribuições

- Gerar uma assinatura digital usando análise de componentes principais de uma maneira incomum, para descrever o comportamento normal de um segmento de rede.
- Usar essa assinatura como base para detecção de anomalia.
- Avaliar o sistema proposto usando dados reais de uma grande rede universitária.

---

## 2. Trabalhos Relacionados

Existem muitos tipos diferentes de métodos de detecção de anomalia e intrusão que usam todos os tipos de algoritmos e técnicas:

- **Xu (2014)** — Detecção sequencial baseada em aprendizado por diferença temporal (TD).
- **Lin et al.** — Combina SVM, Árvore de Decisão e Simulated Annealing.
- **Lakhina et al.** (pioneiro) — PCA para separar tráfego em subespaços normal e anômalo.
- **Pascoal et al.** — PCA robusto combinado com seleção robusta de característica.

### Tabela 1 (resumida): Métodos de Detecção de Anomalia Discutidos

| Ref | Técnicas | Dados | Anomalias | Validação |
|---|---|---|---|---|
| [14] | TD learning + Markov sequencial | *Hosts* com *system call data* | Ciberataques multi-estágio | Curva ROC |
| [15] | SVM + DT + SA | KDD'99 | Probe, DoS, U2R, R2L | Acurácia |
| [16] | *Flow-based sampling* + CPD | Rede de *campus* | DDoS | Variável Xn |
| [20] | PCA (Lakhina) | Sprint-1, Abilene | Anomalias sintéticas | Taxa de detecção, FPR |
| [22] | Sensibilidade do PCA | Abilene, Geant | Anomalias suspeitas PCA | Total detecções, FP |
| [23] | *Sketches* + entropia + PCA | MAWI | 22 categorias (TCP SYN flood, Port scan) | TPR, FPR, Acc, F1, ROC |

---

## 3. Sistema Proposto: PCADS-AD

### 3.1. Caracterização de Tráfego

Sete atributos de fluxo IP:

**Quantitativos** (3): bits, pacotes, número de fluxos transmitidos por segundo.

**Qualitativos** (4): endereços IP de origem e destino, portas TCP/UDP de origem e destino.

A caracterização é realizada usando PCA como mecanismo para analisar dados históricos de entrada da atividade de rede, identificar os intervalos de tempo de tráfego mais relevantes entre o conjunto de dados, e então reduzi-los para que esse novo conjunto possa eficientemente representar o comportamento regular de um segmento de rede.

### 3.2. Detecção de Anomalia

Eventos anormais são detectados com base no DSNSF, que atua como limiar para gerar alarmes. Para minimizar geração de falsos alarmes, **bandas de confiança** são produzidas para o DSNSF, restringindo um intervalo onde desvios são considerados normais.

A análise é multi-dimensional: certos tipos de anomalias causam variação em mais de um atributo de fluxo. Para DoS/DDoS, os atributos afetados são pacotes e número de fluxos, enquanto uma anomalia *Flash Crowd* afeta bits, pacotes e número de fluxos.

### 3.3. PCA — Formulação Matemática

Dada uma matriz de dados $X$ com $m$ observações e $n$ variáveis, PCA computa autovetores e autovalores da matriz de covariância de $X$. Os autovetores formam uma nova base ortogonal — os **componentes principais** — ordenados por autovalor decrescente. Os primeiros $k$ componentes capturam a maior parte da variância dos dados originais.

---

## 4. Resultados

### Ambiente Experimental

Dados de tráfego reais coletados da rede da Universidade Estadual de Londrina (UEL), Brasil.

### Métricas

- **Mean Absolute Percentage Error (MAPE)** — para avaliação da predição do DSNSF.
- **True Positive Rate (TPR)** e **False Positive Rate (FPR)** — para detecção de anomalia.

### Achados-Chave

- **A predição de tráfego pelo DSNSF teve MAPE baixo** em todos os atributos (bits, pacotes, fluxos), mostrando que PCA captura bem o padrão normal de uso da rede.
- **Acurácia de detecção encorajadora** com **taxa de falsos alarmes baixa** ao usar limiares baseados em bandas de confiança do DSNSF.
- O sistema fornece informação qualitativa sobre o intervalo de tempo anômalo, ajudando o administrador de rede a encontrar a fonte de problemas, os alvos e sua magnitude.

---

## 5. Conclusões

Este artigo propôs um sistema autônomo de detecção de anomalia chamado PCADS-AD baseado em PCA aplicado a sete atributos de fluxo IP. O sistema cria o DSNSF como perfil de comportamento normal de tráfego de rede e o usa como limiar para detecção de anomalia volumétrica.

**Vantagens:**
- Captura padrão multi-dimensional de tráfego.
- Não requer conhecimento prévio de anomalias (perfil-based, não signature-based).
- Bandas de confiança reduzem falsos alarmes.
- Fornece informação qualitativa para o administrador.

**Limitações implícitas:**
- Detecção volumétrica — não modela camada de aplicação.
- Sem semântica de sessão — agrega tráfego em janelas temporais.
- Sem explicabilidade ontológica — saída é alarme com magnitude, não cadeia de evidência.

---

## Referências

Mais relevantes:

- **[20] Lakhina A. et al. (2004)** — *Diagnosing network-wide traffic anomalies*. SIGCOMM. (Pioneiro de PCA para detecção de anomalia em rede)
- **[22] Ringberg H. et al. (2007)** — Sensibilidade do PCA em detecção de anomalia.
- **[23] Brauckhoff D. et al.** — *Sketches* + entropia + PCA.

> Lista completa de 50+ referências no [PDF original](../pdfs/1-s2.0-S1568494615003191-main.pdf).

---

## Resumo dos pontos-chave para o nosso paper

### Por que este paper importa para nós

Fernandes 2015 é o **baseline estatístico de perfilamento** no nosso §4.4 Baselines. Representa a abordagem clássica de detecção de anomalia volumétrica via PCA sobre estatísticas de fluxo.

### Como nosso paper se diferencia

| Dimensão | Fernandes 2015 | Nosso paper |
|---|---|---|
| **Granularidade** | NetFlow agregado (bits, pacotes, fluxos por segundo) | HTTP por sessão |
| **Tipo de anomalia detectada** | Volumétrica (Camada 3/4) | Camada 7 (semântica) |
| **Modelo de sessão** | Não tem — agrega por intervalo de tempo | Sessão é entidade ontológica de primeira classe |
| **Representação** | Vetor de 7 atributos numéricos | Grafo de conhecimento com relações tipadas |
| **Saída** | Alarme + magnitude | Veredicto + cadeia de evidência semântica |

### Citação no nosso artigo

Já citado em `\cite{fernandes2015autonomous}`:

- **§1.1 Contexto:** baseline estatístico
- **§1.4 Contribuição 3:** "contrastando com detectores anteriores baseados em features agregadas que produzem rótulos binários por sessão"
- **§4.4 Baselines:** aproximação direta — PCA sobre features agregadas é nosso *baseline* estatístico
- **§4.5 Análise de Ablação:** comparamos nosso arcabouço sem ontologia vs PCA puro à la Fernandes 2015
