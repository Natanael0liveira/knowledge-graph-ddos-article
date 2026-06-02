# Ponto de parada — Sprint 1

**Última atualização**: 2026-06-01 21:00

Este arquivo documenta exatamente onde paramos para que a próxima sessão retome sem reler todo o histórico.

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

**Resultados (cic-iot-2023):**
- **G3 (ROC AUC ≥ 0.85): PASS** — RF combinado 0.999; **ablação coordenação-só = 0.966** (features relatedBy_* sozinhas, evidência limpa); comportamental-só 0.994 (CIC é trivialmente separável por fluxo — caveat).
- **G4 (coordinatedHTTPFlood ≥ 1 cluster): PASS** — query SPARQL real contra Fuseki retorna **33 clusters** (τ=85.5 = pct99 do benigno, |S|≥5, rate≥1). Top: `192.168.137.29:443` Ω=2.06e8 |S|=21415 (Slowloris). 13/33 attack-dominant. Triples `kg:DetectionCluster`/`kg:coordinationScore` carregados via tdbloader-append.

**Pendências:** (a) calibrar τ_cluster (paper adia p/ Sprint 4); (b) CICIDS2017 ainda UNLABELED → rodar gates lá depende do temporal join; (c) formalizar as 6 sub-propriedades no `.owl`.

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
