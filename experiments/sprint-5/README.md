# Sprint 5 — Comparação com KLAGE (CIC-IoT2023)

> **Objetivo:** rodar o arcabouço no mesmo *dataset* usado por KLAGE (Belcastro et al., FGCS 2026) para comparação direta em DDoS Slowloris. KLAGE reporta $F_1 = 84{,}1\%$; queremos reportar o nosso F1 lado a lado, com a métrica adicional de dano colateral em legítimos.

> **Status:** ✅ Executado em CIC-IoT2023 (já adquirido e processado no Sprint 1).
> RT-IoT2022 fica pendente de download (IEEE DataPort, manual).

## ✅ Resultados — DDoS Slowloris, CIC-IoT2023

Detecção de Slowloris (one-vs-rest), `make run`:

| método | F1 | prec | rec | AUC | dano colateral (FPR benigno) |
|---|---|---|---|---|---|
| **KLAGE** (node-level, Graph-BERT) | 0.841 | — | — | — | não reportado |
| nosso **(a)** ML por-sessão | 0.179 | 0.691 | 0.103 | 0.551 | 1.06% |
| nosso **(d)** cross-session completo | **0.911** | 0.908 | 0.915 | 0.982 | 2.73% |

**ΔF1(d−a) = +0.732.** No CIC-IoT2023 o Slowloris é per-sessão indistinguível do
benigno (n_req≈1, dur≈0) e distribuído (143 /24s) — a detecção por-sessão colapsa
(F1=0.18, AUC≈acaso), enquanto o arcabouço cross-session atinge F1=0.911,
**superando o KLAGE (+0.070)**. A tese se sustenta em dados reais.

**⚠️ Caveats honestos:**
- **Granularidade:** KLAGE classifica *nós de rede*; nós classificamos *sessões*. Os
  F1 não são diretamente comutáveis — comparação de ordem de grandeza. Vantagem
  qualitativa nossa: veredicto simbólico auditável (regra SPARQL) + dano colateral
  mensurável (KLAGE não reporta).
- KLAGE avalia em RT-IoT2022 **+** CIC-IoT2023; aqui só CIC-IoT2023 (RT-IoT2022 não
  adquirido).
- (d) tem dano colateral maior que (a) (2.73% vs 1.06%): pega muito mais ataque mas
  sinaliza levemente mais benigno — ainda baixo.

Artefato: [`results/klage_comparison.json`](results/klage_comparison.json).

## Quando rodar este sprint

**Após** Sprint 1 (pipeline em CICIDS2017) validado. Sprint 5 reaproveita a maior parte da infra de Sprint 1, apenas trocando o conjunto de PCAPs de entrada.

## Aquisição do CIC-IoT2023

### Opção A — Via UNB (mesma conta do CICIDS2017)

URL: **https://www.unb.ca/cic/datasets/iotdataset-2023.html**

Mesma página, mesmo registro UNB. Procurar:

| Arquivo | Tamanho | O que tem |
|---|---|---|
| `Network traffic` → `PCAPs/` (subfolder específico) | ~12 GB total | Tráfego de 33 ataques sobre 105 dispositivos IoT |
| `Network traffic` → `CSVs/` (features extraídas) | ~3 GB | Flow-level features prontas para ML |

Para alinhar com a metodologia de KLAGE, baixe especificamente os PCAPs e CSVs do ataque **`DDoS Slowloris`** se possível, ou o subconjunto temporal correspondente.

### Opção B — Via IEEE DataPort

URL: **https://ieee-dataport.org/documents/ciciot2023-dataset**

Requer conta IEEE DataPort gratuita. Mirror do mesmo dataset.

## Onde salvar

```
$DATA_ROOT/raw/cic-iot-2023/
```

(diretório já criado pelo `setup-data-storage.sh`).

## Como reaproveitar o Sprint 1

Quando o CIC-IoT2023 estiver no HD, executar:

```bash
cd experiments/sprint-1
make DATASET=cic-iot-2023 extract-ja4
make DATASET=cic-iot-2023 extract-flows
make DATASET=cic-iot-2023 sessions
make DATASET=cic-iot-2023 clusters
make DATASET=cic-iot-2023 load-kg
```

O parâmetro `DATASET=cic-iot-2023` direciona o Makefile para os paths corretos no HD (`raw/cic-iot-2023/`, `processed/.../cic-iot-2023/`, etc.). A infra é a mesma.

## O que será produzido (Sprint 5 propriamente dito)

| Saída | Conteúdo |
|---|---|
| `results/aggregated/klage_comparison.csv` | F1, precisão, *recall* lado a lado (nosso × KLAGE) |
| `results/figures/klage_comparison.pdf` | Figura comparativa |
| Análise textual em §5 do paper | Discussão metodológica honesta sobre granularidade session-level (nossa) × node-level (KLAGE) |

## Gates de aprovação

- [ ] CIC-IoT2023 baixado e descompactado em `$DATA_ROOT/raw/cic-iot-2023/`
- [ ] Pipeline do Sprint 1 roda com `DATASET=cic-iot-2023` sem ajuste de código
- [ ] F1 do arcabouço em `DDoS Slowloris` do CIC-IoT2023 reportado
- [ ] Dano colateral em legítimos do CIC-IoT2023 reportado
- [ ] Tabela comparativa com KLAGE em §5 do paper

## Próximos passos

1. Concluir Sprint 1 (validar pipeline em CICIDS2017)
2. Baixar CIC-IoT2023 quando o Sprint 1 estiver validado
3. Re-rodar os mesmos `make` com `DATASET=cic-iot-2023`
4. Compor a tabela comparativa final
