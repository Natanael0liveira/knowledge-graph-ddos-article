# Sprint 1 — Pipeline de Extração (PCAP → KG)

> **Objetivo:** transformar PCAPs do CIC-DDoS2019 em um grafo de conhecimento consultável via SPARQL, com sessões reconstruídas, JA4 extraído e *ground truth* de *cluster* derivada.

> **Tempo estimado de envolvimento ativo:** ~6 h, distribuídas em ~14 dias calendário.
> A maior parte do *wall clock* (downloads, extrações pesadas) roda em *background*.

## Fluxo geral

```
[CIC-DDoS2019 PCAPs] ──┐
                       ├──► extract_ja4.py  ──► ja4.csv
                       └──► extract_flows.py ──► flows.csv
                                                       │
                                                       ▼
                                            build_sessions.py ──► sessions.parquet
                                                       │
                                                       ▼
                                            derive_clusters.py ──► clusters.csv
                                                       │
                                                       ▼
                                            load_to_fuseki.py ──► KG em TDB2
                                                       │
                                                       ▼
                                                 validate.ipynb
```

## Pré-requisitos

Itens validados pelo `make check`:

- Python 3.11+ com venv
- Docker rodando (para Fuseki)
- tshark 4.0+ (com JA4)
- Java 17+ (para CICFlowMeter)
- `experiments/.env` configurado pelo `setup-data-storage.sh`

## Passo a passo (com tempo seu vs *wall clock*)

| Passo | Comando | Seu tempo | Wall clock | Observação |
|---|---|---|---|---|
| **1. Validar setup** | `make check` | 5 min | imediato | Detecta dependências faltantes |
| **2. Subir Fuseki** | `make fuseki-up` | 2 min | 1 min | Container Apache Jena rodando em http://localhost:3030 |
| **3. Teste com PCAP pequeno** | `make test` | 30 min | 5 min | Baixa amostra pública (~100 MB), roda pipeline completa, valida output |
| **4. Aquisição do CIC-DDoS2019** | `make download` | 10 min | 8–24 h | Você confirma o registro UNB e dispara; volta no dia seguinte |
| **5. Extração JA4** | `make extract-ja4` | 5 min | 2–6 h | Background. Logs em `$DATA_ROOT/logs/extract_ja4_*.log` |
| **6. Extração de flows** | `make extract-flows` | 5 min | 2–4 h | Background |
| **7. Reconstrução de sessões** | `make sessions` | 10 min | 30 min | Junta flows + JA4 |
| **8. Ground truth de cluster** | `make clusters` | 30 min | 10 min + revisão | Revisa amostra de 10 *clusters* manualmente |
| **9. Carga no Fuseki** | `make load-kg` | 30 min | 1 h | KG navegável em http://localhost:3030 |
| **10. Validação final** | `make validate` | 2 h | 1 h | Abre notebook Jupyter com gráficos e estatísticas |
| **Buffer** | — | 1 h | — | Imprevistos |

**Total seu envolvimento ativo:** ~6 h.

## Targets do Makefile

```bash
make help              # lista todos os targets com descrição

# Configuração e validação
make check             # verifica dependências
make python-venv       # cria .venv (se ainda não existe)
make fuseki-up         # sobe Apache Jena Fuseki via docker-compose
make fuseki-down       # derruba o container

# Teste rápido (PCAP pequeno público)
make test              # pipeline completa em ~100 MB de PCAP

# Pipeline principal
make download          # CIC-DDoS2019 Slowloris subset
make extract-ja4       # PCAPs → JA4 via tshark
make extract-flows     # PCAPs → flows via CICFlowMeter
make sessions          # flows + JA4 → sessions.parquet
make clusters          # sessions → clusters.csv (ground truth heurística)
make load-kg           # sessions/clusters → Apache Jena Fuseki

# Validação
make validate          # abre notebook validate.ipynb
make stats             # imprime contagens e estatísticas básicas

# Limpeza
make clean             # remove artefatos intermediários (mantém raw e KG)
make clean-all         # remove tudo (cuidado!)
```

## Saídas esperadas

Ao final do Sprint 1, em `$DATA_ROOT`:

- `processed/ja4/cic-ddos-2019/*.csv` — JA4 por flow
- `processed/flows/cic-ddos-2019/*.csv` — flows CICFlowMeter
- `processed/sessions/cic-ddos-2019.parquet` — sessões reconstruídas
- `processed/clusters/cic-ddos-2019.csv` — *clusters* derivados
- `kg/fuseki-tdb2/` — base RDF do Fuseki
- `kg/exports/cic-ddos-2019.ttl` — snapshot Turtle exportável

## Gates de aprovação

- [ ] `make test` produz JA4 não-vazio para ao menos um *handshake* TLS observado
- [ ] `sessions.parquet` cobre ≥ 80% dos flows originais
- [ ] Pelo menos 10 *clusters* manualmente validados em `clusters.csv`
- [ ] Fuseki responde `SELECT (COUNT(*) AS ?n) WHERE { ?s a kg:ApplicationSession }` com $n \ge 1000$
- [ ] `validate.ipynb` gera relatório com distribuições de JA4, duração de sessão, e estatísticas básicas

## Troubleshooting

Em caso de problemas, os logs estão em `$DATA_ROOT/logs/`. Os erros mais comuns:

| Sintoma | Causa provável | Solução |
|---|---|---|
| `tshark: command not found` | Wireshark não instalado | `brew install wireshark` |
| `JA4 column empty` | tshark < 4.0 (sem plugin JA4) | Atualizar Wireshark via Homebrew |
| `Docker daemon not running` | Docker Desktop fechado | Abrir Docker Desktop |
| `cic-ddos-2019/` vazio | Registro UNB pendente | Visitar https://www.unb.ca/cic/datasets/ddos-2019.html |
| `CICFlowMeter not found` | Java/JAR não baixado | `make install-cicflowmeter` |

## Onde se encaixa no paper

Os dados produzidos pelo Sprint 1 servem como:

- **§4.2 Conjunto de Dados** — *dataset* secundário para comparação com literatura
- **§5.1 Desempenho Geral por Cenário** — *baseline* Cenário A em dados reais
- **§5.3 Análise por Sub-Relação** — distribuições reais de JA4 e padrões temporais para calibração de `τ_DTW`, `τ_payload`
