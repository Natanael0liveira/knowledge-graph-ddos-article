# Roadmap até *Computers & Security* (Qualis A2)

> **Documento de planejamento** específico para a submissão do paper [papers/http-session](papers/http-session/) — *Grafos de Conhecimento Centrados em Sessão HTTP para Detecção Explicável de DDoS*. Para a visão de projeto, ver [`README.md`](README.md). Para a estrutura do paper, ver [`ESTRUTURA_DO_ARTIGO.md`](ESTRUTURA_DO_ARTIGO.md).

---

## 1. Veículo-alvo e justificativa

**Primário:** *Computers & Security* (Elsevier), Qualis A2.

| Característica | Valor |
|---|---|
| Fator de Impacto | ≈ 3.5 |
| Taxa de aceitação | ≈ 30% |
| Tempo de revisão | 3–6 meses |
| Formato | Artigo completo, 8–10 páginas (preprint 12pt) |
| Cobertura | Segurança aplicada com abertura para ontologias e *explainability* |

**Alternativas:**

- *Journal of Network and Computer Applications* (Elsevier, A2, IF ≈ 5.1) — alvo se o trabalho expandir significativamente em volume e validação real.
- *Journal of Cybersecurity* (Oxford, A2) — alvo se a ênfase migrar para o lado de explicabilidade/operações de segurança.

**Por que C&S como primeiro alvo:** equilíbrio entre Qualis A2 e taxa de aceitação razoável, cobertura aceita ontologias de segurança, formato 8–10 páginas combina com o escopo enxuto do paper.

---

## 2. Análise de gap — estado atual vs. necessário

A análise está organizada por eixo de avaliação típico de revisores A2.

### 2.1 Contribuição científica

| Eixo | Estado atual | Necessário para A2 | Gap |
|---|---|---|---|
| **Originalidade** | Tese forte: sessão como entidade ontológica de primeira classe + raciocínio *cross-session* + KG em tempo de execução | Contribuição clara, defensável, com lacuna evidenciada por *survey* | ✅ Já evidenciada (Odusami, Liu, Kemp) |
| **Profundidade** | Esqueleto guiado em §2–§6 do `.tex` | Implementação, ontologia formalizada, regras SPARQL/SWRL | ❌ Implementar |
| **Comparação** | Baselines listados (Fernandes, Bharathi, Kemp) | Implementação real dos três baselines + ablação de duas vias | ❌ Implementar |
| **Reprodutibilidade** | Código de referência precursor em `src/graph_builder/` | Pipeline final, ontologia OWL pública, gerador sintético, *scripts* de experimento | 🔄 Refatorar e publicar |

### 2.2 Metodologia

| Eixo | Estado atual | Necessário para A2 | Gap |
|---|---|---|---|
| **Dataset primário** | Não produzido | Tráfego sintético parametrizado por **K** (grau de distribuição) para Cenários A/B/C | ❌ Produzir |
| **Dataset secundário** | Não usado | Subconjuntos CICIDS2017 (Slowloris/Slow HTTP) e CIC-DDoS2019 (componentes HTTP) para consistência | ❌ Preparar |
| **Baselines** | Listados em §4.4 | Três baselines implementados sobre o **mesmo conjunto de atributos** | ❌ Implementar |
| **Cenários** | A/B/C definidos em §4.1 | $n \ge 30$ execuções por cenário, *seeds* distintos | ❌ Executar |
| **Métricas** | Três famílias definidas em §4.5 | F1/AUC/FPR por cenário **+ *recall* por campanha** + qualitativo de explicação | ❌ Computar |
| **Análise estatística** | Não realizada | *Paired t-test*, Wilcoxon, Bonferroni | ❌ Aplicar |
| **Ablação** | Configurações (a)/(b)/(c) definidas em §4.6 | Executar e reportar (a)→(c) e (b)→(c) | ❌ Executar |

### 2.3 Escrita e estrutura

| Eixo | Estado atual | Necessário para A2 | Gap |
|---|---|---|---|
| **Idioma** | Português (preprint) | Inglês para submissão internacional | ❌ Traduzir |
| **Revisão bibliográfica** | Núcleo em [`shared/references.bib`](shared/references.bib); expandida em [`REFERENCIAS_EXPANDIDAS.md`](REFERENCIAS_EXPANDIDAS.md) | 40–60 referências bem usadas (não apenas listadas) | 🔄 Trazer ao `.tex` |
| **Formalização** | Algoritmo 1 em pseudocódigo | Definição formal de KG, ontologia em Turtle, regras em SPARQL/SWRL | ❌ Formalizar |
| **Figuras** | Diagrama de arquitetura (tikz) | + *money figure* (curva *recall* × K) + diagrama de ontologia + cadeia de evidência | ❌ Produzir |
| **Tabelas** | Estrutura prevista em §5 | Resultados quantitativos por cenário × ataque × baseline | ❌ Preencher |

---

## 3. Plano de ação por fase

### Fase 1 — Fundamentação (4–6 semanas)

**Objetivo:** transformar os esqueletos de §2 e §3 em prosa pronta para revisão, e fechar a ontologia formal.

#### 3.1.1 Escrita de §2 Trabalhos Relacionados

- Desenvolver as três subseções a partir das referências centrais já citadas:
  - §2.1 KGs em cibersegurança: Jia (2018), Bonagiri (2024), Liu (2022).
  - §2.2 Detecção HTTP Camada 7: Fernandes (2015), Bharathi (2012), Kemp (2023), Tripathi & Hubballi (2021).
  - §2.3 Modelagem de sessão: Odusami (2020).
- Sustentar o argumento de posicionamento (§2.4) nas três lacunas.

**Entregáveis:**
- [ ] §2 completa em PT no `.tex`
- [ ] 40–60 referências expandidas alinhadas ao escopo
- [ ] Mapa de leituras consolidado em [`docs/leituras-pt/`](docs/leituras-pt/)

#### 3.1.2 Formalização da ontologia (§3.2)

- Especificar `ApplicationSession` e as 5 relações em **Turtle**.
- Definir as três subclasses (`CoordinatedHTTPFlood`, `CredentialStuffing`, `CoordinatedAPIAbuse`) com `exhibitsCrossSessionStructure`.
- Validar consistência com *reasoner* (HermiT, Pellet).
- Mapeamento explícito para STIX 2.1 e MITRE ATT&CK T1498.001.

**Entregáveis:**
- [ ] `ontology/ddos_session_ontology.ttl` (recorte para sessão)
- [ ] `ontology/ddos_session_ontology.owl` (RDF/XML)
- [ ] Documentação de mapeamento STIX/ATT&CK

#### 3.1.3 Formalização das regras (§3.4)

- Reescrever as três regras em **SPARQL** (consulta) e/ou **SWRL** (regra DL).
- Parametrizar limiares ($\tau_{\text{fail}}$, $\tau_{\text{rate}}$, $\tau_{\text{api}}$) com método de calibração.
- Especificar a janela operacional $W$ e o efeito de purga.

**Entregáveis:**
- [ ] Conjunto de regras SPARQL/SWRL versionado
- [ ] Documento de calibração de limiares

#### 3.1.4 Formalização matemática mínima

Definições formais necessárias no `.tex`:

```latex
\begin{definition}[Grafo de Conhecimento de Sessão]
Um Grafo de Conhecimento de Sessão é uma tupla
$KG_W = (V, E, \tau, W)$ onde:
\begin{itemize}
  \item $V = V_{\text{sess}} \cup V_{\text{id}} \cup V_{\text{ep}} \cup V_{\text{beh}}$
        é o conjunto de vértices tipados;
  \item $E \subseteq V \times R \times V$ é o conjunto de arestas tipadas
        por $R = \{\texttt{hasIdentity}, \texttt{targets},
                   \texttt{exhibitsBehavior}, \texttt{relatedTo},
                   \texttt{mitigatedBy}\}$;
  \item $\tau$ é a função de carimbo temporal sobre vértices e arestas;
  \item $W$ é a janela operacional (padrão $W = 300\,s$).
\end{itemize}
\end{definition}

\begin{definition}[Estrutura Cross-Session]
Um conjunto $S \subseteq V_{\text{sess}}$ exibe estrutura cross-session se
$\exists\, s_i, s_j \in S, i \ne j$ tais que
$(s_i, \texttt{relatedTo}, s_j) \in E$.
\end{definition}
```

**Entregáveis:**
- [ ] Apêndice ou seção de formalização no `.tex`
- [ ] Análise de complexidade da construção do grafo e da execução das regras

---

### Fase 2 — Implementação e validação (6–8 semanas)

**Objetivo:** produzir os artefatos experimentais e os resultados das tabelas de §5.

#### 3.2.1 Gerador sintético parametrizado por **K** (grau de distribuição)

| Parâmetro | Cenário A | Cenário B | Cenário C |
|---|---|---|---|
| Número de origens distintas (**K**) | 1 | 10 ≤ K ≤ 100 | K ≥ 1000 |
| Identidades por origem | configurável | configurável | configurável |
| Tipo de ataque | um dos três | um dos três | um dos três |
| Tráfego legítimo concorrente | configurável | configurável | configurável |
| Janela temporal | configurável | configurável | configurável |

- Implementar o gerador como módulo Python reutilizável.
- Exportar tráfego em formato compatível com o *pipeline* (eventos HTTP estruturados com `tls_fingerprint`, `src_ip`, `session_id`, `identity_token`, `endpoint`).
- Para cada cenário × ataque, gerar $n \ge 30$ realizações com *seeds* distintas.

**Entregáveis:**
- [ ] `src/generator/synthetic_traffic.py`
- [ ] Conjuntos de tráfego: 3 cenários × 3 ataques × 30 *seeds* = 270 *runs*

#### 3.2.2 *Datasets* secundários para consistência

- **CICIDS2017** — subconjuntos Slowloris e Slow HTTP.
- **CIC-DDoS2019** — componentes HTTP.
- Pré-processar para o mesmo formato do tráfego sintético.
- Usar como *sanity check* dos resultados sintéticos, não como avaliação primária.

**Entregáveis:**
- [ ] `src/dataset_prep/cicids2017.py`
- [ ] `src/dataset_prep/cicddos2019.py`
- [ ] Documentação de mapeamento de campos

#### 3.2.3 Implementação dos três baselines

Todos consumindo o **mesmo conjunto subjacente de atributos** (taxa de requisições por sessão, duração, contagem de operações, entropia de rotas, razão de falha, etc.):

| Baseline | Aproximação | Implementação |
|---|---|---|
| Perfilamento estatístico | Fernandes et al. (2015) | PCA + limiarização sobre estatísticas de sessão |
| Matriz de comportamento | Bharathi & Sukanesh (2012) | *k-means* sobre matriz de *features* por sessão |
| ML supervisionado | Kemp et al. (2023) | Random Forest + SVM sobre o vetor de *features* |

**Princípio metodológico:** todos os baselines recebem **o mesmo material** que o arcabouço. A ablação isola a **representação semântica**, não a disponibilidade de atributos.

**Entregáveis:**
- [ ] `src/baselines/fernandes_pca.py`
- [ ] `src/baselines/bharathi_kmeans.py`
- [ ] `src/baselines/kemp_supervised.py`
- [ ] *Notebook* de calibração compartilhada de hiperparâmetros

#### 3.2.4 Refatoração do *pipeline* em tempo de execução

- Recortar `src/graph_builder/knowledge_graph_ddos.py` para o foco em sessão (remover/separar o que era DNS).
- Implementar `Algoritmo 1` (Construção do KG em Tempo de Execução) com a janela $W$ e a relação `relatedTo` populada por identidade/fingerprint/prefixo.
- Implementar as três regras semânticas e a emissão de cadeia de evidência em JSON-LD + STIX 2.1.

**Entregáveis:**
- [ ] `src/kg/session_kg.py` — construção em tempo de execução
- [ ] `src/kg/rules/` — uma regra por arquivo (HTTPFlood, CredentialStuffing, APIAbuse)
- [ ] `src/kg/evidence.py` — gerador de cadeia de evidência

#### 3.2.5 Execução experimental

**Protocolo:**

1. Para cada (cenário, ataque, *seed*), executar: 3 baselines + 3 configurações de ablação (a/b/c).
2. Calibrar limiares por cenário (manter consistente entre métodos).
3. Coletar métricas: precisão, *recall*, F1, AUC, FPR + ***recall* por campanha**.
4. Coletar amostras de cadeia de evidência para análise qualitativa.

**Análise estatística:**

- Média ± desvio sobre as $n$ *seeds*.
- *Paired t-test* (paramétrico) e Wilcoxon (não-paramétrico) método-a-método.
- Correção de Bonferroni para múltiplas comparações.
- $\alpha = 0{,}05$.

**Entregáveis:**
- [ ] `results/raw/` — métricas por *run* (CSV)
- [ ] `results/aggregated/` — métricas agregadas (média, IC, p-value)
- [ ] `results/figures/` — figuras prontas para o `.tex`
- [ ] `results/evidence_samples/` — cadeias de evidência amostradas

#### 3.2.6 *Money figure*

Curva de ***recall* × grau de distribuição (K)** para:

- 3 baselines (descendentes íngremes entre B e C)
- Configuração (b) — ontologia sem `relatedTo` (descendente, mas atenuado)
- Configuração (c) — arcabouço completo (estável)

**Entregável:**
- [ ] `results/figures/recall_vs_distribution.pdf` — figura central do paper

---

### Fase 3 — Escrita, revisão, submissão (4–6 semanas)

#### 3.3.1 Finalização da escrita

- **§4** — preencher com configuração real (versões de *software*, *seeds*, calibração de limiares).
- **§5** — preencher tabelas e figuras com resultados reais.
- **§6** — síntese curta + extensões.
- **Apêndices** — ontologia completa em Turtle/RDFXML; *scripts* de reprodução.

#### 3.3.2 Tradução PT → EN

- Tradução cuidadosa de §1 (já completa) e demais seções conforme forem concluídas.
- Revisão de inglês acadêmico, idealmente com revisor nativo ou serviço profissional.

#### 3.3.3 Checklist de qualidade para submissão A2

**Conteúdo:**
- [ ] Título específico (Grafos de Conhecimento Centrados em Sessão HTTP…)
- [ ] *Abstract* auto-contido (problema, lacuna, método, ablação, resultado, código)
- [ ] Contribuições numeradas (5 itens, já no `.tex`)
- [ ] §2 com taxonomia, comparação estruturada, posicionamento
- [ ] §3 com ontologia formal (Turtle), pipeline (Algoritmo 1), regras (SPARQL/SWRL)
- [ ] §4 metodologia reprodutível (cenários, gerador, baselines, métricas, ablação)
- [ ] §5 com tabelas + *money figure* + análise estatística + análise por ataque + análise qualitativa
- [ ] §6 conclusão + 4 direções de extensão
- [ ] **Limitações declaradas** (vantagem regime-específica, dependência de instrumentação, custo do grafo)

**Forma:**
- [ ] Inglês acadêmico revisado
- [ ] Formatação `elsarticle` correta
- [ ] Referências no estilo `elsarticle-num`
- [ ] Figuras legíveis (alvo de B&W aceitável)
- [ ] Repositório público com código, ontologia, gerador, *scripts* (após aceitação)
- [ ] Carta de submissão + declaração de Conflito de Interesse

---

## 4. Cronograma consolidado

| Fase | Duração | Marcos |
|---|---|---|
| **1 — Fundamentação** | 4–6 sem | §2 escrita; ontologia Turtle; regras SPARQL/SWRL; formalização matemática |
| **2 — Implementação e Validação** | 6–8 sem | Gerador sintético; 3 baselines; pipeline refatorado; *runs* completos; análise estatística; *money figure* |
| **3 — Escrita, Revisão, Submissão** | 4–6 sem | §4 e §5 preenchidos com resultados; §6 concluída; tradução PT→EN; revisão; submissão |
| **Total** | **14–20 semanas** | Submissão a *Computers & Security* |

---

## 5. Ações prioritárias

### Crítico (gating para A2)

1. **Gerador sintético parametrizado por K** — sem isso, não há Cenários A/B/C, não há *money figure*.
2. **Implementação dos três baselines** sobre o mesmo conjunto de atributos.
3. **Pipeline refatorado** com `relatedTo` populada por identidade/fingerprint/prefixo.
4. **Ablação executada** — configurações (a)/(b)/(c).
5. **Análise estatística** — IC, *paired t-test*, Wilcoxon, Bonferroni, $n \ge 30$ *seeds*.
6. **Tradução PT → EN** revisada.

### Importante (eleva a qualidade da defesa)

7. **Ontologia formal em Turtle** validada com *reasoner*.
8. **Regras em SPARQL/SWRL** versionadas.
9. **Cadeia de evidência exportável** em JSON-LD e STIX 2.1, com exemplos no `.tex`.
10. **Validação em *datasets* secundários** (CICIDS2017, CIC-DDoS2019) como *sanity check*.
11. **Análise por ataque** (§5.3) identificando o nível mínimo de K em que cada baseline começa a falhar.

### Recomendado (valoriza o trabalho, mas não bloqueia)

12. **Estudo qualitativo com analistas** sobre completude/acionabilidade das cadeias de evidência (§5.5).
13. **Análise de custo de manutenção do grafo** em função de $W$ e da taxa de requisições.
14. **Demonstração de integração SIEM** (PoC importando o JSON-LD/STIX).

---

## 6. Riscos e mitigação

| Risco | Mitigação |
|---|---|
| Gerador sintético gera tráfego "fácil demais" e infla o ganho do arcabouço | Calibrar contra distribuições de tráfego real de literatura; validar com *datasets* secundários |
| Baselines mal implementados subestimam o estado da arte | Documentar implementação como aproximação fiel das referências; publicar código junto |
| *Recall* do arcabouço também cai em Cenário C | Caso real do paper: ainda mantém vantagem relativa significativa; reportar honestamente |
| Revisores pedem dados reais | Resposta planejada: §4.2 declara que dados reais anonimizados são direção futura sujeita a aprovação ética; *datasets* secundários servem como ponte |
| Vantagem do raciocínio *cross-session* é marginal em todos os cenários | Refazer a análise considerando se o sinal estrutural foi populado corretamente (identidade/fingerprint/prefixo); se persistir, ajustar a tese antes de submeter |

---

## 7. Síntese

Para chegar a *Computers & Security* (Qualis A2), o projeto deve evoluir de **esqueleto guiado** para **validação científica completa**. Os blocos são:

1. **Fechamento conceitual** — §2 escrita, ontologia em Turtle, regras em SPARQL/SWRL.
2. **Validação experimental** — gerador parametrizado, 3 baselines, ablação (a/b/c), análise estatística com Bonferroni, *money figure* (recall × K).
3. **Apresentação A2** — inglês acadêmico, formato `elsarticle`, repositório público, carta de submissão e declaração de COI.

A contribuição (sessão como entidade + raciocínio *cross-session* + KG em tempo de execução) já está bem evidenciada pela literatura citada. O trabalho remanescente é predominantemente **execução**, não redirecionamento.

---

*Documento de planejamento da submissão do paper [papers/http-session](papers/http-session/) a *Computers & Security*.*
*Última atualização: Maio 2026.*
