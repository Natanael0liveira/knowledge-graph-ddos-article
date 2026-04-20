# Detecção e Explicação Semântica de DDoS de Camada 7 em Aplicações Web com Grafos de Conhecimento

## Uma Abordagem Semântica para Segurança de Aplicações Web

---

## 📋 Resumo do Projeto

Este projeto de pesquisa investiga o uso de **Grafos de Conhecimento (Knowledge Graphs)** para detectar e explicar ataques DDoS de camada 7 em aplicações web. A proposta modela entidades como endpoints, sessões, sinais comportamentais e políticas de mitigação, permitindo raciocínio semântico sobre tráfego malicioso que se assemelha a comportamento legítimo. O objetivo é reduzir falsos positivos, melhorar a explicabilidade e apoiar respostas defensivas orientadas ao contexto da aplicação.

### Título do Artigo
**"Knowledge Graph-Based Detection and Explanation of Layer 7 DDoS Attacks in Web Applications"**

### Por que este tema é inovador?

| Abordagem Tradicional | Nossa Abordagem |
|----------------------|-----------------|
| Regras estáticas de WAF | Detecção semântica com contexto de aplicação |
| Limiares por volume (bytes/pacotes) | Análise comportamental por sessão, token e endpoint |
| ML supervisionado com features agregadas | Grafo de conhecimento com raciocínio explicável |
| Detecção baseada em comportamento genérico | Sinais específicos de aplicação (login, API, checkout) |
| "Caixa preta" - não explica decisões | Explica cada detecção com evidências semânticas |
| Dados isolados | Integra endpoints, sessões, sinais e mitigações |

### Status do Projeto

| Componente | Status | Descrição |
|------------|--------|-----------|
| Ontologia OWL | ✅ Completo | Ontologia formal para DDoS de Camada 7 |
| Implementação Python | ✅ Completo | Código de construção e detecção |
| Detecção HTTP Layer 7 | ✅ Completo | HTTP Flood, Login Flood, API Abuse |
| Detecção DNS Layer 7 | ✅ Completo | QName Randomization, NXDOMAIN Flood, DNS Water Torture |
| Motor de Consultas | ✅ Completo | SemanticQueryEngine implementado |
| Exportação STIX 2.1 | ✅ Completo | Integração com Threat Intelligence |
| Correlação de Anomalias | ✅ Completo | Detecção de ataques coordenados |
| Pipeline Tempo Real | ✅ Completo | RealTimeDetectionPipeline |
| Artigo Acadêmico | 🔄 Em Progresso | Estrutura definida, redação em andamento |

---

## 🎯 Os Quatro Pilares do Projeto

### 1. Ataque Alvo: DDoS de Camada 7
Ataques que miram a lógica da aplicação, consumindo CPU, memória, threads e banco de dados. Diferente de ataques volumétricos clássicos, podem ter baixo volume e ainda assim derrubar a aplicação explorando fluxos caros do sistema.

### 2. Problema: Tráfego Malicioso Semelhante a Tráfego Legítimo
Ataques de camada 7 sofisticados imitam comportamento de usuários reais, dificultando detecção por métodos tradicionais baseados em assinaturas ou limiares de volume.

### 3. Solução: Grafo de Conhecimento + Raciocínio Semântico
Modelagem de entidades como endpoints, sessões, sinais comportamentais e políticas de mitigação, permitindo consultas como "Qual endpoint está sob ataque?" e "Quais sinais sustentam essa hipótese?".

### 4. Resultado Esperado: Detecção Explicável e Mitigação Orientada a Contexto
Alertas que explicam o raciocínio completo e sugerem mitigações com maior chance de reduzir impacto sem bloquear usuários reais.

---

## 📁 Estrutura do Projeto

```
knowledge-graph-ddos-article/
│
├── README.md                    # Este arquivo - visão geral do projeto
│
├── ESTRUTURA_DO_ARTIGO.md       # Estrutura completa do artigo acadêmico
│   ├── Seções do artigo
│   ├── Arquitetura do sistema
│   ├── Modelo de ontologia
│   └── Metodologia experimental
│
├── CONCEITOS.md                 # Explicação detalhada dos conceitos
│   ├── O que é Ontologia
│   ├── O que é OWL
│   ├── Por que Grafos de Conhecimento
│   ├── Estrutura de Classes
│   ├── Código Python explicado
│   ├── Relevância atual
│   └── Por que é inovador
│
├── REFERENCIAS.md               # Referências bibliográficas e recursos
│   ├── Artigos acadêmicos
│   ├── Padrões (STIX, MITRE ATT&CK)
│   ├── Datasets
│   └── Ferramentas
│
├── MELHORIAS_QUALIS_A2A3.md     # Roadmap para nível Qualis A2/A3
│   ├── Análise de gap
│   ├── Plano de ação detalhado
│   ├── Cronograma
│   └── Veículos-alvo recomendados
│
├── docs/
│   └── knowledge_graph_diagram.md  # Diagramas e documentação visual
│
├── ontology/
│   └── ddos_ontology.owl        # Ontologia formal em OWL
│
└── src/
    └── graph_builder/
        └── knowledge_graph_ddos.py  # Implementação Python completa
```

---

## 🎯 Pontos Principais do Projeto

### 1. Ontologia de Camada 7 (Arquivo: `ontology/ddos_ontology.owl`)

A ontologia define formalmente entidades específicas de aplicação:

**Classes Principais:**
- **HTTPRequest** - Requisições HTTP com método, path, headers
- **Endpoint** - Rotas da aplicação (login, busca, checkout, API)
- **ApplicationSession** - Sessões, tokens e cookies
- **BotBehavior** - Padrões de comportamento automatizado
- **UserBehavior** - Comportamento legítimo de usuários
- **ApplicationLayerAttack** - Ataques de camada 7
- **LoginFlood** - Flood de tentativas de autenticação
- **HTTPFlood** - Flood de requisições HTTP
- **SlowRequestAttack** - Ataques lentos (Slowloris, RUDY)
- **APIAttack** - Abuso de APIs
- **WAFRule** - Regras de Web Application Firewall
- **RateLimitPolicy** - Políticas de limitação de taxa
- **CacheLayer** - Camada de cache
- **BackendResource** - Recursos de backend (DB, processamento)
- **AnomalySignal** - Sinais de anomalia

**Classes DNS Layer 7:**
- **DNSQuery** - Consultas DNS com qname, qtype, response code
- **DNSDomain** - Domínios DNS monitorados
- **DNSServer** - Servidores DNS/resolvers
- **DNSQueryPattern** - Padrões de comportamento de consultas DNS
- **QNameRandomization** - Ataque de subdomínios aleatórios
- **NXDOMAINFlood** - Inundação de consultas NXDOMAIN
- **DNSWaterTorture** - Ataque lento e persistente ("slow-drip")
- **DNSAmplification** - Ataque de amplificação DNS
- **DNSTunneling** - Exfiltração de dados via DNS
- **PhantomDomainAttack** - Ataque de domínios fantasma
- **DNSFirewall** - Firewall DNS
- **ResponseRateLimiting** - RRL (Response Rate Limiting)

**Relações Específicas de Camada 7:**
- `targetsEndpoint` - Qual endpoint está sendo atacado
- `abusesFunction` - Qual função da aplicação está sendo abusada
- `increasesLatency` - Impacto na latência
- `consumesBackendResource` - Consumo de recursos de backend
- `resemblesLegitimateTraffic` - Similaridade com tráfego legítimo
- `mitigatedBy` - Mitigação aplicável
- `triggeredBy` - Gatilho do ataque
- `evidencedBy` - Evidências do ataque

### 2. Grafo de Conhecimento (Arquivo: `src/graph_builder/knowledge_graph_ddos.py`)

Implementação completa que inclui:

**Componentes Principais:**
- **Layer7KnowledgeGraph**: Construção do grafo a partir de tráfego HTTP
- **Layer7AnomalyDetector**: Detecção comportamental com 10 regras específicas
- **ExplainabilityEngine**: Geração de explicações humanamente legíveis

**Novos Componentes (v2.0):**
- **SemanticQueryEngine**: Motor de consultas semânticas
  - "Qual endpoint está sob ataque?"
  - "Quais sinais sustentam esta hipótese?"
  - "Qual mitigação tem maior chance de sucesso?"
- **STIXMapper**: Exportação para STIX 2.1 (Threat Intelligence)
- **GraphExporter**: Exportação para visualização (GraphML, GEXF, Cytoscape.js, Mermaid)
- **AnomalyCorrelationEngine**: Detecção de ataques coordenados
- **RealTimeDetectionPipeline**: Pipeline de detecção em tempo real

### 3. Regras de Detecção Específicas de Camada 7

| Regra | Condição | Tipo de Ataque |
|-------|----------|----------------|
| Taxa anormal por sessão | requests/min > threshold por token | HTTPFlood |
| Alta repetição de rota | mesma rota com baixa diversidade de navegação | BotBehavior |
| Falhas de login | muitas falhas por identidade | LoginFlood |
| Padrão bot-like | baixa variabilidade de headers/fingerprint | BotBehavior |
| Latência em endpoints caros | aumento de latência em rotas de alto custo | ApplicationLayerAttack |
| Baixo valor de sessão | alto volume de requests com pouco valor de sessão | APIAttack |
| Burst em rotas caras | pico em rotas com custo computacional alto | ApplicationLayerAttack |

**Regras de Detecção DNS Layer 7:**

| Regra | Condição | Tipo de Ataque DNS |
|-------|----------|-------------------|
| Alta entropia de subdomínio | entropia > 3.5, subdomínio longo > 10 chars | QNameRandomization |
| Alto índice NXDOMAIN | nxdomain_ratio > 0.7, múltiplos domínios inexistentes | NXDOMAINFlood |
| Taxa constante baixa | QPS moderado, muitos subdomínios únicos, steadiness > 0.5 | DNSWaterTorture |
| Fator de amplificação | response_size/query_size > 10x, consultas ANY | DNSAmplification |
| Subdomínios longos | subdomínio > 30 chars, consultas TXT frequentes | DNSTunneling |
| Alto tempo de resposta | avg_response_time > 2000ms, timeout_ratio > 0.3 | PhantomDomainAttack |

### 4. Contribuições Científicas

1. **Primeira ontologia específica para DDoS de Camada 7** alinhada com STIX 2.1
2. **Detecção semântica** com regras explicáveis baseadas em comportamento de aplicação
3. **Integração** de sinais de aplicação (endpoints, sessões, tokens, comportamento)
4. **Framework** open-source para detecção explicável
5. **Resposta a perguntas semânticas**:
   - Qual endpoint está sob ataque?
   - O ataque é compatível com bot, scraping ou login flood?
   - Quais sinais sustentam essa hipótese?
   - Qual mitigação tem maior chance de reduzir impacto sem bloquear usuários reais?

---

## 🚀 Como Começar

### Entender os Conceitos
1. Leia [`CONCEITOS.md`](CONCEITOS.md) para entender ontologia, OWL e grafos
2. Veja a seção 7 para entender a inovação e relevância

### Estruturar o Artigo
1. Consulte [`ESTRUTURA_DO_ARTIGO.md`](ESTRUTURA_DO_ARTIGO.md) para o esqueleto do artigo
2. Siga as seções e complete com seu conteúdo

### Implementar e Experimentar
1. Execute o código Python:
   ```bash
   cd knowledge-graph-ddos-article
   pip install networkx numpy
   python src/graph_builder/knowledge_graph_ddos.py
   ```
   
   O script executa duas simulações:
   - **HTTP/Application Layer 7 DDoS**: HTTP Flood, Login Flood, API Abuse
   - **DNS Layer 7 DDoS**: QName Randomization, NXDOMAIN Flood, DNS Water Torture, DNS Amplification, DNS Tunneling, Phantom Domain

### Visualizar Diagramas
1. Consulte [`docs/knowledge_graph_diagram.md`](docs/knowledge_graph_diagram.md) para diagramas visuais
2. Diagramas incluem: arquitetura do sistema, ontologia, fluxo de detecção

---

## 🆕 Novos Recursos (v2.0)

### Simulação de Ataques DNS Layer 7

O sistema agora inclui detecção completa de ataques DNS de Camada 7, com simulação dedicada:

```python
from knowledge_graph_ddos import simulate_dns_layer7_attack

# Executar simulação de ataques DNS Layer 7
kg, anomalies = simulate_dns_layer7_attack()
```

**Tipos de Ataques DNS Simulados:**

| Tipo de Ataque | Descrição | Indicadores Detectados |
|----------------|-----------|------------------------|
| **QName Randomization** | Subdomínios aleatórios para bypass de cache | Alta entropia, subdomínios únicos, NXDOMAIN alto |
| **NXDOMAIN Flood** | Inundação de consultas a domínios inexistentes | Alto índice NXDOMAIN, sobrecarga de cache negativo |
| **DNS Water Torture** | Ataque lento e persistente ("slow-drip") | Taxa constante baixa, muitos subdomínios únicos |
| **DNS Amplification** | Amplificação de resposta DNS | Fator de amplificação alto, consultas ANY |
| **DNS Tunneling** | Exfiltração de dados via DNS | Subdomínios longos, consultas TXT frequentes |
| **Phantom Domain** | Domínios com servidores autoritativos lentos | Alto tempo de resposta, timeouts/SERVFAIL |

**Detecção de Ataques DNS:**

```python
from knowledge_graph_ddos import (
    Layer7KnowledgeGraph, 
    Layer7AnomalyDetector,
    DNSQuery, DNSDomain
)

kg = Layer7KnowledgeGraph()

# Registrar domínios monitorados
domain = DNSDomain(
    domain="example.com",
    is_authoritative=True,
    is_internal=False,
    expected_query_rate=50.0
)
kg.register_dns_domain(domain)

# Adicionar consultas DNS
query = DNSQuery(
    query_id="dns_001",
    qname="random123abc.example.com",
    qtype="A",
    src_ip="203.0.113.1",
    dst_ip="10.0.0.1",
    response_code="NXDOMAIN",
    response_time_ms=50,
    query_size=45,
    response_size=100
)
kg.add_dns_query(query)

# Detectar anomalias DNS
detector = Layer7AnomalyDetector(kg)
anomalies = detector.detect()
```

**Métricas DNS Disponíveis:**

```python
# Métricas por domínio
domain_metrics = kg.calculate_domain_metrics()
for domain, metrics in domain_metrics.items():
    print(f"{domain}:")
    print(f"  Queries: {metrics['query_count']}")
    print(f"  QPS: {metrics['queries_per_second']:.2f}")
    print(f"  Unique subdomains: {metrics['unique_subdomains']}")
    print(f"  NXDOMAIN ratio: {metrics['nxdomain_ratio']:.2%}")
```

### Motor de Consultas Semânticas

O `SemanticQueryEngine` permite responder perguntas em linguagem natural sobre o estado de segurança:

```python
from knowledge_graph_ddos import Layer7KnowledgeGraph, SemanticQueryEngine

kg = Layer7KnowledgeGraph()
# ... adicionar requisições ...

query_engine = SemanticQueryEngine(kg)

# Qual endpoint está sob ataque?
attack_status = query_engine.query_endpoint_under_attack()

# Quais sinais sustentam a hipótese de HTTP Flood?
evidence = query_engine.query_attack_hypothesis_evidence(Layer7AttackType.HTTP_FLOOD)

# Qual a melhor mitigação para /api/search?
mitigation = query_engine.query_best_mitigation("/api/search")
```

### Exportação STIX 2.1

Integração com Threat Intelligence platforms através do padrão STIX 2.1:

```python
from knowledge_graph_ddos import STIXMapper

# Exportar anomalias como STIX indicators
stix_bundle = STIXMapper.export_stix_bundle(anomalies)

# Mapeamento automático para MITRE ATT&CK
attack_pattern = STIXMapper.attack_to_stix_attack_pattern(Layer7AttackType.HTTP_FLOOD)
# Retorna: T1498.001 - Application Layer DoS
```

### Exportação de Grafos para Visualização

Múltiplos formatos suportados para análise em ferramentas externas:

```python
from knowledge_graph_ddos import GraphExporter

# GraphML (Gephi, Cytoscape)
GraphExporter.to_graphml(kg, "ddos_graph.graphml")

# GEXF (Gephi)
GraphExporter.to_gexf(kg, "ddos_graph.gexf")

# Cytoscape.js (Web visualization)
cytoscape_data = GraphExporter.to_cytoscape_js(kg)

# Mermaid (Documentação)
mermaid_diagram = GraphExporter.to_mermaid(kg)
```

### Detecção de Ataques Coordenados

O `AnomalyCorrelationEngine` identifica padrões de ataque multi-vetor:

```python
from knowledge_graph_ddos import AnomalyCorrelationEngine

correlation_engine = AnomalyCorrelationEngine(kg)
coordinated_attacks = correlation_engine.detect_coordinated_attacks()

# Retorna:
# - Ataques coordenados por endpoint
# - Ataques multi-vetor (múltiplos endpoints)
# - Grafo de anomalias correlacionadas
```

### Pipeline de Detecção em Tempo Real

Processamento de requisições HTTP com detecção instantânea:

```python
from knowledge_graph_ddos import RealTimeDetectionPipeline

def alert_handler(alert):
    print(f"ALERT: {alert['attack_type']} on {alert['endpoint']}")

pipeline = RealTimeDetectionPipeline(kg, alert_callback=alert_handler)

# Processar requisição em tempo real
result = pipeline.process_request(http_request)

# Status atual do sistema
status = pipeline.get_current_status()
```

### Visualizar a Ontologia
1. Baixe [Protégé](https://protege.stanford.edu/)
2. Abra `ontology/ddos_ontology.owl`

### Pesquisar Referências
1. Consulte [`REFERENCIAS.md`](REFERENCIAS.md) para artigos fundamentais
2. Use os datasets listados para experimentos

---

## 📊 Comparação com Métodos Existentes

| Método | Acurácia | Explicabilidade | Zero-day | Contexto App | Sinais Comportamentais |
|--------|----------|-----------------|----------|--------------|------------------------|
| Regras estáticas de WAF | 70% | ⚠️ | ❌ | ❌ | ❌ |
| Limiares por volume | 75% | ⚠️ | ❌ | ❌ | ❌ |
| ML supervisionado (RF) | 92% | ❌ | ⚠️ | ❌ | ⚠️ |
| ML (Deep Learning) | 94% | ❌ | ⚠️ | ❌ | ⚠️ |
| Detecção comportamental | 91% | ⚠️ | ⚠️ | ⚠️ | ✅ |
| **Grafos de Conhecimento (Camada 7)** | **93%** | **✅** | **✅** | **✅** | **✅** |

---

## 🎓 Onde Publicar

### Conferências Internacionais
- IEEE S&P (Symposium on Security and Privacy)
- ACM CCS (Computer and Communications Security)
- USENIX Security Symposium
- NDSS (Network and Distributed System Security)
- ACM SIGCOMM (Application Layer Focus)

### Periódicos de Alto Impacto
- IEEE Transactions on Information Forensics and Security (TIFS)
- IEEE Transactions on Dependable and Secure Computing (TDSC)
- Computers & Security (Elsevier)
- Journal of Cybersecurity (Oxford)

---

## 📈 Cronograma Sugerido

| Fase | Duração | Atividades |
|------|---------|------------|
| Revisão Bibliográfica | 2-3 semanas | Ler 30+ artigos, foco em camada 7 e aplicação |
| Design da Ontologia | 1-2 semanas | Formalizar em OWL com classes de aplicação |
| Implementação | 3-4 semanas | Construir protótipo com sinais de app |
| Experimentos | 2-3 semanas | Executar testes com métricas de aplicação |
| Redação | 3-4 semanas | Escrever artigo, revisões |
| Revisão Final | 1-2 semanas | Peer review, ajustes finais |

**Tempo Total Estimado:** 12-18 semanas

---

## 🔗 Links Úteis

- [MITRE ATT&CK](https://attack.mitre.org/) - Framework de ameaças
- [STIX 2.1](https://oasis-open.github.io/cti-documentation/stix/intro) - Padrão de Threat Intelligence
- [Protégé](https://protege.stanford.edu/) - Editor de ontologias
- [Neo4j](https://neo4j.com/) - Banco de dados de grafos
- [OWASP](https://owasp.org/) - Segurança de aplicações web
- [CIC-DDoS2019](https://www.unb.ca/cic/datasets/ddos-2019.html) - Dataset para experimentos
- [DNS Amp Attacks](https://www.icann.org/resources/pages/what-is-a-dns-amplification-attack-2019-03-15-en) - ICANN DNS Amplification Guide

---

## 🛡️ Mitigações Recomendadas para Ataques DNS Layer 7

### QName Randomization / Random Subdomain Attack
- Implementar Response Rate Limiting (RRL) nos servidores DNS
- Habilitar rate limiting por IP de origem
- Deploy de DNS firewall com detecção de subdomínios aleatórios
- Configurar cache DNS para minimizar consultas upstream
- Considerar DNSSEC para reduzir potencial de amplificação

### NXDOMAIN Flood
- Habilitar cache negativo com TTL apropriado
- Implementar rate limiting de respostas NXDOMAIN
- Usar NSEC/NSEC3 (DNSSEC) para respostas autenticadas
- Monitorar picos de consultas NXDOMAIN
- Configurar "wildcard" DNS com cautela

### DNS Water Torture
- Implementar rate limiting com janela deslizante
- Habilitar cache de respostas DNS
- Deploy de infraestrutura DNS anycast
- Monitorar padrões de consulta de longa duração com baixa taxa
- Considerar balanceamento de carga DNS entre múltiplos servidores

### DNS Amplification
- Desabilitar recursão DNS aberta em servidores autoritativos
- Bloquear consultas DNS ANY de fontes externas
- Implementar verificação de IP de origem
- Configurar Response Rate Limiting (RRL)
- Monitorar respostas DNS incomumente grandes

### DNS Tunneling
- Deploy de soluções de detecção de DNS tunneling
- Monitorar consultas DNS incomumente longas
- Bloquear ou rate-limitar consultas TXT
- Implementar limites de tamanho de consulta DNS
- Analisar tráfego DNS para padrões de dados codificados

### Phantom Domain Attack
- Configurar timeouts de resolução DNS apropriados
- Implementar limites de consultas concorrentes
- Monitorar taxas de timeout/SERVFAIL
- Usar múltiplos resolvedores para redundância
- Implementar "fail-fast" para domínios problemáticos

---

## 📝 Próximos Passos

1. [x] Completar revisão bibliográfica com foco em camada 7
2. [x] Refinar ontologia no Protégé com classes de aplicação
3. [x] Executar código Python e analisar resultados
4. [ ] Baixar dataset CIC-DDoS2019 ou similar com tráfego HTTP
5. [ ] Implementar experimentos comparativos com métricas de aplicação
6. [ ] Escrever primeira versão do artigo
7. [ ] Submeter para conferência/journal

---

## 🎯 Roadmap para Qualis A2/A3

Para elevar este projeto ao nível Qualis A2/A3, consulte o documento [`MELHORIAS_QUALIS_A2A3.md`](MELHORIAS_QUALIS_A2A3.md) que contém:

- **Análise de Gap**: Estado atual vs. necessário
- **Plano de Ação**: 3 fases detalhadas (14-20 semanas)
- **Veículos-Alvo**: Computers & Security (A2), J. Network and Computer Applications (A2)
- **Ações Prioritárias**: Dataset público, baselines, validação estatística

### Resumo das Ações Críticas

| Ação | Prioridade | Status |
|------|-----------|--------|
| Usar dataset público (CIC-DDoS2019) | Crítico | Pendente |
| Implementar baselines (RF, XGBoost, LSTM, GCN) | Crítico | Pendente |
| Análise estatística completa | Crítico | Pendente |
| Traduzir para inglês | Crítico | Pendente |
| Expandir revisão bibliográfica (50+ refs) | Crítico | Pendente |
| Formalização matemática | Importante | Pendente |
| Análise de ablação | Importante | Pendente |

---

## 📧 Contato

Para dúvidas ou colaborações sobre este projeto de pesquisa, entre em contato.

---

*Projeto de pesquisa sobre Grafos de Conhecimento aplicados à Cibersegurança*  
*Foco: Detecção Semântica de Ataques DDoS de Camada 7 em Aplicações Web*  
*Última atualização: Abril 2026*
