# Experimentos — Pasta mestre

Este diretório contém o código e a configuração dos cinco sprints experimentais do paper. Os **dados** (PCAPs, *datasets* processados, *output* do KG) ficam fora do repositório, em um HD externo configurado via variável de ambiente. Apenas o código, *configs* e *logs* leves são versionados.

> **Plano consolidado:** [`../docs/pontos-de-reflexao/03-plano-de-acao.md`](../docs/pontos-de-reflexao/03-plano-de-acao.md)

## Setup inicial (uma vez)

### Pré-requisitos

| Ferramenta | Versão mínima | Como instalar (macOS) |
|---|---|---|
| **Python** | 3.11 | `brew install python@3.11` |
| **Docker Desktop** | 4.x | https://www.docker.com/products/docker-desktop |
| **tshark** | 4.0+ (tem JA4) | `brew install wireshark` |
| **GNU Make** | qualquer | já vem no macOS |
| **Java** | 17+ (para CICFlowMeter) | `brew install openjdk@17` |

Comando único para validar:

```bash
python3 --version && docker --version && tshark --version && make --version && java --version
```

### Configuração do HD externo

1. Conecte o HD externo. Identifique o caminho de montagem:

   ```bash
   df -h | grep -i volumes
   ```

2. Crie um diretório raiz para os dados (recomendado: `kg-ddos-data`):

   ```bash
   export DATA_ROOT=/Volumes/SeuHD/kg-ddos-data   # ajuste o nome do HD
   mkdir -p "$DATA_ROOT"
   ```

3. Execute o script de setup do diretório, que cria a estrutura completa e o `.env` da pasta `experiments/`:

   ```bash
   ./scripts/setup-data-storage.sh "$DATA_ROOT"
   ```

4. Confirme:

   ```bash
   cat experiments/.env
   # deve conter: DATA_ROOT=/Volumes/SeuHD/kg-ddos-data
   ls experiments/data
   # symlink para o HD externo, mostrando raw/, processed/, synth/, kg/, results/
   ```

## Estrutura por sprint

```
experiments/
├── README.md                       # Este arquivo
├── .env                            # DATA_ROOT (não versionado)
├── data → /Volumes/SeuHD/...       # symlink ao HD externo (não versionado)
├── requirements.txt                # dependências Python comuns aos sprints
│
├── sprint-1/                       # Pipeline de extração (PCAP → KG)
│   ├── README.md
│   ├── Makefile
│   ├── docker-compose.yml          # Apache Jena Fuseki
│   ├── configs/
│   ├── scripts/
│   │   ├── extract_ja4.py
│   │   ├── extract_flows.py
│   │   ├── build_sessions.py
│   │   ├── derive_clusters.py
│   │   └── load_to_fuseki.py
│   └── notebooks/
│       └── validate.ipynb
│
├── sprint-2/                       # Gerador sintético calibrado (✅)
├── sprint-3/                       # Baselines + ablação a/b/c/d (✅)
├── sprint-4/                       # Execução estatística n=30 + figura (✅)
├── sprint-5/                       # Comparação com KLAGE (✅ CIC-IoT2023)
├── pillar2-symbolic-reasoning/     # Pilar 2: SWRL+SPARQL, veredicto-como-derivação (✅)
├── pillar4-evidence-mitigation/    # Pilar 4: cadeia JSON-LD/STIX + mitigação cirúrgica (✅)
├── figures-candidatas/             # Figuras candidatas ao artigo (fora do .tex, p/ revisão)
├── METODOLOGIA-DECISOES-RESULTADOS.md  # Por quê/cálculos/resultados/prático por etapa
├── DEEP-DIVE-FINDINGS.md           # Resultados em dados reais (Passos A–C + Pilar 4)
└── RESUME.md                       # Ponto de parada / handoff (status + pendências)
```

> **Estado:** os 5 sprints e os 4 pilares do paper estão codificados e **executados em
> dados reais** (ver `DEEP-DIVE-FINDINGS.md`); o paper está consolidado com os resultados.
> Para o raciocínio das decisões e o significado dos cálculos por etapa, ver
> [`METODOLOGIA-DECISOES-RESULTADOS.md`](METODOLOGIA-DECISOES-RESULTADOS.md); o status
> atual e as pendências reais estão em [`RESUME.md`](RESUME.md).

## Estado atual — Fase B completa (2026-06-01)

| Sprint | Dataset | Status / resultado |
|---|---|---|
| **1** — Pipeline + KG | CICIDS2017 + CIC-IoT2023 | ✅ ambos carregados; gates G1–G4 PASS no `validate.ipynb` |
| **2** — Gerador sintético | calibrado pelo S1 | ✅ KS pass (D≤0.02); reprodutível; modo *stealth* |
| **3** — Baselines + ablação | sintético furtivo | ✅ (d) entre sessões ≫ (a) forte/baselines (0,969 vs 0,505 em K=50) |
| **4** — Execução estatística | sintético, n=30 | ✅ (d)−(c) em C: p_bonf=7,4×10⁻⁹, Cohen's d=14,1 |
| **5** — Comparação KLAGE | CIC-IoT2023 (real) | ✅ (d) F1=0,911 e (a') por-sessão forte F1=0,900 > KLAGE 0,841; vantagem entre-sessões marginal (dataset convencional) |

**Tese sustentada:** a vantagem do raciocínio entre sessões é real e estatisticamente
fortíssima no regime **furtivo-distribuído** sintético (S3, S4); em datasets reais
convencionais (S5) um ML por-sessão forte já basta, mas as contribuições de arcabouço
(sessão ontológica, veredicto simbólico, evidência, mitigação cirúrgica) permanecem. Cada sprint tem README próprio
com resultados, gates e caveats. Para carga no KG, ver `sprint-1/README.md`.

**Pendências (fora da Fase B):** RT-IoT2022 (download manual IEEE DataPort);
calibração real de w_i (sintético satura); pilares 2 e 4 do paper (cadeia de evidência
JSON-LD/STIX + mitigação cirúrgica) ainda não codificados; redação da §5.

## Como começar o Sprint 1

Após o setup do HD externo:

```bash
cd experiments/sprint-1
cat README.md   # leia primeiro
make help       # lista os targets disponíveis
```

Os comandos do Sprint 1 são orquestrados pelo `Makefile`, com targets nomeados (`setup`, `test`, `download`, `extract`, `sessions`, `cluster`, `load-kg`, `validate`). A maior parte roda em *background* sem requerer sua atenção; veja [`sprint-1/README.md`](sprint-1/README.md) para o passo a passo.
