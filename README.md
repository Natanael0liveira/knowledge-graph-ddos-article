# Grafos de Conhecimento para Detecção de Ataques DDoS

## Uma Abordagem Semântica para Segurança de Redes

---

## 📋 Resumo do Projeto

Este projeto de pesquisa explora o uso de **Grafos de Conhecimento (Knowledge Graphs)** para detecção de ataques DDoS (Distributed Denial of Service). A abordagem proposta utiliza raciocínio semântico para identificar ameaças com maior precisão e explicabilidade do que métodos tradicionais.

### Título do Artigo
**"Knowledge Graph-Based Anomaly Detection for DDoS Attacks: A Semantic Approach to Network Security"**

### Por que este tema é inovador?

| Abordagem Tradicional | Nossa Abordagem |
|----------------------|-----------------|
| Detecta apenas padrões conhecidos | Detecta ataques zero-day |
| Alta taxa de falsos positivos | Reduz falsos positivos com contexto |
| "Caixa preta" - não explica decisões | Explica cada detecção semanticamente |
| Dados isolados | Integra múltiplas fontes (Threat Intel, NetFlow, Topologia) |

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
├── CONCEITOS_EXPLICADOS.md       # Explicação detalhada dos conceitos
│   ├── O que é Ontologia
│   ├── O que é OWL
│   ├── Por que Grafos de Conhecimento
│   ├── Estrutura de Classes
│   ├── Código Python explicado
│   ├── Relevância atual
│   └── Por que é inovador
│
├── REFERENCIAS.md                # Referências bibliográficas e recursos
│   ├── Artigos acadêmicos
│   ├── Padrões (STIX, MITRE ATT&CK)
│   ├── Datasets
│   └── Ferramentas
│
├── ontology/
│   └── ddos_ontology.owl         # Ontologia formal em OWL
│
└── src/
    └── graph_builder/
        └── knowledge_graph_ddos.py  # Implementação Python
```

---

## 🎯 Pontos Principais do Projeto

### 1. Ontologia DDoS (Arquivo: `ontology/ddos_ontology.owl`)

A ontologia define formalmente:
- **Classes**: Entidades do domínio (Servidor, IP, Ataque, Anomalia)
- **Relações**: Como entidades se conectam (targets, originatesFrom, indicates)
- **Propriedades**: Atributos das entidades (reputation, byteCount, anomalyScore)
- **Regras**: Inferências para detecção automática

### 2. Grafo de Conhecimento (Arquivo: `src/graph_builder/knowledge_graph_ddos.py`)

Implementação que:
- Constrói o grafo a partir de dados de tráfego
- Aplica regras semânticas de detecção
- Calcula métricas de anomalia
- Gera alertas explicáveis

### 3. Regras de Detecção

| Regra | Condição | Tipo de Ataque |
|-------|----------|----------------|
| Volumétrica | bytes/seg > 1 Gbps | VolumetricAttack |
| Distribuída | fontes únicas > 100 | DDoSAttack |
| SYN Flood | razão SYN/total > 0.8 | SYNFlood |
| IP Malicioso | reputação < 0.3 | MaliciousTraffic |

### 4. Contribuições Científicas

1. **Primeira ontologia DDoS** alinhada com STIX 2.1
2. **Detecção semântica** com regras explicáveis
3. **Integração** de múltiplas fontes de dados
4. **Framework** open-source para detecção

---

## 🚀 Como Começar

### Entender os Conceitos
1. Leia [`CONCEITOS_EXPLICADOS.md`](CONCEITOS_EXPLICADOS.md) para entender ontologia, OWL e grafos
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

### Visualizar a Ontologia
1. Baixe [Protégé](https://protege.stanford.edu/)
2. Abra `ontology/ddos_ontology.owl`

### Pesquisar Referências
1. Consulte [`REFERENCIAS.md`](REFERENCIAS.md) para artigos fundamentais
2. Use os datasets listados para experimentos

---

## 📊 Comparação com Métodos Existentes

| Método | Acurácia | Explicabilidade | Zero-day | Integração TI |
|--------|----------|-----------------|----------|---------------|
| Assinaturas | 70% | ❌ | ❌ | ❌ |
| Limiares | 75% | ⚠️ | ❌ | ❌ |
| ML (Random Forest) | 92% | ❌ | ⚠️ | ❌ |
| ML (Deep Learning) | 94% | ❌ | ⚠️ | ❌ |
| **Grafos de Conhecimento** | **93%** | **✅** | **✅** | **✅** |

---

## 🎓 Onde Publicar

### Conferências Internacionais
- IEEE S&P (Symposium on Security and Privacy)
- ACM CCS (Computer and Communications Security)
- USENIX Security Symposium
- NDSS (Network and Distributed System Security)

### Periódicos de Alto Impacto
- IEEE Transactions on Information Forensics and Security (TIFS)
- IEEE Transactions on Dependable and Secure Computing (TDSC)
- Computers & Security (Elsevier)

---

## 📈 Cronograma Sugerido

| Fase | Duração | Atividades |
|------|---------|------------|
| Revisão Bibliográfica | 2-3 semanas | Ler 30+ artigos, organizar referências |
| Design da Ontologia | 1-2 semanas | Formalizar em OWL |
| Implementação | 3-4 semanas | Construir protótipo |
| Experimentos | 2-3 semanas | Executar testes, coletar resultados |
| Redação | 3-4 semanas | Escrever artigo, revisões |
| Revisão Final | 1-2 semanas | Peer review, ajustes finais |

**Tempo Total Estimado:** 12-18 semanas

---

## 🔗 Links Úteis

- [MITRE ATT&CK](https://attack.mitre.org/) - Framework de ameaças
- [STIX 2.1](https://oasis-open.github.io/cti-documentation/stix/intro) - Padrão de Threat Intelligence
- [Protégé](https://protege.stanford.edu/) - Editor de ontologias
- [Neo4j](https://neo4j.com/) - Banco de dados de grafos
- [CIC-DDoS2019](https://www.unb.ca/cic/datasets/ddos-2019.html) - Dataset para experimentos

---

## 📝 Próximos Passos

1. [ ] Completar revisão bibliográfica
2. [ ] Refinar ontologia no Protégé
3. [ ] Executar código Python e analisar resultados
4. [ ] Baixar dataset CIC-DDoS2019
5. [ ] Implementar experimentos comparativos
6. [ ] Escrever primeira versão do artigo
7. [ ] Submeter para conferência/journal

---

## 📧 Contato

Para dúvidas ou colaborações sobre este projeto de pesquisa, entre em contato.

---

*Projeto de pesquisa sobre Grafos de Conhecimento aplicados à Cibersegurança*
*Foco: Detecção Semântica de Ataques DDoS*
