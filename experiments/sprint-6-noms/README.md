# Sprint 6 — experimentos adicionados para a submissão NOMS

Três experimentos que fecham lacunas que um revisor do NOMS encontra sozinho na
versão atual do artigo. Nenhum deles substitui resultado existente; todos são
aditivos e os sprints 1–5 ficam intactos.

| Script | Lacuna que fecha | Precisa do HD? |
|---|---|---|
| `scripts/bench_latency.py` | O artigo afirma custo O(\|S_W\|·c) e escalabilidade quase-linear do OWL 2 RL, mas **não media nada**. | **Não** |
| `scripts/run_ml_families.py` | A tese "nenhum detector por sessão funciona" era sustentada por **um único** Random Forest. | Sim ✅ (cenário superado — ver §2) |
| `scripts/window_sweep.py` | O Apêndice C declarava que a sensibilidade a *W* não foi caracterizada. | Sim ✅ |

## Cache de cenários — atenção

O work dir canônico é **`$DATA_ROOT/synth/sprint4_realistic_work`**, o único que
reproduz a tabela publicada. Os outros dois enganam:

- `synth/sprint4` — anterior às features de fluxo; `run_sprint4.py` falha nele com
  `KeyError: ['fwd_bytes_sum', ...] not in index`.
- `synth/sprint4_strong_work` — ainda tem o **artefato de porta**: a config (b)
  chega a 0,888 em vez de colapsar para o acaso.

Reprodução verificada com 30 seeds contra `sprint4_realistic_work`: (a) 0,519 /
0,502 · (b) 0,527 / 0,503 · (c) 0,523 / 0,664 · (d) 0,968 / 0,976, com
p_bonf = 7,45e-09 e Cohen's d de +12,2 e +19,6 em K=1000 — **idêntico ao artigo**.

```bash
make latency      # roda em qualquer lugar
make all-hd       # ml + window, exige o HD montado
```

## 1. Latência (`bench_latency.py`)

Mede as **duas camadas separadamente**, porque rodam em taxas diferentes e têm
complexidade diferente — e essa distinção é o resultado:

- **Camada 1 — admissão (por requisição, caminho quente).** Admitir uma sessão
  nova numa janela com |S_W| sessões, instanciando as arestas `relatedBy_*` via
  os índices invertidos descritos no §III-C (bucket de JA4, de endpoint, de /24).
  Custo por par candidato é O(1); o que cresce é o número de candidatos.
- **Camada 2 — avaliação simbólica (por janela, caminho auditável).**
  Materializar as arestas em RDF via SPARQL CONSTRUCT (equivalente às regras
  Horn em `pillar2-symbolic-reasoning/rules/relatedBy.swrl`) e rodar a agregação
  ponderada Ω(S).

Não precisa de dataset: latência depende de |S_W| e da estrutura de coordenação
da janela, não de o tráfego ser real. O mix de sessões é parametrizado
(`--coord-frac`, `--ja4-pool`, `--endpoints`) e gravado junto dos tempos, para
os números serem interpretáveis.

O sweep tem um `--pair-cap`: acima dele a camada simbólica é pulada em vez de
estourar a memória. O estouro em si é achado, não acidente — Ω(S) conta *pares*,
então o termo quadrático é inerente à definição da regra e é exatamente o que
torna a janela *W* uma necessidade, não uma conveniência.

**Ressalva de backend:** a camada simbólica é medida sobre `rdflib`
(implementação de referência, em memória). O backend de produção declarado no
artigo é Apache Jena Fuseki com TDB2, usado no sprint-1. Os números da camada 2
são portanto um limite superior da implementação de referência, não do backend
de produção — e devem ser reportados como tal.

## 2. Famílias de ML (`run_ml_families.py`)

Roda a mesma ablação sobre o mesmo conjunto forte de features e o **mesmo split**
em quatro famílias: `rf` (o que o sprint-4 usou), `hgb`
(HistGradientBoosting), `mlp` e `logreg`. Se todas ficarem no acaso na config
(a), a afirmação deixa de ser "o RF falhou" e passa a ser "nenhuma classe de
hipótese separa as sessões".

`xgboost` está instalado no venv mas a biblioteca nativa não carrega nesta
máquina (falta `libomp`; `brew install libomp` resolveria). O
`HistGradientBoostingClassifier` do sklearn cobre a mesma família de algoritmo
sem dependência nova.

Reaproveita o cache de cenários do sprint-4: se os parquets `(K, seed)` já
existem em `--work`, nada é regerado.

> ⚠️ **`ml_families.json` está sobre o cenário SUPERADO e não é a fonte da
> Tabela I do artigo.** Este script foi rodado antes da correção de realismo,
> sobre o cache do sprint-4 (pool benigno plano, `alpha=0`; botnet monolítica).
> A fonte da Tabela I é `run_canonical_realistic.py` →
> `canonical_realistic.json` (`alpha=1.5`, 25 stacks TLS).
>
> A diferença não é cosmética. Na configuração (d) em `K=1000`:
>
> | família | superado (`ml_families`) | canônico (`canonical_realistic`) |
> |---|---|---|
> | `rf`     | 0,976 | 0,982 |
> | `hgb`    | 0,979 | 0,990 |
> | `mlp`    | 0,956 | **0,803** |
> | `logreg` | 0,961 | **0,799** |
>
> O colapso de `mlp` e `logreg` no cenário canônico **é um achado, não um bug**:
> fragmentar a botnet em 25 stacks torna a evidência entre sessões
> não-monotônica no rótulo, e modelos de resposta monotônica não conseguem
> recortar a faixa intermediária. É o que o artigo discute em §V-A, e é o
> argumento a favor do caminho simbólico. No cenário superado, com botnet
> monolítica, esse efeito simplesmente não existe.
>
> Rode `run_ml_families.py` para reproduzir o passo histórico; para reproduzir o
> artigo, rode `run_canonical_realistic.py`.

## 3. Sweep da janela (`window_sweep.py`)

*W* só entra via `assign_detection_clusters`, então varrê-lo é recomputar as
features cross-session sobre os **mesmos** cenários em cache. Reporta os dois
lados: efeito na detecção (ROC AUC por config) e custo (número de clusters e
tamanho médio, que alimentam o termo quadrático medido em `bench_latency.py`).

*W* pequeno demais deixa a evidência cross-session raquítica (poucos pares no
cluster, Ω abaixo de τ); *W* grande demais funde tráfego não relacionado num
cluster só e dilui o discriminador. O sweep mede onde fica esse compromisso.

## Resultados

### Latência (executado — 3 repetições, 1 core)

| \|S_W\| | admissão p50 | arestas/adm | ns/par | sessões/s | simbólico | arestas RDF | µs/aresta |
|---|---|---|---|---|---|---|---|
| 100 | 2,1 µs | 148 | 14,3 | 470.578 | 0,56 s | 2.703 | 208 |
| 250 | 3,3 µs | 239 | 13,7 | 305.762 | 3,10 s | 17.221 | 180 |
| 500 | 6,1 µs | 396 | 15,3 | 164.950 | 12,09 s | 65.115 | 186 |
| 1.000 | 11,9 µs | 741 | 16,0 | 84.207 | 49,69 s | 265.328 | 187 |
| 2.500 | 32,5 µs | 1.660 | 19,6 | 30.730 | — | — | — |
| 5.000 | 61,7 µs | 3.373 | 18,3 | 16.205 | — | — | — |
| 10.000 | 122,1 µs | 6.495 | 18,8 | 8.188 | — | — | — |

**As duas camadas são lineares na sua própria unidade de trabalho.** A admissão
custa 14–19 ns por par candidato, constante em toda a faixa — o O(\|S_W\|·c) do
artigo se confirma com *c* genuinamente O(1). O simbólico custa ~187 µs por
aresta RDF materializada, também constante. O termo quadrático não é da
implementação nem do backend: é o Ω(S) ser definido sobre **pares**, então é a
contagem de arestas que cresce com o quadrado de \|S_W\|. É isso que torna a
janela *W* uma necessidade estrutural, não uma conveniência.

Consequência de projeto que a medição sustenta: detectar pelo caminho indexado
(microssegundos) e materializar RDF só para os clusters que disparam — que é
exatamente o subconjunto da cadeia de evidência, não a janela inteira.

Está no artigo em §V-F + Fig. 6.

### Famílias de ML (executado — 30 seeds, `sprint4_realistic_work`)

ROC AUC por sessão, config (a) por-sessão / config (d) cross-session:

| família | (a) K=50 | (d) K=50 | (a) K=1000 | (d) K=1000 |
|---|---|---|---|---|
| Random Forest | 0,519 | 0,968 | 0,502 | 0,976 |
| HistGradientBoosting | 0,515 | 0,963 | 0,502 | 0,979 |
| MLP | 0,490 | 0,867 | 0,502 | 0,956 |
| Regressão logística | 0,490 | 0,948 | 0,506 | 0,961 |

**A config (a) fica no acaso para as quatro famílias** (0,490–0,519 em K=50;
0,502–0,506 em K=1000). O colapso é propriedade da *representação*, não do
aprendiz — que é exatamente o que a tese central precisava. A (d) também se
sustenta nas quatro, mas **não igualmente**: o MLP é o mais fraco em K=50 (0,867
contra 0,968 do RF), nuance que ficou registrada no artigo. Todos os contrastes
(d)−(a) seguem significativos (p_bonf = 1,5e-08; Cohen's d de +3,7 a +19,6).

### Sweep da janela W (executado — 10 seeds, K=1000)

| W (s) | clusters | \|S\| médio | (a) | (b) | (c) | (d) |
|---|---|---|---|---|---|---|
| 60 | 16 | 132 | 0,505 | 0,508 | 0,664 | 0,976 |
| 120 | 11 | 207 | 0,505 | 0,508 | 0,663 | 0,977 |
| 300 | 6 | 364 | 0,505 | 0,508 | 0,664 | 0,977 |
| 600 | 4 | 557 | 0,505 | 0,508 | 0,664 | 0,978 |
| 1800 | 3 | 867 | 0,505 | 0,508 | 0,664 | 0,978 |

**A detecção é insensível a W numa faixa de 30×** — (d) vai de 0,976 a 0,978,
(a) e (c) não se mexem — enquanto a ocupação média do cluster cresce 6,6× e com
ela o termo quadrático medido no benchmark de latência. A razão: a feature
discriminativa é uma *fração* (share_ja4, a parcela do cluster com um mesmo
JA4), invariante à escala do cluster; o tamanho do cluster sozinho carrega pouco
— é por isso que (c) fica em 0,664 o tempo todo.

Regra operacional que sai daí: **manter W tão pequeno quanto o tráfego permitir**
— janela maior não compra detecção e custa aproximadamente o quadrado.

Dois limites do resultado: os cenários têm um único endpoint alvo (span de
6.155–39.326 s), então W é o único botão de clusterização e um cenário
multi-endpoint com campanhas interleaved pode se comportar diferente; e W ainda
precisa ser grande o bastante para formar cluster (em W=60 já são ~132 sessões).

### Cenário realista de produção + correção da heurística de escopo

Três defeitos de realismo no gerador, todos favoráveis a nós, e todos corrigidos
(retrocompatível — defaults preservam o comportamento antigo):

1. **JA4 benigno era UNIFORME** sobre um pool sintético (792 distintos em 1.000
   sessões, modal 0,4%). A distribuição real calibrada sobre ~322 mil sessões
   benignas é o oposto: 39 distintos, **top-1 = 52,7%, top-10 = 98,4%**. O próprio
   comentário do config admitia o motivo do pool plano. Corrigido: `benign_ja4_zipf_alpha`.
2. **Botnet monolítica** — um JA4 para 88% dos atacantes. Corrigido: `botnet_ja4_stacks`.
3. **Namespace do atacante disjunto do benigno** — colisão impossível por construção.
   Corrigido: `botnet_ja4_adversarial`, em que a botnet adota os fingerprints benignos
   mais comuns (o que o `curl-impersonate` faz, com presets para Chrome 116/119, Safari 17).

Cuidado: `--param x=false` chega como a **string** `"false"`, e `bool("false")` é `True`
em Python. Corrigido para as duas chaves booleanas.

**O achado.** `derive_scope` escolhe o JA4 **modal** do subconjunto coordenado. Contra
botnet heterogênea, cada stack fica menor que a cabeça benigna, o modal passa a ser um
fingerprint **legítimo**, e o escopo derivado vira um filtro que bloqueia **0% dos
atacantes e 39–61% dos usuários**. Não é degradação suave — é o mecanismo escolhendo o
alvo errado. O "0% de colateral" do artigo valia só para botnet monolítica.

**A correção.** `derive_scope_enriched` ordena candidatos por **enriquecimento** sobre um
perfil histórico benigno (janela `K=0`, sem rótulos), não por frequência, e devolve um
**conjunto** de fingerprints. O fundo precisa vir de fora do episódio: usar a própria
janela dá enriquecimento ~1 para tudo, porque a campanha atravessa a janela inteira.

Resultados (n=15 seeds, `min_support=0.002`, `min_enrichment=3.0`):

| α | M | adv | (a) | (c) | (d) | modal cov/coll | enriquec. cov/coll | #ja4 |
|---|---|---|---|---|---|---|---|---|
| 0 | 1 | – | 0,495 | 0,656 | 0,976 | 84,0/0,0 | 84,0/0,00 | 1 |
| 1,5 | 1 | – | 0,495 | 0,656 | 0,997 | 84,0/0,0 | 84,0/0,00 | 1 |
| 1,5 | 5 | – | 0,496 | 0,653 | 0,996 | **0,0/39,0** | **90,0/0,00** | 5 |
| 1,5 | 25 | – | 0,503 | 0,656 | 0,979 | **0,0/39,0** | **90,3/0,00** | 25 |
| 1,5 | 100 | – | 0,503 | 0,656 | 0,961 | **0,0/39,0** | **85,0/0,00** | 87,6 |
| 2,0 | 25 | – | 0,503 | 0,656 | 0,993 | **0,0/61,1** | **90,3/0,05** | 25,1 |
| 1,5 | 5 | sim | 0,496 | 0,653 | 0,809 | 18,4/39,0 | 17,6/3,36 | 1 |
| 1,5 | 25 | sim | 0,503 | 0,656 | 0,862 | 3,6/39,0 | 30,4/3,78 | 8,3 |
| 2,0 | 25 | sim | 0,503 | 0,656 | 0,917 | 3,6/61,1 | 50,9/3,27 | 14 |

- **Detecção sobrevive ao realismo**: (d) fica em 0,96–0,997 em todo o espaço não
  adversarial, contra ~0,50 de (a)/(b) e ~0,65 de (c). Concentração benigna realista não
  atrapalha (α=1,5 monolítico dá 0,997, melhor que o cenário plano).
- **Enriquecimento é invariante à fragmentação**: 84–90% de cobertura a 0,00–0,05% de
  colateral para M ∈ {1, 5, 25, 100}.
- **O piso de suporte é tunável, não limite**: com 0,01 uma botnet de 100 stacks degenera
  para o global (93,5%/93,3%); com 0,002 volta a 85,0%/0,00%. `min_support` precisa ficar
  abaixo de 1/M, e baixá-lo não custa colateral porque quem protege é o enriquecimento.
- **Adversarial degrada com segurança**: 17,6–50,9% de cobertura a 3,3–3,8% de colateral.
  Recusa bloquear fingerprints populares em vez de emitir filtro nocivo. Limiar estrito faz
  cair para o global — perde-se a vantagem cirúrgica, não se produz dano.

### A regra simbólica COMO detector (executado — 15 seeds, K=1000)

Todo número de detecção do artigo vinha de um classificador sobre features, o que
mede a **representação** e não diz nada sobre a camada simbólica. Aqui a regra é
avaliada ponta a ponta: as sessões que casam com o escopo derivado **são** o
conjunto marcado — sem treino, sem limiar. E como AUC é métrica de ordenação e a
regra emite decisão dura, o classificador é forçado ao **mesmo ponto de operação**.

| cenário | regra: recall / FPR / F1 | RF AUC | **RF recall @ FPR=0** |
|---|---|---|---|
| monolítico (M=1) | 84,0% / 0,00% / 0,885 | 0,997 | 91,7% |
| M=5 | 90,0% / 0,00% / 0,948 | 0,996 | 88,6% |
| M=25 | 90,3% / 0,00% / **0,949** | 0,979 | **36,4%** |
| M=100 | 85,0% / 0,00% / 0,919 | 0,961 | **17,6%** |
| M=25, adversarial | 30,4% / 3,78% / 0,452 | 0,862 | **7,8%** |

**Não é vitória uniforme, e a forma é o ponto.** Contra botnet monolítica ou pouco
fragmentada o RF empata ou ganha (91,7% e 88,6% contra 84,0% e 90,0%) — não há
vantagem simbólica no regime fácil. A partir de 25 stacks a ordem inverte de forma
acentuada: 90,3% contra 36,4%, e 85,0% contra 17,6% em M=100. Sob adoção
adversarial de fingerprint a regra recupera quatro vezes mais da campanha.

O que a coluna de AUC esconde é justamente isso: o classificador ainda marca 0,979
e 0,961 nas configurações em que recupera um terço e um sexto do ataque. A
ordenação é boa, mas a distribuição de escores se sobrepõe ao benigno na cauda,
então **nenhum limiar** entrega ação automática sem colateral. A regra não produz
escore para limiarizar — produz um conjunto definido por teste de enriquecimento
contra fundo explícito, e é por isso que o FPR é 0,00% por construção e não por
ajuste. É a evidência mais forte do projeto de que o grafo se paga.

Está no artigo em §V-B + Tabela II.

### Distribuição de JA4 medida em produção ✅

O parâmetro que mais influenciava os resultados — a concentração da popularidade de
JA4 benigno — **deixou de ser chute e passou a ser medição**. Ver
[`results/ja4_production_measurement.md`](results/ja4_production_measurement.md):
6.329.649 requisições num edge de CDN em produção, 495 fingerprints distintos,
top-1 = 38,37%, top-10 = 93,82%.

O canônico do gerador (alpha=1,5, cabeça de 38,95%) acerta a cabeça medida quase na
vírgula, e o sweep alpha ∈ {1,5 … 2,0} contém a curva real. O testbed de laboratório
(CICIDS2017: 52,7% de cabeça) é *mais* concentrado que a produção — o lab exagera.

Isso substituiu, em §IV-A do artigo, a justificativa "não há medição pública" por uma
medição real, com as ressalvas (ponderação por requisição, um PoP, uma janela)
declaradas.

### Duas tentativas que não deram certo (registradas para ninguém repetir)

**Calibrar o α numa medição pública — não é possível, por razão conceitual.** O
JA4DB (ja4db.com, 227 mil registros) e o `ja4plus-mapping.csv` do FoxIO são
**catálogos de fingerprints mapeados para software**, não amostras de tráfego. O
CSV do FoxIO confirma: as colunas são `Application, Library, Device, OS, ja4,
ja4s, ja4h, ja4x, ja4t, ja4tscan, Notes` — **nenhuma coluna de frequência**. Mesmo
com acesso total, esses bancos dizem *quais* fingerprints existem, nunca *que
fração das sessões* de um serviço carrega cada um — que é exatamente o que o α
parametriza. O site também serve só o shell da SPA em todas as rotas testadas
(`/api/read`, `/api/download`, `/download`, `/ja4db.csv`). Isto virou justificativa
declarada no artigo (§IV-A) para varrer o α em vez de fixá-lo.

**Reproduzir o KLAGE sob nosso protocolo — não é tarefa delimitável.** O
repositório (`SCAlabUnical/KLAGE`, 1.230 linhas em 5 arquivos) não traz **nenhum
dado, nenhum peso de modelo e nenhuma especificação de ambiente**, e todos os
caminhos de entrada são marcadores (`/path/to/your/node_features.pkl`,
`/path/to/your/adjacency_matrix.pkl`, …). O pipeline **começa** em
`path/to/graph.json`, um grafo já construído com triplas `at`/`sp`/`dp`, e a
conversão do CIC-IoT2023 bruto para esse esquema não é publicada. Some-se a
granularidade: eles classificam **nós** em **multiclasse** por `Attack_type`, nós
classificamos **sessões** em binário. Uma reprodução exigiria engenharia reversa do
pré-processamento deles, pré-treino e fine-tuning do Graph-BERT, e um mapeamento
contestável entre granularidades — e repousaria na *nossa* reconstrução, tão
disputável quanto a ressalva atual. O artigo passou a declarar essa razão técnica
em vez de dizer apenas "comparação não controlada".

### Arquivos

Gravados em `results/`:

- `latency_raw.csv`, `latency_summary.json` ✅
- `ml_families_runs.csv`, `ml_families.json` ⚠️ **cenário superado — não é a fonte da Tabela I** (ver §2)
- `canonical_realistic_runs.csv`, `canonical_realistic.json` ✅ **fonte da Tabela I do artigo**
- `window_sweep_runs.csv`, `window_sweep.json` ✅
- `collateral_purity_runs.csv`, `collateral_purity.json` ✅
- `realistic_final_runs.csv`, `realistic_consolidated.csv` ✅
- `symbolic_detector_runs.csv`, `symbolic_detector.json` ✅
