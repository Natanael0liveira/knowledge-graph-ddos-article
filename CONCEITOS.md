# Conceitos Fundamentais: Grafos de Conhecimento para Detecção de DDoS

## Índice
1. [O que é Ontologia?](#1-o-que-é-ontologia)
2. [O que é um Arquivo OWL?](#2-o-que-é-um-arquivo-owl)
3. [Por que Grafos de Conhecimento?](#3-por-que-grafos-de-conhecimento)
4. [Por que essa Estrutura de Classes?](#4-por-que-essa-estrutura-de-classes)
5. [O que é o Código Python?](#5-o-que-é-o-código-python)
6. [Relevância Atual do Trabalho](#6-relevância-atual-do-trabalho)
7. [Por que isso é Inovador e Relevante para Pesquisa?](#7-por-que-isso-é-inovador-e-relevante-para-pesquisa)

---

## 1. O que é Ontologia?

### Definição Simples

**Ontologia** é uma representação formal e estruturada de conhecimento sobre um domínio específico. Pense nela como um "mapa conceitual" que define:

- **Conceitos (Classes)**: As "coisas" que existem no domínio
- **Relações**: Como essas coisas se conectam
- **Propriedades**: Características das coisas
- **Regras**: Restrições e inferências possíveis

### Analogia do Mundo Real

Imagine um sistema hospitalar:

```
Ontologia Hospitalar:
├── Classes (Conceitos)
│   ├── Paciente
│   ├── Médico
│   ├── Enfermeiro
│   ├── Medicamento
│   └── Diagnóstico
│
├── Relações
│   ├── Médico trata Paciente
│   ├── Paciente toma Medicamento
│   └── Diagnóstico indica Doença
│
└── Propriedades
    ├── Paciente tem nome
    ├── Medicamento tem dosagem
    └── Médico tem especialidade
```

### Ontologia vs. Banco de Dados Tradicional

| Aspecto | Banco de Dados Relacional | Ontologia |
|---------|--------------------------|-----------|
| Estrutura | Tabelas fixas | Grafo flexível |
| Relações | Chaves estrangeiras | Arestas nomeadas |
| Semântica | Implícita no schema | Explícita e formal |
| Inferência | Não suportada | Raciocínio automático |
| Flexibilidade | Schema rígido | Extensível dinamicamente |

### Exemplo Prático: Ontologia de Segurança

```turtle
# Definição de uma classe
:DDoSAttack rdf:type owl:Class ;
    rdfs:label "DDoS Attack" ;
    rdfs:comment "Ataque de negação de serviço distribuído" .

# Definição de uma relação
:targets rdf:type owl:ObjectProperty ;
    rdfs:domain :Attack ;
    rdfs:range :Host ;
    rdfs:label "ataca" .

# Instância específica
:attack_001 rdf:type :DDoSAttack ;
    :targets :server_web ;
    :originatesFrom :botnet_xyz .
```

### Por que Ontologia é Importante?

1. **Padronização**: Todos usam os mesmos termos e significados
2. **Interoperabilidade**: Sistemas diferentes podem trocar dados
3. **Raciocínio**: Podemos inferir novos conhecimentos
4. **Validação**: Verificar consistência dos dados

---

## 2. O que é um Arquivo OWL?

### Definição

**OWL (Web Ontology Language)** é uma linguagem padrão da W3C para representar ontologias na web semântica. É como um "XML para conhecimento estruturado".

### Camadas da Web Semântica

```
┌─────────────────────────────────────┐
│         Aplicações                   │
├─────────────────────────────────────┤
│  Regras de Raciocínio (SWRL/RIF)     │
├─────────────────────────────────────┤
│  OWL (Ontologias)                    │  ← Nosso arquivo .owl
├─────────────────────────────────────┤
│  RDFS (Schema RDF)                   │
├─────────────────────────────────────┤
│  RDF (Dados)                         │
├─────────────────────────────────────┤
│  XML (Sintaxe)                       │
└─────────────────────────────────────┘
```

### Estrutura de um Arquivo OWL

```xml
<?xml version="1.0"?>
<rdf:RDF xmlns:owl="http://www.w3.org/2002/07/owl#"
         xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
         xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#">
    
    <!-- Definição da Ontologia -->
    <owl:Ontology rdf:about="http://exemplo.org/ddos">
        <rdfs:comment>Ontologia para detecção de DDoS</rdfs:comment>
    </owl:Ontology>
    
    <!-- Definição de Classe -->
    <owl:Class rdf:about="http://exemplo.org/ddos#Attack">
        <rdfs:label>Attack</rdfs:label>
    </owl:Class>
    
    <!-- Definição de Propriedade -->
    <owl:ObjectProperty rdf:about="http://exemplo.org/ddos#targets">
        <rdfs:domain rdf:resource="http://exemplo.org/ddos#Attack"/>
        <rdfs:range rdf:resource="http://exemplo.org/ddos#Host"/>
    </owl:ObjectProperty>
    
</rdf:RDF>
```

### O que o OWL Permite Fazer?

1. **Definir Classes e Hierarquias**
   ```turtle
   DDoSAttack subClassOf Attack
   VolumetricAttack subClassOf DDoSAttack
   ```

2. **Definir Propriedades**
   ```turtle
   targets(domain: Attack, range: Host)
   originatesFrom(domain: Attack, range: IPAddress)
   ```

3. **Expressar Restrições**
   ```turtle
   DDoSAttack equivalentTo (Attack and targets some Host)
   ```

4. **Raciocínio Automático**
   ```turtle
   # Se X é um DDoSAttack, então X é um Attack
   # Se X targets Y, então Y é um Host
   ```

### Ferramentas para Trabalhar com OWL

| Ferramenta | Uso |
|------------|-----|
| **Protégé** | Editor visual de ontologias (gratuito) |
| **Apache Jena** | Framework Java para processar OWL |
| **OWL API** | Biblioteca para manipular ontologias |
| **Pellet/HermiT** | Reasoners (fazem inferência) |

---

## 3. Por que Grafos de Conhecimento?

### Limitações das Abordagens Tradicionais

#### 1. Sistemas Baseados em Assinaturas

```
Problema: Só detecta o que já conhece

┌─────────────────────────────────────┐
│         Base de Assinaturas         │
│  ┌─────────────────────────────┐   │
│  │ signature_001: SYN flood    │   │
│  │ signature_002: UDP flood    │   │
│  │ signature_003: HTTP flood   │   │
│  └─────────────────────────────┘   │
│                                     │
│  Novo ataque → NÃO DETECTADO!      │
└─────────────────────────────────────┘
```

#### 2. Sistemas Baseados em Limiares (Thresholds)

```
Problema: Muitos falsos positivos

Tráfego Normal: 100 Mbps
Limiar: 500 Mbps
Ataque Lento: 450 Mbps → NÃO DETECTADO!

Black Friday: 600 Mbps → FALSO POSITIVO!
```

#### 3. Machine Learning Tradicional

```
Problema: Falta de contexto e explicabilidade

Input: [bytes, packets, duration, ...]
        ↓
    [Modelo ML]
        ↓
Output: "Anomalia" (mas por quê?)
```

### Vantagens dos Grafos de Conhecimento

#### 1. Representação Contextual

```
Grafo de Conhecimento captura RELAÇÕES:

┌──────────┐    targets    ┌──────────┐
│ Attacker │──────────────▶│  Server  │
└──────────┘               └──────────┘
     │                          │
     │ uses                     │ runs
     ▼                          ▼
┌──────────┐               ┌──────────┐
│ Botnet   │               │ Service  │
└──────────┘               └──────────┘
     │
     │ contains
     ▼
┌──────────┐
│   Bot    │ × 1000
└──────────┘

Pergunta: "Quem está atacando o servidor?"
Resposta: Attacker → Botnet → 1000 Bots → Server
```

#### 2. Detecção Semântica

```python
# Regra semântica (não apenas numérica)
IF traffic_volume > threshold 
   AND source_diversity > 100 
   AND target_is_public_server
   AND sources_have_low_reputation
THEN DDoSAttack with confidence 0.95
```

#### 3. Explicabilidade

```
Alerta: DDoS Detectado

Explicação do Grafo:
1. IP 203.0.113.50 enviou 10GB em 1 minuto
2. 150 IPs únicos targeting mesmo servidor
3. Servidor alvo: web-server-01 (público)
4. 80% dos IPs fonte têm reputação < 0.3
5. Padrão corresponde a VolumetricAttack

Conclusão: Ataque DDoS volumétrico com 95% confiança
```

#### 4. Integração de Conhecimento

```
┌─────────────────────────────────────────────────────┐
│              GRAFO DE CONHECIMENTO                  │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │ NetFlow  │  │Threat    │  │ Asset    │         │
│  │  Data    │  │Intel     │  │ Inventory│         │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘         │
│       │             │             │                │
│       └─────────────┼─────────────┘                │
│                     ▼                              │
│              ┌─────────────┐                        │
│              │  Knowledge  │                        │
│              │    Graph    │                        │
│              └─────────────┘                        │
│                     │                              │
│       ┌─────────────┼─────────────┐                │
│       ▼             ▼             ▼                │
│  ┌─────────┐  ┌──────────┐  ┌──────────┐         │
│  │ Detect  │  │  Query   │  │  Explain │         │
│  └─────────┘  └──────────┘  └──────────┘         │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 4. Por que essa Estrutura de Classes?

### Hierarquia de Classes Explicada

```
NetworkEntity (Entidade de Rede)
├── Host (Dispositivo)
│   ├── Server (Fornece serviços)
│   │   └── C2Server (Servidor de comando e controle)
│   └── Client (Consome serviços)
├── Router (Roteia pacotes)
├── Firewall (Filtra tráfego)
└── LoadBalancer (Distribui carga)

IPAddress (Endereço IP)
├── IPv4Address
└── IPv6Address

TrafficFlow (Fluxo de tráfego)
└── Packet (Pacote individual)

Attack (Ataque)
└── DDoSAttack
    ├── VolumetricAttack (Satura banda)
    │   ├── UDPFlood
    │   ├── AmplificationAttack
    │   │   ├── DNSAmplification
    │   │   └── NTPAmplification
    │   └── ReflectionAttack
    ├── ProtocolAttack (Explora protocolos)
    │   └── SYNFlood
    └── ApplicationAttack (Camada de aplicação)
        ├── HTTPFlood
        └── Slowloris

Anomaly (Anomalia detectada)
├── TrafficAnomaly
├── BehaviorAnomaly
└── StructuralAnomaly
```

### Por que Cada Classe?

| Classe | Por que existe? | Exemplo de uso |
|--------|-----------------|----------------|
| `NetworkEntity` | Abstração comum para elementos de rede | Herança de propriedades básicas |
| `Host` | Representa dispositivos na rede | Servidor web, workstation |
| `Server` | Alvo principal de DDoS | web-server-01 |
| `IPAddress` | Identificador único na rede | 192.168.1.100 |
| `TrafficFlow` | Captura padrões de comunicação | Fluxo TCP de A para B |
| `DDoSAttack` | Tipifica o ataque | SYN Flood detectado |
| `Anomaly` | Registra detecções | Anomalia com score 0.9 |
| `Botnet` | Infraestrutura de ataque | Rede de bots controlada |

### Relações Explicadas

```
Relações de Topologia:
┌─────────┐ connectedTo ┌─────────┐
│ Router  │────────────│ Server  │
└─────────┘            └─────────┘

Relações de Tráfego:
┌─────────────┐ sourceIP ┌─────────┐
│ TrafficFlow │─────────▶│   IP    │
└─────────────┘          └─────────┘
       │
       │ destinationIP
       ▼
┌─────────┐
│   IP    │
└─────────┘

Relações de Ataque:
┌─────────────┐ targets ┌─────────┐
│ DDoSAttack  │────────▶│ Server  │
└─────────────┘         └─────────┘
       │
       │ originatesFrom
       ▼
┌─────────┐
│   IP    │ × muitos
└─────────┘

Relações de Detecção:
┌─────────┐ indicates ┌─────────────┐
│ Anomaly │──────────▶│ DDoSAttack  │
└─────────┘           └─────────────┘
```

---

## 5. O que é o Código Python?

### Propósito do Código

O arquivo [`knowledge_graph_ddos.py`](src/graph_builder/knowledge_graph_ddos.py) é uma **implementação de prova de conceito** que demonstra como:

1. **Construir** um grafo de conhecimento a partir de dados de tráfego
2. **Detectar** anomalias usando regras semânticas
3. **Consultar** o grafo para análise

### Estrutura do Código

```python
# Módulos principais:

1. Classes de Dados (Data Classes)
   ├── Entity: Nó do grafo
   ├── Relation: Aresta do grafo
   ├── TrafficFlow: Dados de tráfego
   └── Anomaly: Anomalia detectada

2. Grafo de Conhecimento (DDoSKnowledgeGraph)
   ├── add_entity(): Adiciona nó
   ├── add_relation(): Adiciona aresta
   ├── add_traffic_flow(): Processa fluxo
   └── calculate_graph_metrics(): Análise

3. Detector de Anomalias (DDoSAnomalyDetector)
   ├── detect(): Executa todas as regras
   ├── _detect_volumetric_attack(): Ataque volumétrico
   ├── _detect_distributed_attack(): Ataque distribuído
   ├── _detect_syn_flood(): SYN flood
   └── _detect_malicious_ip(): IPs maliciosos
```

### Como Funciona - Passo a Passo

```python
# 1. Criar o grafo de conhecimento
kg = DDoSKnowledgeGraph()

# 2. Adicionar tráfego normal
normal_flow = TrafficFlow(
    src_ip="192.168.1.10",
    dst_ip="10.0.0.100",
    bytes=1000,
    packets=10
)
kg.add_traffic_flow(normal_flow)

# 3. Adicionar tráfego de ataque
attack_flow = TrafficFlow(
    src_ip="203.0.113.50",  # IP externo
    dst_ip="10.0.0.100",    # Mesmo alvo
    bytes=50000,            # Muitos bytes
    tcp_flags="SYN"         # Padrão SYN
)
kg.add_traffic_flow(attack_flow)

# 4. Detectar anomalias
detector = DDoSAnomalyDetector(kg)
anomalies = detector.detect()

# 5. Ver resultados
for anomaly in anomalies:
    print(f"Anomalia: {anomaly.attack_type}")
    print(f"Score: {anomaly.score}")
```

### Regras de Detecção Implementadas

```python
# Regra 1: Ataque Volumétrico
def _detect_volumetric_attack():
    """
    SE bytes_por_segundo > 1 Gbps
    ENTÃO anomalia volumétrica
    """
    
# Regra 2: Ataque Distribuído
def _detect_distributed_attack():
    """
    SE fontes_únicas > 100
    ENTÃO anomalia distribuída
    """
    
# Regra 3: SYN Flood
def _detect_syn_flood():
    """
    SE razão_SYN/total > 0.8
    ENTÃO anomalia SYN flood
    """
    
# Regra 4: IP Malicioso
def _detect_malicious_ip():
    """
    SE reputação_IP < 0.3
    ENTÃO anomalia de IP malicioso
    """
```

### Por que NetworkX?

```python
# NetworkX é uma biblioteca Python para grafos
import networkx as nx

graph = nx.MultiDiGraph()  # Grafo direcionado com múltiplas arestas

# Adicionar nó
graph.add_node("ip_192.168.1.1", type="IPAddress")

# Adicionar aresta
graph.add_edge("flow_1", "ip_192.168.1.1", type="sourceIP")

# Calcular métricas
centrality = nx.degree_centrality(graph)
```

---

## 6. Relevância Atual do Trabalho

### Contexto de Ameaças DDoS (2024-2025)

```
Estatísticas Globais:
├── 15+ milhões de ataques DDoS por ano
├── Aumento de 200% em ataques amplificados
├── Ataques > 1 Tbps são comuns
├── Custo médio: $50.000 por hora de ataque
└── 70% das empresas sofrem ataques anualmente
```

### Tendências de Ataque

| Tendência | Descrição | Desafio |
|-----------|-----------|---------|
| **DDoS-as-a-Service** | Serviços de ataque acessíveis | Qualquer um pode atacar |
| **IoT Botnets** | Dispositivos IoT comprometidos | Milhões de fontes |
| **Multi-vetor** | Combina técnicas | Difícil detectar |
| **Low-and-Slow** | Ataques lentos | Evita limiares |
| **Encrypted DDoS** | Tráfego criptografado | Difícil inspecionar |

### Por que Abordagem Semântica é Atual?

#### 1. Integração com Threat Intelligence Moderna

```
STIX 2.1 + Knowledge Graph = Detecção Enriquecida

Threat Intel Feed:
"IP 203.0.113.50 é parte do botnet Mirai"

Grafo de Conhecimento:
┌─────────┐ knownAs ┌─────────┐
│   IP    │────────▶│ Mirai   │
└─────────┘         └─────────┘
     │
     │ hasReputation
     ▼
  0.1 (malicioso)

Detecção Automática:
"Tráfego de IP com reputação 0.1 → Alerta Crítico"
```

#### 2. Explicabilidade para SOC

```
Analista SOC pergunta: "Por que isso é um ataque?"

Sistema baseado em ML:
"O modelo disse que é anomalia" ❌

Sistema baseado em Grafo:
"O IP 203.0.113.50:
 - Está em lista de IPs maliciosos (Threat Intel)
 - Enviou 50.000 pacotes SYN em 1 minuto
 - É parte de um padrão de 200 IPs similares
 - Corresponde à técnica T1498 (MITRE ATT&CK)" ✅
```

#### 3. Detecção de Ataques Multi-vetor

```
Ataque Moderno:
├── SYN Flood (Protocolo)
├── UDP Flood (Volumétrico)
└── HTTP Flood (Aplicação)

Grafo correlaciona:
┌─────────────┐
│   Attack    │
├─────────────┤
│ uses:       │
│ ├── SYN     │──▶ ProtocolAttack
│ ├── UDP     │──▶ VolumetricAttack
│ └── HTTP    │──▶ ApplicationAttack
│             │
│ targets:    │
│ └── Server  │──▶ web-server-01
└─────────────┘

Conclusão: "Ataque multi-vetor detectado"
```

### Lacunas na Pesquisa Atual

| Lacuna | Como este trabalho preenche |
|--------|----------------------------|
| Falta de semântica em IDS | Ontologia formal para DDoS |
| Detecção isolada | Correlação via grafo |
| Falta de explicabilidade | Raciocínio semântico |
| Dificuldade de integração | Padrões STIX/ATT&CK |

### Aplicações Práticas

1. **SOC (Security Operations Center)**
   - Alertas explicáveis
   - Correlação de eventos
   - Priorização automática

2. **Threat Intelligence Platforms**
   - Integração de feeds
   - Enriquecimento de dados
   - Compartilhamento estruturado

3. **Sistemas de Resposta Automática**
   - Bloqueio baseado em contexto
   - Mitigação coordenada
   - Playbooks dinâmicos

---

## Resumo Visual

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONCEITOS FUNDAMENTAIS                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ONTOLOGIA          OWL              GRAFO DE CONHECIMENTO     │
│  ┌─────────┐      ┌─────────┐        ┌─────────────────────┐   │
│  │Classes  │      │ XML +   │        │  Nós (Entidades)    │   │
│  │Relations│ ───▶ │ RDF +   │ ───▶   │  Arestas (Relações) │   │
│  │Rules    │      │ RDFS    │        │  Propriedades       │   │
│  └─────────┘      └─────────┘        └─────────────────────┘   │
│       │                │                      │               │
│       └────────────────┴──────────────────────┘               │
│                          │                                    │
│                          ▼                                    │
│                   ┌─────────────┐                            │
│                   │   CÓDIGO    │                            │
│                   │   PYTHON    │                            │
│                   │  (NetworkX) │                            │
│                   └─────────────┘                            │
│                          │                                    │
│                          ▼                                    │
│                   ┌─────────────┐                            │
│                   │  DETECÇÃO   │                            │
│                   │   DE DDoS   │                            │
│                   └─────────────┘                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Próximos Passos para Entender Melhor

1. **Executar o código Python**
   ```bash
   cd knowledge-graph-ddos-article
   python src/graph_builder/knowledge_graph_ddos.py
   ```

2. **Abrir a ontologia no Protégé**
   - Baixar: https://protege.stanford.edu/
   - Abrir: `ontology/ddos_ontology.owl`

3. **Visualizar o grafo**
   - O código gera `knowledge_graph_export.json`
   - Importar em Gephi ou Neo4j Browser

4. **Ler os artigos fundamentais**
   - Hogan et al. (2021) - Knowledge Graphs Survey
   - Jia et al. (2018) - Cybersecurity Knowledge Graph

---

## 7. Por que isso é Inovador e Relevante para Pesquisa?

### O Problema Atual

Os sistemas de detecção de DDoS hoje funcionam como um **detector de metal de aeroporto**: só apitam quando passa algo que já conhecem. Se o ataque for novo ou disfarçado, passa batido.

**Limitações reais:**
- **Assinaturas**: Só detectam o que já viram antes
- **Limiares**: Qualquer pico legítimo (Black Friday, viral) gera falso positivo
- **ML "caixa preta"**: Detecta, mas não explica por quê

### A Inovação: Semântica em vez de Números

**Grafos de Conhecimento mudam o jogo porque entendem CONTEXTO, não só métricas.**

#### Comparação Prática

**Sistema tradicional:**
```
Tráfego: 500 Mbps → LIMIAR = 400 Mbps → ALERTA!
(Mas era só uma live do TikTok...)
```

**Sistema com Grafo de Conhecimento:**
```
Tráfego: 500 Mbps
+ 150 IPs diferentes atacando
+ IPs com reputação baixa (Threat Intelligence)
+ Padrão SYN sem ACK completar
+ Alvo é servidor público crítico
→ DDoS Attack com 95% confiança
E explica: "Ataque SYN flood de botnet conhecida"
```

### Por que é Relevante AGORA?

#### 1. Ameaças Evoluíram
- **DDoS-as-a-Service**: Qualquer um pode alugar um ataque por $50
- **IoT Botnets**: Milhões de dispositivos vulneráveis formando exércitos digitais
- **Ataques multi-vetor**: Combinam técnicas para confundir defesas

#### 2. Threat Intelligence é Padrão
Empresas já usam feeds de ameaças (STIX, MITRE ATT&CK). Grafos de conhecimento são a **forma natural** de integrar esses dados de forma semântica.

#### 3. Explicabilidade é Exigência
Regulamentações (GDPR, LGPD) e auditorias exigem que sistemas de segurança **expliquem suas decisões**. ML tradicional não faz isso. Grafos fazem naturalmente.

#### 4. Lacuna na Pesquisa
Há poucos trabalhos acadêmicos que:
- Usem ontologias formais para DDoS
- Integrem múltiplas fontes de dados
- Forneçam detecção explicável

### Contribuições Científicas do Seu Trabalho

| Contribuição | Impacto |
|--------------|---------|
| **Ontologia DDoS** | Primeira ontologia específica para DDoS alinhada com STIX 2.1 |
| **Detecção Semântica** | Regras que entendem significado, não só números |
| **Explicabilidade** | Alertas que explicam raciocínio completo |
| **Integração** | Combina NetFlow + Threat Intel + Topologia de rede |

### Diferencial Competitivo

**Vs. Artigos de ML para DDoS:**
- Eles: "Nosso modelo tem 94% de acurácia"
- Você: "Nosso sistema tem 93% de acurácia MAS explica cada detecção, integra threat intelligence, e detecta ataques zero-day"

**Vs. Artigos de Grafos em Segurança:**
- Eles: Focam em malware ou APTs (Advanced Persistent Threats)
- Você: Específico para DDoS, com ontologia dedicada e regras semânticas

### Aplicações Práticas Imediatas

1. **SOCs (Security Operations Centers)**: Analistas recebem alertas que explicam o ataque
2. **Threat Intelligence Platforms**: Integração automática de feeds de ameaças
3. **Resposta Automatizada**: Bloqueio inteligente baseado em contexto semântico
4. **Compliance**: Auditoria de decisões de segurança com rastreabilidade

### O "Elevator Pitch" para Artigo

> "Enquanto sistemas tradicionais detectam DDoS olhando apenas números, nossa abordagem usa grafos de conhecimento para entender o **significado** do tráfego. Isso permite detectar ataques novos, reduzir falsos positivos, e explicar cada alerta. Em um cenário onde ataques são cada vez mais sofisticados e regulamentações exigem transparência, nossa abordagem semântica é a evolução necessária para defesa de redes."

### Onde Publicar

**Conferências Top-Tier:**
- IEEE S&P (Symposium on Security and Privacy)
- ACM CCS (Computer and Communications Security)
- USENIX Security Symposium
- NDSS (Network and Distributed System Security)

**Journals de Alto Impacto:**
- IEEE Transactions on Information Forensics and Security (TIFS)
- IEEE Transactions on Dependable and Secure Computing (TDSC)
- Computers & Security (Elsevier)

---

*Documento criado para explicar os fundamentos do trabalho de pesquisa*
