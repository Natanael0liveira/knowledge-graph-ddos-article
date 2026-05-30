# Plano de Ação Consolidado — Paper http-session

> **Data de elaboração:** 2026-05-30
> **Escopo:** consolidar (i) as lacunas conceituais identificadas após a leitura de KLAGE e a revisão crítica do framing e (ii) o roadmap experimental que produz os dados necessários para defesa do paper.

---

## Visão geral

Duas fases, sequenciais, com gates de aprovação entre fases:

| Fase | Foco | Duração estimada | Saída principal |
|---|---|---|---|
| **Fase A** | Endurecimento conceitual do `.tex` | ~1 semana | Paper revisado, com lacunas conceituais explicitamente endereçadas |
| **Fase B** | Validação experimental | ~5 semanas | Resultados reais, calibração de pesos, comparação com KLAGE, *money figure* |

Princípio orientador: **a Fase A precede a Fase B** porque o paper escrito determina o que precisa ser medido. Não rodamos experimento antes de saber qual pergunta empírica ele responde.

---

## Fase A — Endurecimento conceitual

### A1. Algoritmos de instanciação das sub-relações `relatedBy_*` (Lacuna 1)

**Problema:** §3.3 declara que cada sub-propriedade é "instanciada independentemente a partir de seu sinal específico", sem especificar o algoritmo. Um revisor experiente pedirá: como exatamente o pipeline decide que `(s_a, relatedByTemporalPattern, s_b)` é instanciada?

**Entregável:** nova subseção §3.3.1 "Algoritmos de Instanciação das Sub-relações", com pseudocódigo ou especificação formal para cada uma das seis sub-propriedades. Mínimo:

| Sub-propriedade | Especificação |
|---|---|
| `relatedByTLSFingerprint` | Match exato de JA4. Se variantes próximas (JA4_a), match por edit distance ≤ 1 |
| `relatedByReusedIdentity` | Match exato de pelo menos um identificador entre `{cookie, token JWT (após decode), username}` |
| `relatedByTemporalPattern` | Dynamic Time Warping (DTW) sobre o vetor de inter-arrival-times das requisições, normalizado pela duração; instancia se DTW < `τ_DTW` |
| `relatedByPayloadSignature` | Cosine similarity sobre vetor de [tamanho médio, std, User-Agent hash, content-type]; instancia se similaridade > `τ_payload` |
| `relatedByEndpointConvergence` | Match exato do `path` (não só `endpoint type`); ou match por regex `path_pattern` |
| `relatedByNetworkProximity` | Match exato de prefixo /24 OU match exato de ASN |

**Tempo estimado:** 1–2 dias de escrita. Custo zero de dados.

### A2. Calibração de pesos `w_i` justificada (Lacuna 2)

**Problema:** pesos $w_{\text{TLS}} = 1{,}0$, $w_{\text{identity}} = 1{,}0$, $w_{\text{temporal}} = 0{,}9$, $w_{\text{payload}} = 0{,}6$, $w_{\text{endpoint}} = 0{,}6$, $w_{\text{network}} = 0{,}3$ são declarados arbitrariamente.

**Decisão:** adotar o **Caminho B** (calibração empírica por *grid search* em conjunto de validação separado).

**Entregável imediato em §3.2:** nota explicitando que os pesos iniciais são *priors* derivados de propriedades conhecidas de evasão (citando Cloudflare 2025, Cambiaso 2013, Althouse) e serão refinados empiricamente em §5 sobre o conjunto de validação. A análise de sensibilidade dos pesos faz parte dos resultados experimentais.

**Tempo estimado:** 30 min de escrita (em §3.2 e §5.4). A calibração efetiva ocorre na Fase B (Sprint 4).

### A3. Recorte de escopo: HTTP/2 Rapid Reset como extensão futura (Lacuna 3)

**Problema técnico real:** Rapid Reset é caracterizado por *alta taxa de cancelamento de stream* (RST_STREAM), não por *conexões prendidas*. A regra `CoordinatedHTTPFlood` calibrada para conexões longas não detecta Rapid Reset; precisaria de uma nova sub-relação como `relatedByStreamCancellationPattern`.

**Decisão:** recortar o escopo. Rapid Reset, CONTINUATION Flood e MadeYouReset passam a ser mencionados em §1.1 como **categoria adjacente** da família HTTP/2 cuja detecção requer extensão direta da ontologia, deixada como **trabalho futuro explícito** em §6. A avaliação experimental se concentra em Slowloris e suas variantes diretas (slow body, slow read, HULK, GoldenEye).

**Entregável:** revisão de §1.1 e §6 para reposicionar HTTP/2 Rapid Reset como extensão. Substituir frases que sugerem cobertura presente por menções a "extensibilidade da ontologia".

**Tempo estimado:** 30 min de escrita.

### A4. Adversidade adaptativa (Lacuna 4)

**Problema:** atacantes sofisticados podem (i) usar `curl-impersonate` para forjar JA4 de Chrome legítimo; (ii) introduzir *jitter* aleatório no padrão temporal; (iii) rotacionar identidades; (iv) randomizar payload. Não discutimos.

**Entregável:** nova subseção §5.7.5 (ou item adicional em §5.7) "Adversidade adaptativa e degradação esperada", com:

- Reconhecimento explícito dos quatro vetores de evasão acima
- Argumento de que `relatedTo` é uma família precisamente para sobreviver a quebra parcial: quando JA4 é forjado, identidade reaproveitada e padrão temporal carregam; quando padrão temporal é jittered, JA4 + identidade carregam
- Reconhecimento honesto: quebra simultânea de **três ou mais** sinais de peso alto degrada o arcabouço para próximo de aleatório
- Trabalho futuro em §6: avaliação dirigida sob atacante adaptativo

**Tempo estimado:** 1 dia de escrita.

### A5. Performance do *reasoner* (Lacuna 5)

**Problema:** SPARQL/SWRL em tempo de execução com 10k+ sessões ativas não é trivial. HermiT/Pellet são notoriamente lentos.

**Entregável:** nota técnica em §3.3 (sobre o pipeline) e item em §5.7 (limitações):

- Pipeline usa **OWL 2 RL profile** (não DL completo), permitindo *reasoning* materializado e consultas SPARQL em índice
- *Backend* recomendado: Apache Jena Fuseki com TDB2, ou GraphDB Free
- Janela $W$ implementada como *sliding window* com purga incremental; complexidade $O(|sessões ativas| \cdot |sub-relações|)$ por requisição
- Performance medida na Fase B (latência média de inserção, latência média de consulta SPARQL para a regra)
- Citar literatura de RDF Stream Processing (Dell'Aglio et al. 2017) como referencial

**Tempo estimado:** 1 dia de escrita.

### A6. Correção dos exemplos do Diagrama 2 (cosmético, mas vale)

**Problema:** Diagrama 2 mistura IPs reais (45.142.x.x, 91.236.x.x) com IPs RFC 5737 (203.0.113.x). Mistura ASNs reais (8075 = Microsoft, 7922 = Comcast) com privados (64999).

**Entregável:** padronizar para RFC 5737 (`192.0.2.0/24`, `198.51.100.0/24`, `203.0.113.0/24`) nos IPs, e RFC 5398 (`64496–64511`) nos ASNs, com nota indicando origem RFC.

**Tempo estimado:** 15 min.

### Checkpoint Fase A

Ao final da Fase A: paper deve estar pronto para uma leitura de revisor cético sem buracos visíveis. Antes de partir para Fase B, **fazer uma releitura completa do `.tex`** para garantir consistência entre as seções modificadas.

---

## Fase B — Validação experimental (5 sprints)

### Princípios transversais

Antes dos sprints, decisões válidas para toda a Fase B:

1. **Reprodutibilidade**: `requirements.txt` com versões fixas; SHA-256 dos *datasets*; *seeds* explícitas; YAMLs de configuração; logs em JSON; `Makefile` orquestrando.
2. **Separação treino/validação/teste**: 40% treino (para baselines ML), 30% validação (para calibração de pesos e tuning), 30% teste (apenas para reportar resultados finais — não retocado durante o desenvolvimento).
3. **Estatística**: $n \ge 30$ runs por configuração; intervalos de confiança via *bootstrap*; *paired t-test* + Wilcoxon entre métodos; correção de Bonferroni; reportar *effect size* (Cohen's d) junto com p-values.
4. **Otimização computacional**: cachear extrações em Parquet; paralelizar ablação via `joblib`; usar DuckDB para joins; *backend* RDF com TDB2.
5. **Documentação executável**: cada sprint produz scripts em `experiments/sprint-N/` + README.

### Sprint 1 — Pipeline de extração (PCAP → grafo)

**Goal:** ter um *pipeline* automatizado e validado que processa PCAP → JA4 → sessões → KG. Demonstração *end-to-end* em amostra pequena (~100 MB–1 GB) antes de escalar para o *dataset* completo.

**Princípio de design:** **scripts pré-escritos por mim, executados unattended por você**. Seu envolvimento ativo: ~6 h total, distribuídas em ~14 dias calendário. A maior parte do tempo de *wall clock* é processamento que roda sozinho.

| Etapa | Seu tempo | Wall clock | O que você faz |
|---|---|---|---|
| **E1. Setup do ambiente** | ~1 h | imediato | Clonar repo, instalar dependências (`make sprint-1-setup`); criar conta UNB para CIC-DDoS2019 |
| **E2. Validação em PCAP pequeno** | ~30 min | ~5 min | Baixar PCAP de exemplo (~100 MB, link público fornecido no README); rodar `make sprint-1-test`; conferir output |
| **E3. Download CIC-DDoS2019 (subconjunto Slowloris)** | ~10 min | 8–24 h (overnight) | Disparar `make sprint-1-download` antes de dormir; volta no dia seguinte |
| **E4. Extração JA4 + flows** | ~5 min | 2–6 h (background) | Disparar `make sprint-1-extract`; deixa rodando, recebe notificação ao terminar |
| **E5. Reconstrução de sessões** | ~10 min | 30 min | Rodar `make sprint-1-sessions`; é rápido após extração |
| **E6. Derivação de cluster ground truth** | ~30 min | 10 min + revisão | Rodar `make sprint-1-cluster`; revisar amostra de 10 *clusters* validados |
| **E7. Carga no Apache Jena Fuseki** | ~30 min | 1 h (background) | Rodar `make sprint-1-load-kg`; validar com 3 SPARQL queries de teste |
| **E8. Validação final + relatório** | ~2 h | ~1 h | Rodar notebook Jupyter `validate.ipynb` que produz relatório com gráficos; revisar |
| **Buffer para troubleshooting** | ~1 h | — | Espaço para imprevistos |
| **Total** | **~6 h** | **~10–30 h wall clock** | espalhadas em 10–14 dias calendário |

**O que MEU trabalho prévio entrega:**

- `experiments/sprint-1/Makefile` com targets nomeados (`setup`, `test`, `download`, `extract`, `sessions`, `cluster`, `load-kg`)
- `experiments/sprint-1/scripts/`:
  - `extract_ja4.py` — wrapper sobre `tshark` ou `pyja4` para PCAP → CSV de JA4
  - `extract_flows.py` — wrapper sobre `CICFlowMeter` ou implementação Python equivalente
  - `build_sessions.py` — reconstrução de sessões a partir de flows + JA4
  - `derive_clusters.py` — *ground truth* de *cluster* via heurística + amostra para revisão
  - `load_to_fuseki.py` — carga das sessões como triplas RDF em Fuseki
- `experiments/sprint-1/notebooks/validate.ipynb` — análise exploratória dos *outputs*
- `experiments/sprint-1/docker-compose.yml` — Fuseki + reasoner rodando em container
- `experiments/sprint-1/README.md` — instruções *passo a passo*

**Gates de aprovação ao final do Sprint 1:**

- E2 (PCAP pequeno) produz JA4 não-vazio para pelo menos um *handshake* TLS observado
- E5 produz `sessions.parquet` com pelo menos 80% dos flows originais mapeados em sessões
- E6 produz amostra de 10 *clusters* validados manualmente (você confirma que faz sentido)
- E7 carga no Fuseki responde a `SELECT (COUNT(*) AS ?n) WHERE { ?s a :ApplicationSession }` com $n \ge 1000$ (Slowloris CIC-DDoS2019 deve ter mais)
- E8 notebook gera relatório com distribuições de JA4, duração de sessão, e estatísticas básicas

**Riscos previstos e mitigação:**

| Risco | Mitigação |
|---|---|
| CIC-DDoS2019 muito grande para laptop (~80 GB total) | Script só baixa o subconjunto Slowloris/Slow HTTP (~5–10 GB) |
| `pyja4` falha em PCAPs antigos | Fallback automático para `tshark` com plugin JA4 (TShark 4.x+) já configurado no Makefile |
| *Ground truth* difícil de derivar de ataques single-source | E6 produz *clusters* sintéticos por janela temporal; ground truth real é só validação parcial, complementada pelo Sprint 2 (gerador) |
| Você não tem 8h consecutivas para acompanhar | Não precisa: tudo é orquestrado em targets do Makefile que rodam unattended e gravam logs |

### Sprint 2 — Gerador sintético calibrado

**Goal:** implementar gerador parametrizado por K (grau de distribuição) e demais variáveis, calibrado a partir das distribuições reais extraídas no Sprint 1.

| Dia | Atividade | Saída |
|---|---|---|
| 1 | Extrair distribuições de tráfego legítimo do Sprint 1 (taxa, endpoints, JA4 entre usuários, duração de sessão) | `analysis/legitimate_distributions.json` |
| 2–3 | Implementar gerador modular (`src/synth/generator.py`): legítimo + ataque coordenado parametrizado | Gerador funcional |
| 4 | Implementar variantes de ataque (`slowloris`, `slow_body`, `slow_read`, `hulk`, `goldeneye`) | Cobertura da família |
| 5 | Validação visual: gráficos lado a lado de "legítimo sintético" vs "legítimo real" do Sprint 1 | Relatório de calibração |
| 6 | Geração dos *datasets* para Cenários A, B, C ($n \ge 30$ *seeds* cada) | `data/synth/scenarios/A/`, `B/`, `C/` |
| 7 | Documentação do gerador + README de reprodução | `experiments/sprint-2/README.md` |

**Tempo total:** ~1 semana.

**Gates:**

- Distribuições estatísticas do legítimo sintético dentro de 10% das do real (teste KS)
- Para cada cenário, ground truth de cluster perfeitamente conhecida (porque foi gerada)
- Reprodutibilidade: rodar duas vezes com mesma *seed* produz output bit-idêntico

### Sprint 3 — Baselines + ablação

**Goal:** implementar (i) os três *baselines* acadêmicos, (ii) as quatro configurações de ablação, sobre o mesmo conjunto de atributos. Resultados preliminares no Cenário A.

| Dia | Atividade | Saída |
|---|---|---|
| 1 | *Baseline* Fernandes 2015 — PCA + limiarização | `src/baselines/fernandes.py` |
| 2 | *Baseline* Bharathi 2012 — k-means em matriz comportamental | `src/baselines/bharathi.py` |
| 3 | *Baseline* Kemp 2023 — Random Forest + SVM | `src/baselines/kemp.py` |
| 4 | Configuração (a): ML sem ontologia; (b): ontologia sem `relatedBy_*`; (c): só `relatedByNetworkProximity` | `src/ablation/configs/` |
| 5 | Configuração (d): arcabouço completo | `src/ablation/configs/d.yaml` |
| 6 | Execução em Cenário A; checar que (a) e baselines convergem em resultados similares (sanity) | Resultados preliminares |
| 7 | Refinamento e debug | Pipeline estável |

**Tempo total:** ~1 semana.

**Gates:**

- *Baselines* reproduzem (dentro de ±5%) os números reportados nos papers originais quando aplicáveis
- Configurações (a), (b), (c), (d) consomem o **mesmo** input
- Em Cenário A, configurações (a)–(d) têm desempenho similar (sanity check: o ganho da família relatedTo só aparece em B/C)

### Sprint 4 — Execução completa + calibração de pesos

**Goal:** rodar a grade completa de experimentos, calibrar pesos $w_i$ via *grid search* sobre conjunto de validação, produzir resultados estatisticamente significativos.

| Dia | Atividade | Saída |
|---|---|---|
| 1 | Grid search dos pesos $w_i$ (Caminho B); domínio: $\{0{,}3, 0{,}5, 0{,}7, 0{,}9, 1{,}0\}^6$ sobre conjunto de validação | Pesos finais + análise de sensibilidade |
| 2 | Execução paralela: 4 configurações × 3 cenários × ≥ 30 *seeds* = 360+ runs | `results/raw/` |
| 3 | Análise estatística: IC via bootstrap, paired t-test, Wilcoxon, Bonferroni | `results/aggregated.json` |
| 4 | Geração das figuras: *money figure*, decomposição de $\Omega(S)$ por sub-relação, dano colateral | `results/figures/` |
| 5–6 | Análise qualitativa de cadeias de evidência: amostragem de 20 cadeias geradas, avaliação de completude/acionabilidade | Apêndice qualitativo |
| 7 | Redação de §5 (Resultados) com tabelas e figuras geradas | §5 do `.tex` atualizada |

**Tempo total:** ~1 semana.

**Gates:**

- $n \ge 30$ runs por configuração concluídas com sucesso
- Pesos finais documentados com sensibilidade (±20% perturbação)
- Diferença (d) − (c) estatisticamente significativa em Cenário C com $p < 0{,}01$ após Bonferroni

### Sprint 5 — Comparação com KLAGE

**Goal:** rodar o arcabouço em RT-IoT2022 e CIC-IoT2023 (mesmos *datasets* de KLAGE) para comparação direta em `DDoS Slowloris`. Reportar F1 lado a lado, com mapeamento honesto session-level vs flow-level.

| Dia | Atividade | Saída |
|---|---|---|
| 1 | Aquisição de RT-IoT2022 e CIC-IoT2023 (IEEE DataPort) | Datasets locais |
| 2 | Pipeline de extração adaptado (Sprint 1 reaproveitado) | Sessões + KG |
| 3 | Execução do arcabouço completo | F1 nossa proposta |
| 4 | Análise comparativa: mapeamento metodológico, tabela final | Tabela KLAGE × nossa |

**Tempo total:** 3–4 dias.

**Gates:**

- F1 no nosso esquema reportado em ambos os *datasets*
- Mapeamento explícito entre granularidades de classificação (session vs node de rede)
- Discussão honesta: vantagens nossas, vantagens deles

---

## Checkpoint inter-fases

Antes de iniciar a Fase B:

- [ ] Todas as 6 entregas da Fase A aplicadas no `.tex`
- [ ] Paper compila limpo, sem `[?]` em citações ou figuras
- [ ] Releitura completa por outro autor (Arthur Kobielski, Marcos Luna)
- [ ] Aprovação para começar Sprint 1

Entre Sprint 1 e Sprint 2:

- [ ] Pipeline de extração reproduzível por um terceiro
- [ ] Dataset Sprint 1 documentado em README
- [ ] Aprovação para começar Sprint 2

Entre cada Sprint subsequente: revisão dos resultados parciais antes de seguir.

---

## Disciplina transversal

| Item | Onde fica |
|---|---|
| `requirements.txt` raiz do repo | `experiments/requirements.txt` |
| Versões dos *datasets* (SHA-256) | `experiments/datasets_versions.json` |
| Seeds das execuções | `experiments/seeds.txt` |
| Configurações YAML | `experiments/configs/*.yaml` |
| Logs estruturados (JSON) | `experiments/logs/run_*.json` |
| Makefile com targets | `experiments/Makefile` |
| Scripts de análise | `experiments/analysis/*.py` |
| Notebooks Jupyter de exploração | `experiments/notebooks/` |

---

## Registro de riscos

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| CIC-DDoS2019 PCAPs muito grandes para laptop | Média | Médio | Trabalhar com subconjunto Slowloris (~5–10 GB); processar em lotes |
| `pyja4` falha em PCAPs antigos | Média | Médio | Fallback para `tshark` + plugin JA4 |
| *Ground truth* de cluster difícil de derivar do CIC-DDoS2019 | Alta | Médio | Compensar com gerador sintético robusto (Sprint 2) |
| Gerador sintético "fácil demais" → resultado inflado | Alta | Alto | Calibração obrigatória contra distribuições reais (Sprint 2); validação KS |
| Reasoner OWL muito lento | Média | Médio | Usar OWL 2 RL profile; *materialization*; *backend* TDB2 |
| Grid search dos pesos não converge | Baixa | Médio | Reduzir espaço de busca; usar análise de sensibilidade ao redor de priors |
| KLAGE replicação difícil (sem comparar diretamente) | Média | Médio | Reportar números *deles* da publicação + nossos no mesmo *dataset*; não tentar reimplementar KLAGE |

---

## Resumo executivo

**Fase A** (1 semana, custo zero de dados, custo zero de tempo experimental):
- 6 entregas no `.tex` endereçando lacunas conceituais identificadas
- Saída: paper "conceitual robusto defensável", pronto para receber resultados experimentais
- Crítico: A1 (algoritmos das sub-relações), A3 (recorte Rapid Reset), A4 (adversidade)

**Fase B** (5 semanas, dados sintéticos + dois *datasets* públicos):
- Sprint 1: pipeline de extração (CIC-DDoS2019)
- Sprint 2: gerador sintético calibrado
- Sprint 3: baselines + ablação
- Sprint 4: execução completa + calibração de pesos
- Sprint 5: comparação com KLAGE (RT-IoT2022 + CIC-IoT2023)

**Custo total estimado:** 6 semanas para chegar a "paper completo com resultados", desde hoje (2026-05-30) → submissão por volta de 2026-07-11.

**Recursos necessários:**

- 1 laptop com 16+ GB RAM, ~100 GB disco livre
- Conexão estável para download dos *datasets* (~80 GB CIC-DDoS2019, ~12 GB CIC-IoT2023)
- Registro UNB para CIC-DDoS2019 (gratuito, mas burocrático)
- Conta IEEE DataPort para CIC-IoT2023 (gratuito)
- Tempo: aproximadamente 4 h/dia em sprints, 6 dias por semana
