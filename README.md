# Grafos de Conhecimento Centrados em Sessão HTTP

> Modelar a **sessão HTTP como entidade ontológica de primeira classe** e raciocinar sobre **conjuntos de sessões correlacionadas** — não sobre sessões isoladas.

---

## A tese, em uma frase

Campanhas coordenadas e **furtivas** de DDoS de Camada 7 (Slowloris distribuído calibrado para parecer benigno por sessão, *credential stuffing*, abuso de API por frota de *tokens*) ficam sub-limiares em qualquer sessão isolada — o sinal de ataque mora na **estrutura entre sessões** ligadas por identidade reaproveitada, *fingerprint* TLS (JA4) ou prefixo de cliente. Tratamos esse padrão estrutural como **objeto raciocinável** numa ontologia OWL, em vez de descartá-lo no vetor de *features* do classificador.

---

## Como isso muda a detecção

| Eixo | Estado da arte | Nossa proposta |
|---|---|---|
| Representação da sessão | Vetor de *features* (taxa, duração, contagens) | **Entidade ontológica** com identidade, alvo, comportamento, mitigação |
| Granularidade do raciocínio | Por sessão isolada | **Entre sessões** via `relatedTo` (identidade, JA4, prefixo IP) |
| Saída do detector | Rótulo binário opaco | **Cadeia de evidência** percorrendo o grafo |
| Mitigação aplicada | Limite global (afeta legítimos) | **Escopo cirúrgico** derivado do discriminador do *cluster* |
| KGs em cibersegurança | Construídos estaticamente a partir de texto | **Construído em tempo de execução** sobre o tráfego |

A relação `relatedTo` no grafo é o que carrega a campanha: une sessões que compartilham identidade, JA4 ou prefixo, mesmo quando IPs e cookies divergem. Sem ela, o detector vê 1000 sessões "benignas"; com ela, vê uma campanha de 1000 sessões.

---

## Os quatro pilares

### 1. Ontologia centrada em sessão (OWL 2 DL)

Classe central `ApplicationSession` com cinco relações tipadas:

| Relação | Liga a sessão a... |
|---|---|
| `hasIdentity` | Cookie, *token* JWT, *username*, **JA4 TLS fingerprint** |
| `targets` | Endpoint (`AuthEndpoint`, `APIEndpoint`, `StaticAsset`) |
| `exhibitsBehavior` | `UserBehavior` ou `BotBehavior` |
| `relatedTo` | **Outra sessão** com identidade/JA4/prefixo compartilhado — habilitador do raciocínio entre sessões |
| `mitigatedBy` | Política aplicável com **escopo derivado** do *cluster* |

Três subclasses de ataque coordenado, todas com `exhibitsCrossSessionStructure`:

- **`CoordinatedHTTPFlood`** — sessões convergindo no mesmo `Endpoint` com taxa agregada alta. Caso de teste experimental: **Slowloris distribuído** (ver [`TESTAGEM.md`](TESTAGEM.md)).
- **`CredentialStuffing`** — múltiplas sessões `relatedTo` contra `AuthEndpoint` com falha agregada alta.
- **`CoordinatedAPIAbuse`** — múltiplos *tokens* distintos mas mesmo JA4/ASN convergindo em `APIEndpoint`.

### 2. *Pipeline* em tempo de execução

Cada requisição HTTP eleva a instâncias ontológicas dentro de uma janela operacional $W = 5$ min; sessões viram nós persistentes; `relatedTo` é populada por *match* de identidade/JA4/prefixo na janela; estado é purgado fora dela.

Diferencial: KGs em cibersegurança hoje são **estáticos**, construídos a partir de CVEs e texto de *threat intel*. O nosso é **vivo**, alimentado pelo tráfego.

### 3. Regras semânticas explicáveis (SPARQL/SWRL)

Todas as regras dependem de `relatedTo`. Nenhuma é satisfeita por uma sessão isolada. Quando disparam, emitem veredicto + cadeia de evidência exportável em **JSON-LD** e **STIX 2.1**.

### 4. Mitigação com escopo cirúrgico

A cadeia de evidência **identifica o discriminador do *subconjunto coordenado*** — as sessões que compartilham o JA4 modal (a assinatura da campanha), **não** o *cluster* `(endpoint, janela)` cru. Esse discriminador vira o `scope` da política de mitigação — *Challenge* só para o tráfego que bate o JA4, não para todo mundo na rota. Tráfego legítimo é preservado; o ataque é contido. (Derivar o escopo do cluster inteiro era um erro: os legítimos diluíam o JA4 do atacante abaixo do limiar de cobertura e o escopo degradava para o endpoint todo — i.e. global; restringir ao subconjunto coordenado restaura o 0% cirúrgico.)

Esse é o eixo onde nossa contribuição se diferencia de WAFs e *rate-limiters* tradicionais: eles **funcionam** contra a campanha (com limite global), mas pagam em **dano colateral em legítimos** — métrica que produtos comerciais auto-reportam mas a literatura acadêmica não usa sistematicamente em L7 DDoS.

---

## Como testamos

Anchored em **Slowloris** (e variantes: slowhttptest, HULK, GoldenEye) como caso experimental. Por quê Slowloris:

- **Cobertura em datasets públicos** — único ataque L7 HTTP/HTTPS bem documentado em CIC-DDoS2019, CICIDS2017, CIC-IoT2023 e BCCC-cPacket-Cloud-DDoS-2024.
- **Funciona sobre HTTPS** — *headers* parciais sobre conexão TLS estabelecida; JA4 é capturável.
- **Distribuível** — slowloris de K hosts contra o mesmo alvo encena o Cenário B/C da nossa parametrização.
- **Ferramentas open-source disponíveis** para reprodução em laboratório local (slowhttptest, slowloris.py).
- **Mapeia diretamente para `CoordinatedHTTPFlood`** — K=1 é Slowloris clássico; K alto é a campanha distribuída.

Avaliação combinando três fontes (zero-cost, sem dados de produção):

1. **Gerador sintético em Python** — controle paramétrico total sobre K (grau de distribuição), para Cenários A/B/C.
2. **Laboratório local em Docker** — Nginx com módulo JA4 + Flask + slowhttptest + Locust; JA4 real, baixa escala.
3. **Datasets públicos** — BCCC-cPacket-Cloud-DDoS-2024 (primário) e CIC-DDoS2019 (secundário) como *sanity check* do Cenário A.

Detalhes em [`TESTAGEM.md`](TESTAGEM.md).

---

## Estrutura do repositório

```
knowledge-graph-ddos-article/
│
├── README.md                       # Este arquivo
├── CONCEITOS.md                    # Fundamentação: sessão como entidade, raciocínio entre sessões, JA4
├── TESTAGEM.md                     # Plano experimental ancorado em Slowloris
│
├── papers/
│   ├── http-session/               # ◀ Foco ativo — paper em desenvolvimento
│   │   ├── README.md
│   │   ├── article.tex
│   │   ├── article.pdf
│   │   └── references.bib          # cópia de shared/references.bib (sincronizar via scripts/sync-bib.sh)
│   │
│   └── cdn-crosssurface/           # Engavetado — extensão futura DNS↔HTTP em CDNs
│
├── shared/
│   └── references.bib              # Bibliografia compartilhada
│
├── ontology/
│   └── ddos_ontology.owl           # Ontologia (a refinar para foco em sessão)
│
├── src/
│   └── graph_builder/
│       └── knowledge_graph_ddos.py # Implementação de referência
│
├── docs/
│   ├── estrutura-do-artigo.md      # Mapa seção-a-seção do paper
│   ├── referencias.md              # Catálogo expandido de referências por função argumentativa
│   ├── knowledge_graph_diagram.md
│   ├── mathematical_formalization.tex
│   ├── leituras-pt/                # Resumos em PT-BR de papers lidos
│   ├── pdfs/                       # PDFs originais
│   └── pontos-de-reflexao/         # Decisões em aberto, prior art validation
│
├── ARTIGOS/
└── results/
```

---

## Estado atual

**Sprint 6 (2026-08-22) — submissão NOMS.** Versão em inglês / IEEE 2-colunas em
[`papers/http-session-noms/`](papers/http-session-noms/). No caminho, o endurecimento
encontrou **três defeitos de realismo no gerador** e um **erro conceitual na derivação de
escopo de mitigação** (escolha por frequência modal seleciona o fingerprint *legítimo*
contra botnets heterogêneas: 0% dos atacantes, 39–61% dos usuários). Corrigidos; o
critério passou a ser **enriquecimento** sobre perfil histórico. Detalhes, tabelas e
fronteiras medidas em [`experiments/sprint-6-noms/`](experiments/sprint-6-noms/).

**Fase B (Sprints 1–5) + os 4 pilares + endurecimento em dados reais + consolidação do
paper concluídos (2026-06).** Raciocínio das decisões e significado dos cálculos por
etapa: [`experiments/METODOLOGIA-DECISOES-RESULTADOS.md`](experiments/METODOLOGIA-DECISOES-RESULTADOS.md);
resultados em dados reais e ameaças à validade:
[`experiments/DEEP-DIVE-FINDINGS.md`](experiments/DEEP-DIVE-FINDINGS.md); status atual e
pendências: [`experiments/RESUME.md`](experiments/RESUME.md).

| Componente | Status |
|---|---|
| §1 Introdução do paper | ✅ Escrita completa |
| §2–§6 + Apêndice | ✅ Consolidados com resultados reais + caveats; §5 preenchida (tabelas + *money figure*); §2 revisado |
| *Pipeline* de extração (PCAP→sessões→KG) | ✅ Executado — CICIDS2017 + CIC-IoT2023 no Fuseki |
| Extração de JA4 dos *datasets* | ✅ Feita (gates G1–G2 PASS) |
| Gerador sintético parametrizado por K | ✅ Calibrado (KS≤0.02), modo *stealth* |
| Ambiente Docker do laboratório (Fuseki) | ✅ Funcional (TDB2 no SSD; bulk load nativo) |
| *Baselines* (Fernandes, Bharathi, Kemp) | ✅ Implementados (operacionalizações; no acaso em ataque furtivo — ver DEEP-DIVE-FINDINGS) |
| **Generalização em dados reais** (6 ataques, 2 datasets) | ✅ ML por-sessão **forte** já atinge AUC 0,98–1,00 sozinho; entre sessões fica ~1,00 (ganho ≈0): ataques reais convencionais têm assinatura por sessão |
| Ablação a/b/c/d + estatística (n=30) | ✅ regime furtivo-distribuído sintético (cenário realista de mesmo serviço, :443): (a) forte 0,519 e (b) ontologia s/ relatedBy 0,527 ambos no acaso → (d) 0,968 (K=50); (d)−(c) p_bonf=7,4×10⁻⁹, d=12,2 |
| Comparação com KLAGE (CIC-IoT2023) | ✅ (d) F1=0,911 e (a') por-sessão forte F1=0,900 superam KLAGE 0,841; o F1=0,18 antigo era artefato do baseline magro (caveat: granularidade nó-vs-sessão) |
| Ontologia OWL: 6 sub-propriedades `relatedBy_*` ponderadas | ✅ Formalizadas (com `coordinationWeight`) |
| Alinhamento de namespace ontologia↔dados em runtime | ⏳ Pendente (instâncias usam namespace distinto do `.owl`) |
| **Pilar 4** (cadeia de evidência JSON-LD/STIX + mitigação cirúrgica) | ✅ Codado + rodado em cluster real e sintético calibrado no cenário realista de mesmo serviço (cirúrgico 0% vs global 100%, n=30, K=1000; escopo derivado do **subconjunto coordenado**, não do cluster cru); não se manifesta no CIC (LAN+não-TLS, surgical=global=31,8%) |
| **Pilar 2** (raciocínio simbólico SWRL+SPARQL · veredicto-como-derivação) | ✅ Codado; regra dispara com a derivação; pesos lidos da ontologia |
| Calibração empírica de pesos $w_i$ | ✅ No cenário realista de mesmo serviço a calibração por sessão corrobora a **ordem** (TLS dominante; melhor 1,0/0,3/0,3; pesos do paper atingem o mesmo AUC ótimo 0,943, robustos a ±20%; TLS único sinal discriminativo isolado); valores absolutos exigem produção — ver DEEP-DIVE-FINDINGS |
| RT-IoT2022 (2º dataset KLAGE) · avaliação em produção | ⏳ Pendente (trabalho futuro) |

---

## Por onde começar

- **Entender a ideia:** ler [`CONCEITOS.md`](CONCEITOS.md) (sessão como entidade, raciocínio entre sessões, papel do JA4).
- **Entender o experimento:** ler [`TESTAGEM.md`](TESTAGEM.md) (por que Slowloris, qual *dataset*, como o lab é montado).
- **Entender o paper:** ler [`papers/http-session/README.md`](papers/http-session/README.md) e [`papers/http-session/article.tex`](papers/http-session/article.tex).
- **Acompanhar decisões em aberto:** consultar [`docs/pontos-de-reflexao/`](docs/pontos-de-reflexao/).

---

## O que ficou fora do escopo

- **DNS / CDN cross-surface** — formalizado em [`papers/cdn-crosssurface/`](papers/cdn-crosssurface/), engavetado como direção futura.
- **Defesas volumétricas (Camada 3/4)** — assumidas como camada anterior; complementamos, não substituímos.
- **Dados de produção** — declarados como direção futura sob aprovação ética; usamos apenas tráfego sintético, laboratório local e *datasets* públicos.
