# Sprint 5 — Comparação com KLAGE (CIC-IoT2023)

> **Objetivo:** rodar o arcabouço no mesmo *dataset* usado por KLAGE (Belcastro et al., FGCS 2026) para comparação direta em DDoS Slowloris. KLAGE reporta $F_1 = 84{,}1\%$; queremos reportar o nosso F1 lado a lado, com a métrica adicional de dano colateral em legítimos.

> **Status:** 🛠 Stub — infraestrutura a ser construída após validação do Sprint 1.
> Para já, esta pasta serve para guardar o *dataset* CIC-IoT2023 quando você baixar.

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
