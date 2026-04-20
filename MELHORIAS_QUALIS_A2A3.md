# Roadmap para Nível Qualis A2/A3

## Análise de Gap e Recomendações

Este documento analisa os requisitos para elevar o projeto e artigo ao nível Qualis A2 ou A3, com base nos critérios da CAPES e melhores práticas acadêmicas.

---

## 1. O que é o Qualis?

O **Qualis** é o sistema de classificação de periódicos e conferências utilizado pela CAPES para avaliar a pós-graduação no Brasil. A classificação vai de A1 (mais alto) a C (mais baixo).

| Estrato | Características | Fator de Impacto Médio |
|---------|-----------------|------------------------|
| **A1** | Top mundial, altíssimo impacto | > 5.0 |
| **A2** | Alto impacto internacional | 2.0 - 5.0 |
| **A3** | Impacto internacional relevante | 1.0 - 2.0 |
| **A4** | Impacto regional/nacional | 0.5 - 1.0 |
| **B1-B4** | Menor impacto | < 0.5 |

### Conferências Qualis A2/A3 em Segurança/Redes

| Conferência | Qualis | Aceitação | Área |
|-------------|--------|-----------|------|
| IEEE S&P | A1 | ~10% | Segurança |
| ACM CCS | A1 | ~15% | Segurança |
| USENIX Security | A1 | ~12% | Segurança |
| NDSS | A1 | ~18% | Segurança |
| **ACM SIGCOMM** | **A1** | ~15% | Redes |
| **IEEE TNSM** | **A2** | ~25% | Gerência de Redes |
| **IEEE/ACM ToN** | **A1** | ~20% | Redes |
| **Computers & Security** | **A2** | ~30% | Segurança |
| **Journal of Cybersecurity** | **A2** | ~25% | Cibersegurança |

### Periódicos Qualis A2/A3 em Segurança

| Periódico | Qualis | Fator de Impacto |
|-----------|--------|-------------------|
| IEEE TIFS | A1 | 7.2 |
| IEEE TDSC | A1 | 6.5 |
| ACM TOPS | A1 | 5.8 |
| **Computers & Security** | **A2** | 3.5 |
| **J. Network and Computer Applications** | **A2** | 5.1 |
| **Digital Investigation** | **A3** | 2.1 |
| **Information Security Journal** | **A3** | 1.8 |

---

## 2. Análise de Gap: Estado Atual vs. Necessário

### 2.1 Contribuição Científica

| Aspecto | Estado Atual | Necessário para A2/A3 | Gap |
|---------|--------------|----------------------|-----|
| **Originalidade** | Boa - ontologia específica para Layer 7 | Alta - contribuição clara e distinta | ⚠️ Refinar |
| **Profundidade** | Média - implementação de prova de conceito | Alta - validação extensiva | ❌ Melhorar |
| **Comparação** | Básica - tabela comparativa | Robusta - baseline experimental | ❌ Implementar |
| **Reprodutibilidade** | Código disponível | Dataset + código + protocolo | ⚠️ Completar |

### 2.2 Metodologia

| Aspecto | Estado Atual | Necessário para A2/A3 | Gap |
|---------|--------------|----------------------|-----|
| **Dataset** | Simulação própria | Dataset público (CIC-DDoS2019) | ❌ Usar dataset real |
| **Baseline** | Tabela teórica | Implementação e comparação real | ❌ Implementar |
| **Métricas** | Definidas | Análise estatística completa | ❌ Implementar |
| **Validação** | Simulação | Validação cruzada, múltiplos cenários | ❌ Implementar |

### 2.3 Escrita e Estrutura

| Aspecto | Estado Atual | Necessário para A2/A3 | Gap |
|---------|--------------|----------------------|-----|
| **Revisão Bibliográfica** | 23 referências | 50+ referências atualizadas | ❌ Expandir |
| **Formalização** | Básica | Formalismo matemático completo | ❌ Melhorar |
| **Visualizações** | Diagramas básicos | Figuras de alta qualidade | ⚠️ Melhorar |
| **Escrita** | Português | Inglês (internacionalização) | ❌ Traduzir |

---

## 3. Plano de Ação Detalhado

### Fase 1: Fundamentação Teórica (4-6 semanas)

#### 3.1.1 Revisão Bibliográfica Sistemática

**Objetivo:** Expandir de 23 para 50+ referências relevantes e atualizadas.

**Ações:**
1. Busca sistemática em bases (IEEE Xplore, ACM DL, Scopus)
2. Foco em artigos 2020-2025 sobre:
   - Knowledge Graphs em cibersegurança
   - DDoS detection com ML/DL
   - Ontologias de segurança
   - Graph Neural Networks para detecção
3. Identificar gaps na literatura para posicionar contribuição

**Entregáveis:**
- [ ] Tabela de 50+ referências categorizadas
- [ ] Mapa conceitual do estado-da-arte
- [ ] Identificação clara do gap de pesquisa

#### 3.1.2 Formalização Matemática

**Objetivo:** Formalizar completamente o modelo proposto.

**Elementos necessários:**

```latex
% Definição formal do Grafo de Conhecimento
\begin{definition}
Um Grafo de Conhecimento para DDoS é uma tupla $KG = (E, R, P, \phi)$ onde:
\begin{itemize}
    \item $E = \{e_1, e_2, ..., e_n\}$ é o conjunto de entidades
    \item $R = \{r_1, r_2, ..., r_m\}$ é o conjunto de relações
    \item $P = \{p_1, p_2, ..., p_k\}$ é o conjunto de propriedades
    \item $\phi: E \times R \times E \rightarrow [0,1]$ é a função de peso
\end{itemize}
\end{definition}

% Teorema de detecção
\begin{theorem}
Dado um grafo $KG$ e um conjunto de regras $\mathcal{R}$, 
a detecção de anomalias $A$ é computável em $O(|E| \cdot |R|)$.
\end{theorem}
```

**Entregáveis:**
- [ ] Definições formais de todas as estruturas
- [ ] Teoremas e provas de corretude/completude
- [ ] Análise de complexidade algorítmica

### Fase 2: Implementação e Validação (6-8 semanas)

#### 3.2.1 Dataset e Pré-processamento

**Dataset recomendado: CIC-DDoS2019**

| Característica | Valor |
|----------------|-------|
| Tamanho | ~15 GB |
| Tipos de ataque | 12 (inclui HTTP Flood, DNS amplification) |
| Amostras | ~50 milhões |
| Features | 80+ |

**Ações:**
1. Download e extração do dataset
2. Pré-processamento:
   - Normalização de features
   - Balanceamento de classes
   - Divisão treino/teste/validação (70/15/15)
3. Feature engineering específica para Layer 7

**Entregáveis:**
- [ ] Pipeline de pré-processamento documentado
- [ ] Estatísticas do dataset processado
- [ ] Scripts reprodutíveis

#### 3.2.2 Baselines de Comparação

**Implementar e comparar com:**

| Método | Tipo | Referência | Razão |
|--------|------|------------|-------|
| Random Forest | ML tradicional | Breiman (2001) | Baseline clássico |
| XGBoost | Gradient Boosting | Chen (2016) | Estado-da-arte em ML |
| LSTM | Deep Learning | Hochreiter (1997) | Sequências temporais |
| GCN | Graph Neural Network | Kipf (2017) | Grafos |
| Autoencoder | Anomaly Detection | An (2015) | Não supervisionado |

**Métricas de avaliação:**

| Métrica | Fórmula | Meta |
|---------|---------|------|
| Accuracy | (TP+TN)/(TP+TN+FP+FN) | > 95% |
| Precision | TP/(TP+FP) | > 93% |
| Recall | TP/(TP+FN) | > 92% |
| F1-Score | 2×(P×R)/(P+R) | > 92% |
| AUC-ROC | Área sob curva ROC | > 0.95 |
| FPR | FP/(FP+TN) | < 2% |
| Tempo Detecção | t_detect - t_start | < 100ms |

**Entregáveis:**
- [ ] Implementação de 5+ baselines
- [ ] Tabela comparativa completa
- [ ] Análise estatística (testes t, ANOVA)

#### 3.2.3 Validação Experimental

**Protocolo de validação:**

1. **Validação Cruzada 10-fold**
   - Particionar dataset em 10 folds
   - Treinar em 9, testar em 1
   - Repetir 10 vezes
   - Reportar média ± desvio padrão

2. **Testes de Significância**
   - Teste t pareado vs. baselines
   - Correção Bonferroni para múltiplas comparações
   - Nível de significância α = 0.05

3. **Análise de Ablação**
   - Remover cada componente do sistema
   - Medir impacto na performance
   - Identificar componentes críticos

4. **Análise de Escalabilidade**
   - Testar com diferentes volumes de dados
   - Medir tempo de processamento
   - Identificar gargalos

**Entregáveis:**
- [ ] Resultados de validação cruzada
- [ ] Testes estatísticos documentados
- [ ] Análise de ablação
- [ ] Gráficos de escalabilidade

### Fase 3: Escrita e Submissão (4-6 semanas)

#### 3.3.1 Estrutura do Artigo (8-10 páginas)

```
1. Abstract (200-250 palavras)
2. Introduction (1.5 páginas)
   - Contexto e motivação
   - Problema e gap
   - Contribuições (lista clara)
3. Related Work (1.5 páginas)
   - Taxonomia de abordagens
   - Comparação estruturada
   - Posicionamento do trabalho
4. Proposed Approach (2.5 páginas)
   - Formalização matemática
   - Arquitetura do sistema
   - Ontologia OWL
   - Algoritmos de detecção
5. Experimental Evaluation (2 páginas)
   - Setup experimental
   - Dataset e baselines
   - Resultados e análise
   - Discussão de limitações
6. Conclusion (0.5 páginas)
   - Resumo das contribuições
   - Trabalhos futuros
7. References (1 página)
```

#### 3.3.2 Elementos Essenciais para A2/A3

**1. Contribuições Claras e Numeradas:**

```
As principais contribuições deste trabalho são:
1. Uma ontologia OWL formal para modelagem de ataques DDoS 
   de Camada 7, alinhada com STIX 2.1 e MITRE ATT&CK.
2. Um framework de detecção baseado em grafos de conhecimento 
   com raciocínio semântico explicável.
3. Uma metodologia de avaliação experimental abrangente 
   usando dataset público e múltiplos baselines.
4. Uma análise comparativa demonstrando superioridade sobre 
   métodos tradicionais em precisão e explicabilidade.
```

**2. Figuras de Alta Qualidade:**

| Figura | Descrição | Tipo |
|--------|-----------|------|
| Fig. 1 | Arquitetura do sistema | Diagrama |
| Fig. 2 | Ontologia OWL | Grafo |
| Fig. 3 | Pipeline de detecção | Fluxograma |
| Fig. 4 | Resultados comparativos | Gráfico de barras |
| Fig. 5 | ROC curves | Gráfico de linhas |
| Fig. 6 | Análise de ablação | Gráfico |
| Fig. 7 | Escalabilidade | Gráfico |

**3. Tabelas Estruturadas:**

| Tabela | Descrição |
|--------|-----------|
| Tab. 1 | Comparação com trabalhos relacionados |
| Tab. 2 | Classes e relações da ontologia |
| Tab. 3 | Regras de detecção semânticas |
| Tab. 4 | Estatísticas do dataset |
| Tab. 5 | Resultados experimentais |
| Tab. 6 | Análise de ablação |

#### 3.3.3 Checklist de Qualidade

**Conteúdo:**
- [ ] Título claro e específico
- [ ] Abstract auto-contido (problema, método, resultados)
- [ ] Introdução com contribuições numeradas
- [ ] Related work com taxonomia e comparação
- [ ] Metodologia reprodutível
- [ ] Resultados com análise estatística
- [ ] Discussão de limitações
- [ ] Conclusão com trabalhos futuros

**Forma:**
- [ ] Inglês acadêmico correto
- [ ] Formatação do veículo alvo
- [ ] Referências no estilo correto
- [ ] Figuras legíveis em P&B
- [ ] Código disponível (GitHub)
- [ ] Dataset documentado

**Reprodutibilidade:**
- [ ] Código fonte disponível
- [ ] Dataset público utilizado
- [ ] Hiperparâmetros documentados
- [ ] Ambiente experimental descrito
- [ ] Scripts de reprodução incluídos

---

## 4. Cronograma Proposto

| Fase | Duração | Atividades | Entregáveis |
|------|---------|------------|-------------|
| **1. Fundamentação** | 4-6 sem | Revisão bibliográfica, formalização | 50+ refs, formalismo |
| **2. Implementação** | 6-8 sem | Dataset, baselines, experimentos | Resultados completos |
| **3. Escrita** | 4-6 sem | Redação, revisão, submissão | Artigo submetido |
| **Total** | **14-20 sem** | | **Artigo Qualis A2/A3** |

---

## 5. Veículos-Alvo Recomendados

### Opção 1: Computers & Security (Elsevier) - Qualis A2

| Característica | Valor |
|----------------|-------|
| Fator de Impacto | 3.5 |
| Taxa de Aceitação | ~30% |
| Tempo de Revisão | 3-6 meses |
| Tipo | Periódico |
| Formato | Artigo completo (8-10 pág) |

**Por que este veículo?**
- Foco em segurança aplicada
- Aceita trabalhos com ontologias
- Comunidade acadêmica ativa
- Indexação ampla

### Opção 2: Journal of Network and Computer Applications - Qualis A2

| Característica | Valor |
|----------------|-------|
| Fator de Impacto | 5.1 |
| Taxa de Aceitação | ~25% |
| Tempo de Revisão | 4-8 meses |
| Tipo | Periódico |
| Formato | Artigo completo (10-12 pág) |

**Por que este veículo?**
- Foco em aplicações de redes
- Relevância para DDoS
- Alto fator de impacto

### Opção 3: IEEE International Conference on Communications (ICC) - Qualis A2

| Característica | Valor |
|----------------|-------|
| Taxa de Aceitação | ~35% |
| Tempo de Revisão | 3 meses |
| Tipo | Conferência |
| Formato | 6-8 páginas |

**Por que este veículo?**
- Comunidade de redes
- Proceedings indexados
- Networking acadêmico

---

## 6. Resumo das Ações Prioritárias

### Crítico (deve fazer)

1. **Usar dataset público real** (CIC-DDoS2019)
2. **Implementar baselines** (RF, XGBoost, LSTM, GCN)
3. **Análise estatística completa** (validação cruzada, testes t)
4. **Traduzir para inglês** (veículos internacionais)
5. **Expandir revisão bibliográfica** (50+ referências)

### Importante (deve considerar)

6. **Formalização matemática completa**
7. **Análise de ablação**
8. **Análise de escalabilidade**
9. **Código disponível no GitHub**
10. **Figuras de alta qualidade**

### Recomendado (valoriza o trabalho)

11. **Comparação com GNNs**
12. **Dataset adicional** (validação cruzada de datasets)
13. **Case study** (cenário real ou semi-real)
14. **Integração com SIEM** (demonstração prática)

---

## 7. Conclusão

Para atingir nível Qualis A2/A3, o projeto precisa evoluir de uma **prova de conceito** para uma **validação científica rigorosa**. Os principais gaps são:

1. **Validação experimental** com dataset público
2. **Comparação robusta** com estado-da-arte
3. **Formalização matemática** completa
4. **Escrita em inglês** para veículos internacionais

O cronograma de 14-20 semanas é factível para um pesquisador dedicado, e o trabalho já tem uma base sólida (ontologia, implementação, estrutura). O foco deve ser em **completar a validação experimental** e **formalizar a contribuição científica**.

---

*Documento criado para orientar a elevação do projeto ao nível Qualis A2/A3*  
*Última atualização: Abril 2026*
