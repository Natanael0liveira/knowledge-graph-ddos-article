# Plano de Testagem — Família Slow HTTP DDoS como Caso Experimental

> **Pergunta operacional:** como validar empiricamente que o raciocínio *cross-session* sobre o grafo detecta campanhas que defesas por sessão isolada não veem?
> **Resposta:** instâncias da **família Slow HTTP DDoS distribuído** como casos experimentais concretos, em três fontes complementares de dados.

Para a visão de projeto, ver [`README.md`](README.md). Para a fundamentação, ver [`CONCEITOS.md`](CONCEITOS.md). Para decisões em aberto, ver [`docs/pontos-de-reflexao/`](docs/pontos-de-reflexao/).

> **✅ Este plano FOI EXECUTADO (Fase B, Sprints 1–5, 2026-06-01).** Resultados,
> gates e *caveats* em [`experiments/RESUME.md`](experiments/RESUME.md) e nos READMEs de
> cada sprint. Resumo: detecção por-sessão colapsa em campanha furtiva distribuída
> (F1≈0.18) enquanto o arcabouço cross-session detecta (F1=0.911 no CIC-IoT2023 real,
> vs KLAGE 0.841). Resultados em dados reais e ameaças à validade:
> [`experiments/DEEP-DIVE-FINDINGS.md`](experiments/DEEP-DIVE-FINDINGS.md); metodologia
> e decisões por etapa: [`experiments/METODOLOGIA-DECISOES-RESULTADOS.md`](experiments/METODOLOGIA-DECISOES-RESULTADOS.md).

---

## Por que a família Slow HTTP DDoS

A categoria escolhida não é uma ferramenta única (Slowloris), mas uma **família** de ataques de Camada 7 que exploram conexões parciais ou sustentadas. Inclui Slowloris (RSnake, 2009), Slow POST / R.U.D.Y., Slow Read, HULK, GoldenEye, e suas variantes modernas em HTTP/2 — **Rapid Reset** (CVE-2023-44487, agosto de 2023) e CONTINUATION Flood (2024). Tripathi & Hubballi (2021) e Cambiaso et al. (2013) consolidam a taxonomia formal.

Cinco razões para ancorar a avaliação nessa família:

1. **É a classe de ataque L7 HTTP/HTTPS com maior cobertura em *datasets* públicos acadêmicos.** Slowloris, slowhttptest, HULK e GoldenEye aparecem em CIC-DDoS2019, CICIDS2017, CIC-IoT2023 e BCCC-cPacket-Cloud-DDoS-2024 — sobreposição em todos os quatro.
2. **Funciona sobre HTTPS nativamente.** Os ataques sustentam tráfego sobre conexões TLS estabelecidas — JA4 é capturável a cada *handshake*.
3. **Tem casos reais contemporâneos em escala recorde.** HTTP/2 Rapid Reset sustentou picos de 398 milhões RPS (Google), 201 milhões RPS (Cloudflare) e 155 milhões RPS (AWS) em setembro de 2023, com *botnet* de cerca de 20.000 máquinas. No segundo trimestre de 2025, Cloudflare reportou 6.500+ ataques *hyper-volumetric* (média de 71/dia) e crescimento de 129% YoY especificamente em HTTP DDoS. **A escala da *botnet* (K ≈ 20.000) cai diretamente no Cenário C da nossa parametrização (K ≥ 1000).**
4. **Mapeia diretamente para a classe ontológica `CoordinatedHTTPFlood`.** K=1 é o ataque clássico single-source (Cenário A); K alto é a versão distribuída (Cenários B e C). Variantes connection-holding (Slowloris, slow body, slow read) e rate-based (HULK, GoldenEye, Rapid Reset) ficam como subclasses ontológicas dentro da mesma família.
5. **É distribuível com ferramentas open-source.** slowhttptest, slowloris.py e implementações de referência das variantes rodam em qualquer Linux; com *namespaces* de rede, encenamos K origens distintas num único host.

**O que isso significa para o paper:** a contribuição **ontológica** (sessão como entidade) continua aplicável aos três ataques coordenados modelados (`CoordinatedHTTPFlood`, `CredentialStuffing`, `CoordinatedAPIAbuse`). A **avaliação experimental** se concentra no primeiro porque é o que tem dados públicos e relevância contemporânea verificada (Rapid Reset 2023, hyper-volumetric Q2 2025). Os outros dois ficam validados em laboratório com escopo reduzido, e como direções de extensão em §6.

---

## A questão honesta

Slowloris em *datasets* públicos é majoritariamente **single-source** (Cenário A). A versão **distribuída** com **identidade compartilhada** (Cenários B e C — onde nossa tese vive) não está em nenhum *dataset* acadêmico. Por isso a avaliação combina três fontes:

| Fonte | Cobre | Por quê |
|---|---|---|
| **Gerador sintético em Python** | Cenários A, B, C com K controlado | Controle paramétrico total; reproduzível |
| **Laboratório local em Docker** | Cenários A e B (K ≤ ~200) | JA4 real, *handshake* TLS real, baixa escala |
| **Datasets públicos** | Cenário A (single-source) | Validação contra literatura existente |

Cada fonte cobre uma fatia. Juntas, cobrem todo o espectro da nossa parametrização. Limitações declaradas explicitamente em §5.7 do paper.

---

## Fonte 1 — Gerador sintético em Python

**Onde:** `src/generator/synthetic_traffic.py` (a implementar).

**O que faz:** emite *eventos* HTTP estruturados diretamente para o *pipeline*, sem passar por rede. Cada evento tem os campos que importam:

```python
{
  "timestamp": "...",
  "src_ip": "203.0.113.42",
  "tls_ja4": "t13d1516h2_8daaf6152771_b186095e22b6",
  "session_id": "sid_a3f2",
  "identity_token": "...",  # opcional, por sessão
  "method": "GET",
  "path": "/api/auth/login",
  "headers": {...},
  "status_code": 200
}
```

**Parâmetros:**

- `K` — número de origens distintas sob coordenação comum (1, 10, 100, 1000, 10000)
- `legitimate_session_count` — número de sessões legítimas concorrentes
- `attack_type` — `slowloris_distributed`, `credential_stuffing`, `api_abuse`
- `window_seconds` — janela temporal (padrão 300)
- `ja4_sharing_prob` — fração das sessões coordenadas que compartilham JA4
- `seed` — semente para reprodutibilidade

**Calibração:** distribuições de taxa, duração e *path* sorteadas a partir de estatísticas extraídas do BCCC-cPacket-Cloud-DDoS-2024 (Fonte 3), não inventadas. Isso garante que o tráfego sintético é "plausível" — não decretado artificialmente fácil.

**Cobertura:** Cenários A (K=1), B (10 ≤ K ≤ 100), C (K ≥ 1000). É a única fonte que cobre o Cenário C.

---

## Fonte 2 — Laboratório local em Docker

**Onde:** `docker-compose.yml` (a implementar).

**Stack mínimo:**

```
┌──────────────────────────────────────────────────────────────────┐
│  [Locust]              → Clientes legítimos com sessão e cookies │
│                                                                  │
│  [slowhttptest]        → Atacante Slowloris/SlowHTTP             │
│   + namespaces de rede   (K origens distintas no mesmo host)     │
│                                                                  │
│  [Nginx + ja4 module]  → Reverse proxy, extrai JA4 a cada handshake│
│        │                                                         │
│        ▼                                                         │
│  [Flask app]           → /api/auth/login, /api/users/{id},       │
│                          /api/search; SQLite atrás               │
│        │                                                         │
│        ▼                                                         │
│  [Pipeline KG]         → Lê access.log com JA4, popula grafo,    │
│                          executa regras, emite veredicto         │
└──────────────────────────────────────────────────────────────────┘
```

**Ferramentas (todas FOSS):**

- **slowhttptest** — gera Slowloris, SlowHTTP, Slow Read.
- **slowloris.py** — versão Python, mais fácil de variar JA4.
- **Locust** — simula usuários legítimos com sessões persistentes.
- **Nginx + módulo nginx-ja4** (FoxIO) — extrai JA4 em produção real.
- **Flask + SQLite** — aplicação-alvo simples com os três tipos de endpoint.

**Escala alcançável num laptop M-series 16 GB RAM:** K ≤ ~200 origens reais simultâneas com *handshakes* TLS reais. Para K maior, Fonte 1.

**Cobertura:** Cenários A e B com JA4 real. Validação cruzada com Fonte 1 no Cenário B (mesmo K) — se as curvas batem, ganhamos confiança no sintético para extrapolar ao Cenário C.

---

## Fonte 3 — *Datasets* públicos

### Primário: BCCC-cPacket-Cloud-DDoS-2024

**Origem:** York University BCCC + cPacket, paper MDPI Information 2024.
**Acesso:** [Kaggle](https://www.kaggle.com/datasets/dhoogla/bccc-cpacket-cloud-ddos-2024) (free).
**Tamanho:** 17 cenários DDoS + 8 atividades benignas, 300+ *features* via NTLFlowLyzer, 26 *labels*.
**Por que primário:** coletado em **infraestrutura de nuvem real em 2024**, refletindo HTTPS contemporâneo. Mais moderno e fiel ao ambiente de produção atual do que CIC-DDoS2019 (2019, lab UNB).

### Secundário: CIC-DDoS2019

**Origem:** Canadian Institute for Cybersecurity, UNB.
**Acesso:** [UNB official](https://www.unb.ca/cic/datasets/ddos-2019.html) (free com registro).
**Tamanho:** 50M+ instâncias; subsets de 424k e 731k flows são padrão.
**Por que secundário:** padrão acadêmico canônico para DDoS — citado em centenas de papers. Validação cruzada com BCCC garante consistência com a literatura existente. PCAPs estão disponíveis para extração JA4 retroativa.

### Filtro aplicado em ambos

Mantemos apenas os ataques Slow HTTP DoS:

- **Slowloris** — *headers* parciais sustentados
- **slowhttptest** — variante com *body* parcial
- **HULK** — *HTTP Unbearable Load King*, randomiza *headers*
- **GoldenEye** — variante de HULK com *keepalive*
- **XerXes** — variante específica do CIC

Outros ataques (UDP Flood, SYN Flood, DNS Reflection, etc.) ficam fora — não são L7 HTTPS.

### Extração de JA4 retroativa

Nenhum dos *datasets* públicos vem com JA4 pré-extraído. Solução: processar os PCAPs com ferramenta open-source.

```bash
git clone https://github.com/D4-project/sensor-d4-tls-fingerprinting
# Pipeline: pcap → CSV de fingerprints → match (5-tupla, timestamp) com flows
```

Conexões sem *handshake* TLS observável (HTTP cleartext) ficam sem JA4 — tratamos como `tls_ja4 = NULL` no grafo, e a regra de detecção tem fallback para identidade ou prefixo IP. Isso é declarado em §4.2.

### Caveats que apareceram em peer review

- **Engelen et al. (2021)** alerta sobre rótulos ruidosos em CICIDS2017 — por isso CICIDS2017 fica fora desta seleção. CIC-DDoS2019 é distinto (não tem os problemas reportados em 2017).
- **Datasets cobrem majoritariamente single-source.** Por isso são *sanity check* do Cenário A, não primários para a tese de *cross-session*.
- **JA4 extraído retroativamente** pode divergir de JA4 vivo — efeito uniforme sobre todos os métodos (não enviesa a comparação).

---

## Métricas de avaliação

Três famílias, todas reportadas por cenário (A, B, C) × ataque × *baseline*:

### 1. Classificação padrão

Precisão, *recall*, F1, AUC, FPR por sessão.

### 2. *Recall* por **campanha** (não por sessão)

Para cada campanha coordenada instrumentada, qual fração foi detectada **como pertencente à campanha** (não apenas sessões individuais isoladas). Essa métrica captura diretamente o ganho do raciocínio *cross-session*.

### 3. Dano colateral em tráfego legítimo

Fração do tráfego legítimo que seria afetada pela mitigação resultante de cada método:

- *Baselines* tipicamente aplicam *rate-limit* global ou bloqueio por IP — afeta legítimos.
- Nosso arcabouço aplica mitigação com **escopo derivado do discriminador do *cluster*** — JA4, ou par (JA4, endpoint), ou prefixo + JA4 — preservando o resto.

Essa métrica é o que produtos comerciais auto-reportam (DataDome: FPR < 0.01% em CAPTCHAs servidos), mas que a literatura acadêmica de L7 DDoS não usa sistematicamente. Reportá-la é parte da contribuição metodológica do paper.

---

## Configuração experimental

- $n \ge 30$ execuções por cenário com *seeds* diferentes (intervalos de confiança)
- *Paired t-test* (paramétrico) e Wilcoxon (não-paramétrico) entre métodos
- Correção de Bonferroni para múltiplas comparações
- $\alpha = 0{,}05$
- Janela operacional $W = 300$ s (padrão do *pipeline*)

---

## Ablação — isolando a contribuição

**Quatro** configurações sobre o mesmo conjunto subjacente de atributos de tráfego:

| Config | Componente |
|---|---|
| **(a)** | ML *baseline* (Random Forest sobre *features* agregadas de sessão), sem ontologia |
| **(b)** | Arcabouço com ontologia mas **sem** a família `relatedBy_*` (sessões como nós isolados) |
| **(c)** | Ontologia + **apenas** `relatedByNetworkProximity` (o sinal de rede, peso baixo) |
| **(d)** | Arcabouço completo: família `relatedBy_*` ponderada (TLS/JA4, endpoint, rede, …) |

- (a) → (d): **contribuição total da abordagem**
- (c) → (d): **ganho específico dos sinais de peso alto (JA4/identidade) sobre só proximidade de rede**

Hipótese a validar: diferença (c)→(d) é pequena no Cenário A (single-source) e dominante no Cenário C (distribuído), onde a proximidade de rede é fraca e o JA4 compartilhado é que sustenta a detecção.

---

## *Baselines* contra os quais comparamos

Os três consomem o **mesmo conjunto de atributos** subjacente — a ablação isola a representação semântica, não a disponibilidade de *features*:

| *Baseline* | Aproximação | Implementação |
|---|---|---|
| Perfilamento estatístico | Fernandes et al. (2015) | PCA + limiarização sobre estatísticas de sessão |
| Matriz de comportamento | Bharathi & Sukanesh (2012) | *k-means* sobre matriz de *features* por sessão |
| ML supervisionado | Kemp et al. (2023) | Random Forest + SVM sobre o vetor |

---

## *Money figure* do paper

Curva de **recall × grau de distribuição (K)**:

- *Baselines* descendem entre Cenário B e C (perdem campanhas distribuídas)
- Configuração (b) — ontologia sem `relatedTo` — também descende, atenuado
- Configuração (c) — arcabouço completo — mantém estável

Essa curva é o que sustenta a tese empiricamente. Sem ela, o paper é só conceito.

---

## Limitações declaradas

Três limitações vão explícitas em §5.7 do paper:

1. **Cenário C (K ≥ 1000) avaliado puramente em sintético.** Validação cruzada com lab no Cenário B demonstra consistência entre os regimes, mas extrapolação para K alto não é validada em rede real. Avaliação em escala de produção fica como direção futura.

2. ***Datasets* públicos não contêm campanhas coordenadas distribuídas com identidade compartilhada.** São usados como *sanity check* para Cenário A, não como avaliação primária. Os outros dois ataques modelados (`CredentialStuffing`, `CoordinatedAPIAbuse`) são validados apenas em laboratório com escopo reduzido.

3. **Métrica de dano colateral medida sobre a mistura controlada de tráfego sintético + lab.** Em produção, a distribuição pode diferir; extensões com dados reais (anonimizados, sob aprovação ética) são necessárias para validação operacional.

---

## Cronograma (8 semanas, zero-cost)

| Sem. | Entrega |
|---|---|
| 1–2 | Gerador sintético `src/generator/synthetic_traffic.py` parametrizado por K |
| 3 | Refatoração do *pipeline* `src/kg/session_kg.py` para foco em sessão; Algoritmo 1; ontologia em Turtle |
| 4 | Regras SPARQL/SWRL para os três ataques; três *baselines* (Fernandes, Bharathi, Kemp); instrumentação da métrica de dano colateral |
| 5 | Laboratório local: Docker Compose com Flask + Nginx-JA4 + slowhttptest + Locust |
| 6 | Execução em lab — Cenários A e B com K ≤ 200, $n \ge 30$ *seeds* |
| 7 | Execução sintética — Cenário C com K ≥ 1000; validação cruzada com lab em K compartilhado |
| 8 | Análise estatística (IC, *paired t-test*, Wilcoxon, Bonferroni); *money figure*; amostragem qualitativa de cadeias de evidência |

---

## *Stack* completo (FOSS, zero-cost)

| Componente | Ferramenta |
|---|---|
| Linguagem do *pipeline* | Python 3.11+ |
| Ontologia OWL | Protégé (editor) + `owlready2` (runtime) |
| Consultas semânticas | `rdflib` + SPARQL |
| *Reasoner* | HermiT, Pellet via `owlready2` |
| Aplicação-alvo | Flask + SQLite |
| *Reverse proxy* + JA4 | Nginx + módulo `nginx-ja4` (FoxIO) |
| Orquestração | Docker + Docker Compose |
| Clientes legítimos | Locust |
| Atacante Slow HTTP | slowhttptest, slowloris.py |
| Extração JA4 retrofit | `sensor-d4-tls-fingerprinting` (D4-project) |
| Análise estatística | `scipy`, `statsmodels`, `pingouin` |
| Plotagem | `matplotlib`, `seaborn` |

Total: **R$ 0,00**.
