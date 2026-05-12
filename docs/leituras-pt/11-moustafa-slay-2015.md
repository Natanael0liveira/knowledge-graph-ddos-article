# UNSW-NB15: Um Conjunto de Dados Abrangente para Sistemas de Detecção de Intrusão de Rede

> **Tradução em português** de *"UNSW-NB15: A Comprehensive Data Set for Network Intrusion Detection Systems (UNSW-NB15 Network Data Set)"*, Moustafa e Slay (2015), Military Communications and Information Systems Conference (MilCIS), IEEE.
>
> **PDF original:** [`docs/pdfs/UNSW-NB15_a_comprehensive_data_set_for_network_intrusion_detection_systems_UNSW-NB15_network_data_set.pdf`](../pdfs/) — 6 páginas
> **DOI:** 10.1109/MilCIS.2015.7348942
> **Status:** ✅ Tradução resumida (apenas seções essenciais — Tier 4)
> **Tier:** 4 (Opcional — paper de *dataset*, não usaremos UNSW-NB15 neste paper)

---

## Autores

- **Nour Moustafa** (correspondência: nour.abdelhameed@student.adfa.edu.au)
- **Jill Slay** (j.slay@adfa.edu.au)

School of Engineering and Information Technology, University of New South Wales at the Australian Defence Force Academy, Canberra, Austrália.

---

## Resumo

Um dos principais desafios de pesquisa neste campo é a indisponibilidade de um conjunto de dados abrangente baseado em rede que possa refletir cenários modernos de tráfego de rede, vastas variedades de intrusões de pegada baixa e informação profunda estruturada sobre tráfego de rede. Avaliando esforços de pesquisa de sistemas de detecção de intrusão de rede, os conjuntos de dados *benchmark* KDD98, KDDCUP99 e NSLKDD foram gerados há uma década. No entanto, numerosos estudos atuais mostraram que para o ambiente atual de ameaça de rede, **esses conjuntos de dados não refletem inclusivamente tráfego de rede e ataques modernos de pegada baixa**. Contrariando os desafios de indisponibilidade de conjunto de dados *benchmark* de rede, este artigo examina a criação do **conjunto de dados UNSW-NB15**.

Este conjunto de dados tem um híbrido do tráfego normal moderno real e das atividades de ataque sintetizadas contemporâneas do tráfego de rede. Métodos existentes e novos são utilizados para gerar as características do conjunto de dados UNSW-NB15.

## Palavras-chave

Conjunto de dados UNSW-NB15; NIDS; ataques de pegada baixa; arquivos pcap; *testbed*.

---

## I. Introdução

Atualmente, devido ao crescimento massivo em redes e aplicações de computador, muitos desafios surgem para pesquisa de cibersegurança. Intrusões/ataques podem ser definidos como um conjunto de eventos que são capazes de comprometer os princípios de sistemas computacionais, e.g. disponibilidade, autoridade, confidencialidade e integridade. Sistemas *firewall* não podem detectar ambientes de ataque modernos e não são capazes de analisar pacotes de rede em profundidade.

Um Sistema de Detecção de Intrusão de Rede (NIDS) monitora fluxo de tráfego de rede para identificar ataques. NIDS são classificados em **baseados em uso indevido/assinatura e baseados em anomalia**. Os baseados em assinatura casam a existência de ataques conhecidos para detectar intrusões. No entanto, no baseado em anomalia, um perfil normal é criado a partir do comportamento normal da rede, e qualquer desvio disso é considerado como ataque.

A efetividade de NIDS é avaliada com base em seu desempenho para identificar ataques que requer um conjunto de dados abrangente que contém comportamentos normais e anormais. *Datasets benchmark* antigos são **KDDCUP 99** e **NSLKDD**, que foram amplamente adotados para avaliar desempenho NIDS. **É percebido através de vários estudos que avaliar um NIDS usando esses conjuntos de dados não reflete desempenho de saída realista devido a várias razões.**

### Razões pelas quais KDDCUP99 e NSLKDD são inadequados

1. **KDDCUP 99 contém um número tremendo de registros redundantes** no conjunto de treinamento. Os registros redundantes afetam os resultados de viés de detecção em direção aos registros frequentes.
2. Existem **múltiplos registros faltantes** que são um fator em mudar a natureza dos dados.
3. **NSLKDD não é uma representação abrangente de um ambiente moderno de ataque de pegada baixa.**

As razões acima motivaram um desafio sério para o grupo de pesquisa de cibersegurança no *Australian Centre for Cyber Security* (ACCS).

---

## II. O Objetivo e Orientação de um Conjunto de Dados NIDS

Um conjunto de dados NIDS pode ser conceitualizado como dados relacionais. Entrada para um NIDS é um conjunto de registros de dados. Cada registro consiste de atributos de diferentes tipos de dados (e.g., binário, *float*, nominal e inteiro). O rótulo atribui a cada registro dos dados, ou normal é 0 ou anormal é 1.

---

## III. Críticas aos Conjuntos de Dados Existentes

### A. KDDCup99

Gerado a partir do DARPA98, o KDDCUP99 contém recursos extraídos divididos em três grupos de **características intrínsecas, características de conteúdo e características de tráfego**. Registros de ataque são categorizados em quatro vetores: **DoS, Probe, U2R e R2L**. O conjunto de treinamento incluiu 22 tipos de ataque e os dados de teste continham 15 tipos de ataque.

**Três desvantagens principais:**

1. Pacotes de dados de cada ataque têm um valor de tempo de vida (TTL) de 126 ou 253, enquanto os pacotes do tráfego têm principalmente um TTL de 127 ou 254.
2. A distribuição de probabilidade do conjunto de teste é diferente da do conjunto de treinamento.
3. O conjunto de dados não é uma representação abrangente de projeções de ataque de pegada baixa recentemente reportadas.

### B. NSLKDD

Uma versão atualizada do conjunto de dados KDD, com três objetivos:

1. Remover a duplicação de registros
2. Selecionar variedade de registros de diferentes partes do original
3. Eliminar o problema de desbalanceamento entre os números de registros

A principal desvantagem é que **não representa cenários modernos de ataque de pegada baixa**.

---

## IV. O Conjunto de Dados UNSW-NB15

### A. Configuração do Testbed da Ferramenta IXIA

O gerador de tráfego **IXIA PerfectStorm** é configurado com três servidores virtuais. Servidores 1 e 3 são configurados para tráfego normal, enquanto servidor 2 forma atividades anormais/maliciosas. As atividades anormais são alimentadas pelo CVE site para representação real de um ambiente de ameaça moderno.

A **simulação foi de 16 horas em 22 de janeiro de 2015 e 15 horas em 17 de fevereiro de 2015 para capturar 100 GBs**. O IXIA é configurado para gerar 1 ataque/segundo (primeira simulação) e 10 ataques/segundo (segunda simulação).

### 📌 Figuras 1 e 2: Visualização do Testbed e Transações Concorrentes

> **Descrição:** Figura 1 mostra topologia: gerador IXIA → 3 servidores virtuais (normal/normal/anormal) → 2 roteadores → firewall → tcpdump captura. Figura 2 mostra gráficos de transações concorrentes durante simulação em 16h e 15h.
>
> 📌 *Ver Figuras 1 e 2 nas páginas 2-3 do PDF original.*

### B. Estatísticas do Conjunto de Dados

### Tabela I: Estatísticas do Dataset

| Característica Estatística | 16 horas | 15 horas |
|---|---|---|
| Número de fluxos | 987.627 | 976.882 |
| Bytes de origem | 4.860.168.866 | 5.940.523.728 |
| Bytes de destino | 44.743.560.943 | 44.303.195.509 |
| Pacotes de origem | 41.168.425 | 41.129.810 |
| Pacotes de destino | 53.402.915 | 52.585.462 |
| TCP | 771.488 | 720.665 |
| UDP | 301.528 | 688.616 |
| ICMP | 150 | 374 |
| Outros | 150 | 374 |
| **Registros normais** | **1.064.987** | **1.153.774** |
| **Registros de ataque** | **22.215** | **299.068** |
| IPs únicos de origem | 40 | 41 |
| IPs únicos de destino | 44 | 45 |

### C. Arquitetura

Quando a simulação está executando no *testbed*, os arquivos *pcap* são gerados via tcpdump. As características são extraídas via **Argus** e **Bro-IDS**, além de **12 algoritmos** desenvolvidos em C#. Os dados são rotulados a partir de uma tabela de ground truth contendo todos os tipos de ataques simulados, gerada de um relatório IXIA.

### D-G. As Características

O conjunto de dados final tem **49 características** divididas em:

1. **Características de Fluxo** (Argus)
2. **Características Básicas** (Argus)
3. **Características de Conteúdo** (Bro-IDS)
4. **Características de Tempo** (Bro-IDS)
5. **Características de Conexão Adicionais** (12 algoritmos próprios em C#)
6. **Rótulos** (gerados de ground truth IXIA)

### Tipos de Ataques

**Nove famílias de ataques** simuladas:

1. **Fuzzers** — fuzzing/scanning
2. **Analysis** — análise de vulnerabilidade
3. **Backdoors** — backdoors
4. **DoS** — Denial of Service
5. **Exploits** — exploits diversos
6. **Generic** — ataques genéricos
7. **Reconnaissance** — reconhecimento
8. **Shellcode** — shellcode injection
9. **Worms** — worms

---

## V. Análise Comparativa entre KDDCUP99 e UNSW-NB15

UNSW-NB15 supera KDDCUP99 nas seguintes dimensões:

- **Tráfego mais realista** (gerado com IXIA com base em CVE atual)
- **Pegada baixa** (ataques modernos de baixo perfil)
- **Sem viés de registros redundantes**
- **Mais características** (49 vs 41)
- **Reflexão mais profunda do ambiente de ameaça moderno**

---

## VI. Os Arquivos do Conjunto de Dados

O *dataset* é disponibilizado em formato CSV com features descritas em tabelas:

- Tabela II: Características de Fluxo (Argus)
- Tabela III: Características Básicas
- Tabela IV: Características de Conteúdo (Bro-IDS)
- Tabela V: Características de Tempo (Bro-IDS)
- Tabela VI: Características de Conexão Adicionais
- Tabela VII: Características de Rótulo
- Tabela VIII: Lista das 9 famílias de ataque

Disponível em: http://www.cybersecurity.unsw.adfa.edu.au/ADFA%20NB15%20Datasets/

---

## VII. Conclusão e Trabalho Futuro

Este artigo apresentou a criação do conjunto de dados **UNSW-NB15** para avaliar NIDS modernos. Os ataques são gerados via IXIA PerfectStorm alimentado por CVE para representação realista. O *dataset* tem 100 GB de tráfego com 49 características.

**Trabalho futuro:** análises mais detalhadas com algoritmos de aprendizado de máquina sobre o *dataset*.

---

## Referências

Lista de ~15 referências, principalmente sobre KDDCUP99, NSLKDD e DARPA98.

---

## Resumo dos pontos-chave para o nosso paper

### Por que este paper é Tier 4 (opcional)

UNSW-NB15 é um *dataset* de NIDS genérico (Camada 3/4 + alguns ataques de aplicação como DoS genérico). **Não é específico para Layer 7 HTTP**, que é o foco do nosso paper. Não vamos usar UNSW-NB15 como *dataset* primário.

### Quando vale citar

- Se nossa §2 (Trabalhos Relacionados) discutir *datasets* para NIDS em geral, podemos mencionar UNSW-NB15 como um *dataset* moderno de NIDS publicado pela UNSW Canberra.
- Pode ser comparado como contraponto: *"UNSW-NB15 cobre 9 famílias gerais de ataque (Fuzzers, Analysis, Backdoors, DoS, etc.) mas não isola variantes específicas de Camada 7 HTTP nem instrumenta campanhas coordenadas cross-session"* — argumento para nossa escolha de gerar dataset sintético.

### Citação no nosso artigo

**Não citamos atualmente.** Pode ser referenciado em §4.1 (Conjunto de Dados) se quisermos mencionar UNSW-NB15 como alternativa considerada mas inadequada para nosso foco específico em Layer 7 coordenado.
