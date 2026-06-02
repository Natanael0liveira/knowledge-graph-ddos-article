# Ponto de parada — Sprint 1

**Última atualização**: 2026-06-01 21:00

Este arquivo documenta exatamente onde paramos para que a próxima sessão retome sem reler todo o histórico.

> **➡️ PRÓXIMA SESSÃO (2026-06-02):** começar por [`HARDENING-PLAN.md`](HARDENING-PLAN.md)
> — plano gratuito para endurecer a validade dos resultados (auto-auditoria cética
> encontrou circularidade no sintético, comparação KLAGE não-controlada, baselines
> não-fiéis, pesos não-calibrados). Passo 1 = generalização multi-ataque em dados reais.

---

## ⚡ 2026-06-01: carga no Fuseki RESOLVIDA (ambos KGs no ar)

| Dataset | Triples | ApplicationSessions |
|---|---|---|
| cicids2017 | 4.553.508 | 368.777 |
| cic-iot-2023 | 9.750.257 | 787.237 |

**O que travava** (e a correção, já no Makefile):
1. **Banco TDB2 no exfat** → memory-map/fsync sem semântica POSIX. Movido para o **SSD interno** via `FUSEKI_DB` no `.env` (`docker-compose.yml` monta `${FUSEKI_DB}:/fuseki`). Dados crus/exports continuam no HD externo. O banco é derivado, reconstruível em ~1min.
2. **POST HTTP transacional por chunk numa JVM amd64 emulada** (imagem `stain/jena-fuseki` roda sob QEMU no Mac ARM) → travava ~chunk 6 (~1.2M triples). Trocado por **bulk load offline com `tdb2.tdbloader` nativo** (Apache Jena 5.1.0 em `~/apache-jena-5.1.0`, rodando na JVM ARM do host `openjdk@17`). 4.5M em ~40s.
3. **`build_graph` rdflib inteiro em RAM** estourava swap em datasets grandes (cic-iot-2023 congelou a 3% CPU). Trocado por **escritor streaming de N-Triples em lotes** (memória constante). Flag `--stream` no `load_to_fuseki.py`.

**Como recarregar (reproduzível):**
```bash
make DATASET=cicids2017 load-kg-bulk     # gera .nt via stream + tdb2.tdbloader nativo + sobe Fuseki
make DATASET=cic-iot-2023 load-kg-bulk
```
Pré-requisito: `~/apache-jena-5.1.0` (mesma versão da imagem Fuseki) e `FUSEKI_DB` no `.env` apontando p/ SSD interno.

⚠️ O alvo antigo `load-kg` (HTTP POST chunked) ficou **deprecado** — só serve p/ datasets pequenos.

**Próximo:** rodar `validate.ipynb` (gates G1–G4) e resolver o gap de labels do CICIDS2017 (pré-req do G3) — ver seções abaixo.

---

## ⚡ 2026-06-01 (cont.): gates G3 + G4 implementados (cic-iot-2023)

Novo script [`scripts/compute_coordination.py`](sprint-1/scripts/compute_coordination.py) + alvo `make DATASET=cic-iot-2023 coordination`.

**Decisões:**
- **Escopo Ω(S) = "3 limpas"**: relatedByTLSFingerprint (w=1.0, JA4), relatedByEndpointConvergence (0.6), relatedByNetworkProximity /24 (0.3). As outras 3 (ReusedIdentity, TemporalPattern, PayloadSignature) **não têm dado** a nível de session neste dataset.
- **Anti-circularidade (crítico)**: `cluster_id` do `derive_clusters` é formado por `[label, dst_ip, dst_port]` → embute a resposta. NÃO usar como S. Em vez disso, **clusters de detecção label-agnósticos** por `(endpoint, janela 300s)`. Labels só para avaliar.
- **Ω(S) em O(N)**: pares que compartilham sinal = Σ C(n,2) por valor; nunca materializa O(N²).

Filtro HTTP no G4 (a regra é `coordinatedHTTPFlood`): portas {80,443,8080,...} —
senão serviços benignos de alto volume (DNS :53) dominam Ω por massa de endpoint.

**Resultados (AMBOS datasets, gates G3+G4 PASS, validados via SPARQL real):**

| | G3 coord-só / melhor | G4 clusters | attack-dom |
|---|---|---|---|
| cic-iot-2023 | 0.966 / 0.999 | 16 | **11/16 (69%)** |
| cicids2017 | 1.0 / 1.0 | 65 | 4/65 (6%) |

- **Achado de precisão**: Ω é forte quando há sinal de alto peso (cic-iot-2023: bots com JA4 compartilhado → 69% precisão). No cicids2017 o JA4 é quase ausente → τ frouxo (pct99 benigno) deixa passar HTTP benigno grande (4/65), MAS os 4 ataques (Hulk/GoldenEye/Slowhttptest/Slowloris) têm o **maior Ω** (topo do ranking SPARQL). Precision@top-k seria a métrica certa; calibrar τ é Sprint 4.
- **G3 caveat**: AUC alto é parte trivial (CIC separável por fluxo: comportamental-só 0.994/0.9998). No cicids2017 há circularidade parcial (label derivado do IP atacante ↔ share_net). Evidência limpa = ablação coordenação-só.

**Labeling CICIDS2017 (resolvido):** `scripts/label_cicids2017.py` — par atacante `172.16.0.1→192.168.10.50:80` + janelas verificadas nos bursts reais (5min): Slowloris 4035, Slowhttptest 4217, Hulk 30391, GoldenEye 7472, BENIGN 322658. Backup do parquet em `.unlabeled.bak`.

**Fechados 2026-06-01 (cont.):**
- ✅ **Gate JA4 reformulado** — era "≥50% de TODAS as sessões" (irreal: HTTP/DNS puro não tem JA4). Agora "G1: ≥5 JA4 distintos" + "cobertura ≥50% do subconjunto TLS (:443|sni|ja3)". Resultado: cicids2017 98.6%, cic-iot-2023 68.6% → PASS. Extração estava ótima; só a métrica estava errada.
- ✅ **KG cicids2017 recarregado** com labels (groundTruthLabel: BENIGN 322658, Hulk 30391, …). DetectionClusters re-anexados. 4.63M triples.
- ✅ **validate.ipynb integrado** — gates G1–G4 num único relatório (importa `compute_coordination`); **todos os gates PASS nos dois datasets**, executado via nbconvert.

## ⚡ 2026-06-01 (cont.): Sprints 3, 4, 5 — Fase B completa

- **Sprint 3** (`experiments/sprint-3/`, `make scenarios && make ablation`): ablação a/b/c/d + 3 baselines (Fernandes/Bharathi/Kemp). Em campanha **furtiva** (ataque per-sessão indistinguível do benigno), (a) ML e baselines ~acaso (0.5), (d) cross-session ~1.0. Exigiu o modo `stealth: true` no gerador do S2.
- **Sprint 4** (`experiments/sprint-4/`, `make run|weights|figures`): n=30 seeds, IC bootstrap + Wilcoxon + Bonferroni + Cohen's d. **GATE: (d)−(c) no Cenário C, p_bonf=2.2e-05, d=2.91**. Money figure em `results/`. Caveat: grid search de pesos satura (todo w_i dá AUC=1.0 no sintético).
- **Sprint 5** (`experiments/sprint-5/`, `make run`): comparação com KLAGE em DDoS Slowloris no **CIC-IoT2023 real**. Nosso (d) **F1=0.911 > KLAGE 0.841**; (a) por-sessão colapsa (F1=0.18). Caveats: granularidade sessão-vs-nó; RT-IoT2022 não adquirido.

**Pendências (fora da Fase B):** (a) RT-IoT2022 (download manual IEEE DataPort); (b) calibração real de w_i (precisa de dados mais difíceis — sintético satura); (c) formalizar as 6 sub-propriedades relatedBy_* no `.owl`; (d) pilares 2 e 4 do paper (cadeia de evidência JSON-LD/STIX + mitigação cirúrgica) ainda não codificados; (e) redação da §5.

---

## ✅ O que está pronto

### Pipeline executado para AMBOS datasets

| Etapa | cic-iot-2023 | cicids2017 (Wednesday) |
|---|---|---|
| **extract-ja4** | ✅ 6 CSVs, 79.810 JA4 records | ✅ 1 CSV, 132.115 records (66.306 JA4 válidos) |
| **extract-flows** | ✅ 6 CSVs, 421 MB | ✅ 15 CSVs chunkados, 240 MB |
| **build_sessions** | ✅ **787.237 sessions** | ✅ **368.777 sessions** |

### Artefatos no HD externo (`$DATA_ROOT`)

```
$DATA_ROOT = /Volumes/Untitled/kg-ddos-data

processed/
├── ja4/
│   ├── cic-iot-2023/        (6 CSVs)
│   └── cicids2017/          (Wednesday-workingHours.csv)
├── flows/
│   ├── cic-iot-2023/        (6 CSVs, 421M)
│   └── cicids2017/          (15 chunks_Wed_*.csv, 240M)
└── sessions/
    ├── cic-iot-2023.parquet (39M, 787.237 rows)
    └── cicids2017.parquet   (19M, 368.777 rows)
```

### Decisões técnicas importantes desta sessão

1. **CICFlowMeter Java JAR → cicflowmeter Python (pip)**: o JAR oficial está fora do ar (GitHub 404). Refatoramos para usar `pip install cicflowmeter` v0.2.0.

2. **scapy 2.7.0 → 2.5.0**: cicflowmeter 0.2.0 usa API antiga de sessions do scapy (`toPacketList`). scapy ≥2.6 mudou para `process/recv` → CSV vazio. Downgrade automático no `make install-cicflowmeter`.

3. **3 patches em cicflowmeter**: `min()` em sequência vazia matava a AsyncSniffer thread. Aplicados via [`scripts/patch_cicflowmeter.py`](sprint-1/scripts/patch_cicflowmeter.py) (idempotente, chamado pelo Makefile).

4. **Wednesday-workingHours.pcap (12 GB) splittado em 15 chunks**: cicflowmeter tem `garbage_collect` O(N) por chamada → degradação quadrática em PCAPs longos. Solução: `editcap -i 3600` + sub-split de chunks >1.5GB. Original preservado em `Wednesday-workingHours.pcap.original` no `$DATA_ROOT/raw/cicids2017/`.

5. **tshark 4.6.6 não tem `tls.handshake.ja4s`**: usamos JA3 como fallback. CSV columns: `timestamp,src_ip,src_port,dst_ip,dst_port,ja4,ja3,sni`.

6. **AppleDouble (`._*`) no ExFAT**: filtros adicionados em find (Makefile), `load_ja4`/`load_flows` (build_sessions.py). Se aparecerem mais, rodar `find $DATA_ROOT -name "._*" -delete`.

---

## ▶️ Para retomar amanhã

### Pré-requisitos antes de qualquer comando

1. **HD externo conectado**: `ls /Volumes/Untitled/kg-ddos-data` deve mostrar `raw/ processed/ logs/`
2. **Docker Desktop aberto** (manual): necessário para `load-kg`. Se `docker info` falhar, abrir o app.
3. **Diretório de trabalho**: `cd /Users/natanaeloliveira/netautomation/knowledge-graph-ddos-article/experiments/sprint-1`

### Próximas etapas (em ordem)

```bash
# 1. Validar que tudo está como deixamos
make check
ls $DATA_ROOT/processed/sessions/  # deve ter cic-iot-2023.parquet + cicids2017.parquet

# 2. Derivar clusters (ground truth coordenação) — autônomo, ~5 min
make DATASET=cic-iot-2023 clusters
make DATASET=cicids2017 clusters

# 3. Subir Fuseki (Docker Desktop precisa estar rodando)
make fuseki-up
# verificar em http://localhost:3030

# 4. Carregar sessions + clusters como RDF no Fuseki
make DATASET=cic-iot-2023 load-kg
make DATASET=cicids2017 load-kg

# 5. Rodar notebook de validação (gates do Sprint 1)
make validate    # abre Jupyter ou
jupyter nbconvert --to notebook --execute notebooks/validate.ipynb
```

### Gates do Sprint 1 que precisamos verificar

A pipeline acima é canônica; o que vai exigir nossa atenção é a interpretação dos **gates** no `notebooks/validate.ipynb`. Os gates definidos no plano são:

- **G1**: ≥ 5 JA4 fingerprints distintos por dataset
- **G2**: ≥ 1.000 sessions BENIGN e ≥ 100 sessions de ataque
- **G3**: ROC AUC ≥ 0.85 para um classifier simples baseado nas relatedBy_*
- **G4**: SPARQL query `coordinatedHTTPFlood` retorna ≥ 1 cluster com Ω(S) > threshold

Se algum gate falhar, decidimos juntos:
- Ajustar threshold da Ω(S)
- Investigar qualidade dos dados (talvez Slow HTTP em cicids2017 não tenha JA4 suficiente)
- Refinar pesos w_i das sub-relações

### Lacunas conhecidas a resolver na próxima sessão

1. **Labels do CICIDS2017**: `build_sessions.py` marca tudo como `"UNLABELED"` para Wednesday. Precisamos cruzar com a timeline oficial CIC (Slowloris 09:20-10:00, Slowhttptest 10:14-10:35, Hulk 10:43-11:00, GoldenEye 11:10-11:23, Heartbleed 14:19-15:01) → adicionar coluna `attack_type` via filtro temporal sobre `start_ts`.

2. **JA4 vs flow alignment no CICIDS2017**: o JA4 foi extraído do PCAP inteiro (132K records). Os flows foram extraídos dos 15 chunks. Possível que algumas sessions percam JA4 fingerprint na fronteira de chunks. Verificar % de sessions sem JA4.

3. **Commit dos fixes**: muitos arquivos modificados nesta sessão (Makefile, extract_flows.py, build_sessions.py, patch_cicflowmeter.py novo). Fazer um commit consolidado antes de mexer em mais coisas.

---

## 🗂 Arquivos modificados nesta sessão (não commitados ainda)

```
experiments/sprint-1/Makefile                       (install-cicflowmeter + patches)
experiments/sprint-1/scripts/extract_flows.py       (Python cicflowmeter via venv)
experiments/sprint-1/scripts/build_sessions.py      (colunas snake_case + label by filename + filtro ._*)
experiments/sprint-1/scripts/patch_cicflowmeter.py  (NOVO — patches idempotentes)
```

---

## 🧠 Comandos rápidos de diagnóstico

```bash
# Memória dos sessions parquets
python3 -c "import pandas as pd; df = pd.read_parquet('$DATA_ROOT/processed/sessions/cic-iot-2023.parquet'); print(df.head()); print('shape:', df.shape); print('labels:', df['label_first'].value_counts())"

# Sanity check JA4 coverage
python3 -c "import pandas as pd; df = pd.read_parquet('$DATA_ROOT/processed/sessions/cic-iot-2023.parquet'); print('com JA4:', df['ja4'].notna().sum(), '/', len(df))"

# Disk usage
du -sh /Volumes/Untitled/kg-ddos-data/{raw,processed,logs}/
```

---

## 📊 Métricas da sessão de hoje

- **Início**: 2026-05-31 ~14:00 (com pipeline inicial JA4)
- **Fim**: 2026-05-31 23:50
- **Tempo total**: ~10h (boa parte em background)
- **Datasets processados**: 2 (cic-iot-2023 + cicids2017 Wednesday)
- **PCAPs analisados**: 22 (6 IoT + 1 Wednesday original em 15 chunks)
- **JA4 extraídos**: 145.925 (79.810 IoT + 132.115 Wednesday, ~66K com JA4 válido)
- **Flows extraídos**: 1.381.395 (917.925 IoT + 463.470 Wednesday)
- **Sessions construídas**: 1.156.014 (787.237 IoT + 368.777 Wednesday)

Próxima estimativa: derive_clusters + load-kg + validate = ~30 min de execução total.
