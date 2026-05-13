# Conceitos Fundamentais — Sessão HTTP como Entidade Semântica

> **Documento de fundamentação** do paper [papers/http-session](papers/http-session/) — *Grafos de Conhecimento Centrados em Sessão HTTP para Detecção Explicável de DDoS*. Para a visão de projeto, ver [`README.md`](README.md). Para o mapa seção-a-seção do paper, ver [`ESTRUTURA_DO_ARTIGO.md`](ESTRUTURA_DO_ARTIGO.md).

---

## Índice

1. [O problema que justifica a abordagem](#1-o-problema-que-justifica-a-abordagem)
2. [Ontologia, OWL e Grafo de Conhecimento](#2-ontologia-owl-e-grafo-de-conhecimento)
3. [Por que a sessão HTTP deve ser tratada como entidade](#3-por-que-a-sessão-http-deve-ser-tratada-como-entidade)
4. [Raciocínio cross-session](#4-raciocínio-cross-session)
5. [A ontologia do paper](#5-a-ontologia-do-paper)
6. [Três especializações de ataque coordenado](#6-três-especializações-de-ataque-coordenado)
7. [Pipeline em tempo de execução vs. KGs estáticos](#7-pipeline-em-tempo-de-execução-vs-kgs-estáticos)
8. [Cadeia de evidência e explicabilidade](#8-cadeia-de-evidência-e-explicabilidade)
9. [Por que isso é inovador](#9-por-que-isso-é-inovador)

---

## 1. O problema que justifica a abordagem

### A natureza dos ataques de Camada 7 coordenados

DDoS de Camada 7 sobre HTTP atinge três classes de endpoint:

| Endpoint | Exemplo | Ataque típico |
|---|---|---|
| **Autenticação** | `/api/auth/login` | **Login Flood**, *Credential Stuffing* |
| **API** | `/api/users/{id}` | **Abuso de API** distribuído por *tokens* |
| **Processamento custoso** | `/search?q=...` | **HTTP Flood** contra rotas caras |

As variantes mais perigosas são **coordenadas**: múltiplas sessões, frequentemente vindas de centenas/milhares de origens, atacando o mesmo endpoint sob direção comum. **Vista isoladamente, cada requisição é indistinguível de uma legítima.** O sinal mora em duas camadas:

1. **Padrão de uso da sessão** — entropia das rotas, consistência do *fingerprint*, ritmo de chamadas.
2. **Padrão estrutural entre sessões** — quantas falhas de login em quantas identidades, quantos *tokens* convergem para o mesmo endpoint, qual o prefixo IP comum.

### O que o estado da arte faz hoje

A meta-análise de Odusami et al. (2020) sobre **75 estudos** mostra:

- **47% dos métodos** usam *features* extraídas de sessões (taxa, duração, contagens).
- Em **todos** esses métodos, **a sessão é reduzida a um vetor numérico antes do classificador**.
- O detector vê estatísticas. Não vê a sessão.

Consequência: o detector **não consegue raciocinar sobre relações entre sessões**, sobre identidades reaproveitadas, ou sobre padrões que só emergem quando duas sessões individualmente normais são analisadas em conjunto.

**Detectores ML para HTTP de Camada 7 reportam AUC competitivo, mas seus autores admitem [Kemp et al., 2023]:**

- Metodologia não validada em tempo real.
- Resultado binário, sem explicação ontológica.

### Três deficiências motivam o trabalho

1. **Sessão como *feature aggregate*, não como entidade.**
2. **Ausência de explicação ontológica** — analistas decidem dezenas de vezes por hora; "parece um ataque" não é decisão.
3. **Ausência de raciocínio *cross-session*** — campanhas coordenadas dependem dele.

---

## 2. Ontologia, OWL e Grafo de Conhecimento

### Ontologia (definição operacional)

**Ontologia** é uma representação formal e estruturada de um domínio, com:

- **Classes** — as "coisas" do domínio (`ApplicationSession`, `Endpoint`, `Identity`).
- **Relações tipadas** — como elas se conectam (`hasIdentity`, `targets`, `relatedTo`).
- **Propriedades** — características das instâncias (`requestRate`, `failureRatio`).
- **Restrições / Axiomas** — regras que toda instância válida obedece.

### Ontologia vs. Banco de dados relacional

| Aspecto | DB Relacional | Ontologia |
|---|---|---|
| Estrutura | Tabelas fixas | Grafo flexível |
| Relações | FKs implícitas | Arestas nomeadas |
| Semântica | No *schema* | Explícita e formal |
| Inferência | Não suportada | Raciocínio automático (OWL reasoners) |
| Extensibilidade | *Schema* rígido | Subclasses, novas relações sem reestruturar |

### OWL (Web Ontology Language)

Padrão W3C para serializar ontologias. Em Turtle:

```turtle
:ApplicationSession  rdf:type owl:Class ;
    rdfs:label "Sessão de aplicação HTTP" .

:hasIdentity  rdf:type owl:ObjectProperty ;
    rdfs:domain :ApplicationSession ;
    rdfs:range :Identity .

:session_a3f2  rdf:type :ApplicationSession ;
    :hasIdentity :token_xyz ;
    :targets :authEndpoint_login .
```

### Grafo de Conhecimento (KG)

**KG = (E, R, P)** com entidades (E), relações (R) e propriedades (P) — instanciação de uma ontologia com dados reais. No paper, o KG é populado **em tempo de execução** a partir do tráfego HTTP.

---

## 3. Por que a sessão HTTP deve ser tratada como entidade

A sessão HTTP é a **unidade natural de comportamento** de um cliente contra a aplicação — agrupa múltiplas requisições sob uma mesma identidade observada (cookie, *token* JWT, *username* em formulário, *fingerprint* TLS).

Também é o objeto que detectores existentes mais **sumarizam** e menos **modelam semanticamente**.

### O custo da redução a vetor

Quando se aplaina a sessão em um vetor `[req_rate, duration, op_count, ...]`:

- **Perde-se a identidade** que liga sessões.
- **Perde-se o endpoint** específico que ela visa.
- **Perde-se o histórico observável** (que requisição veio antes de qual).
- **Perde-se a possibilidade de ligar sessões** que compartilham identidade ou *fingerprint*.

### Sessão como entidade preserva o que importa

Modelada como **classe ontológica** (`ApplicationSession`):

- **Tem identidade.** Cada sessão é um nó com IRI estável dentro da janela operacional.
- **Tem alvo.** A relação `targets` aponta para o endpoint sob estresse.
- **Tem comportamento.** A relação `exhibitsBehavior` aponta para `UserBehavior` ou `BotBehavior`.
- **Tem laços com outras sessões.** A relação `relatedTo` é o que habilita o raciocínio entre sessões.
- **Tem mitigação.** A relação `mitigatedBy` aponta para a política aplicável.

A sessão deixa de ser estatística e passa a ser **objeto raciocinável**.

---

## 4. Raciocínio cross-session

### Definição

**Raciocínio *cross-session*** é a capacidade de relacionar múltiplas sessões através de identificadores compartilhados do cliente — em vez de tratar cada sessão como caso independente.

### Por que é estruturalmente necessário

Campanhas coordenadas têm **assinatura fraca por sessão**, **estrutura clara em conjunto**:

- *Credential Stuffing* contra `/api/auth/login`: cada sessão tenta poucos pares usuário/senha; o conjunto representa milhões.
- Abuso de API por frota de *tokens*: cada *token* respeita sua quota; a frota agregada degrada o serviço.
- HTTP Flood distribuído: cada IP envia poucas req/s; a *botnet* sustenta 100k+ req/s.

Detectores que reduzem a sessão a *features* tratam cada caso isoladamente — perdem a campanha.

### Os três sinais estruturais

A relação `relatedTo` no grafo é populada por três sinais distintos:

| Sinal | Quando dispara | Resistência a evasão |
|---|---|---|
| **Identidade reaproveitada** | Mesmo *username*, *token* ou cookie em múltiplas sessões | Forte se a identidade não foi pulverizada |
| **TLS fingerprint** (JA3/JA4) | Mesmo *handshake* TLS, mesmo cliente *software* | Resiliente a mudança de IP |
| **Prefixo IP** | Mesmo bloco /24 ou ASN | Fraco se atacante usa *proxies* residenciais |

A combinação desses três sinais permite detectar a campanha **mesmo quando o atacante varia um deles**.

### TLS Fingerprint (JA3/JA4) — o ingrediente que muitos detectores ignoram

Assinatura computada a partir do *handshake* TLS — identifica o *software* cliente (curl com flags específicas, headless Chrome customizado, biblioteca HTTP de Python) mesmo quando o **IP de origem muda**. JA3 e JA4 são implementações conhecidas.

---

## 5. A ontologia do paper

### Classe central

```turtle
:ApplicationSession  rdf:type owl:Class ;
    rdfs:label "Sessão de aplicação HTTP" ;
    rdfs:comment "Unidade de comportamento de um cliente contra a aplicação." .
```

### Cinco relações tipadas

| Relação | Domínio | Imagem | Significado |
|---|---|---|---|
| `hasIdentity` | `ApplicationSession` | `Identity` | Cookie, *token*, *username* ou *fingerprint* TLS |
| `targets` | `ApplicationSession` | `Endpoint` | Endpoint da aplicação atingido |
| `exhibitsBehavior` | `ApplicationSession` | `Behavior` | `UserBehavior` ou `BotBehavior` |
| `relatedTo` | `ApplicationSession` | `ApplicationSession` | **Habilitador do raciocínio cross-session** |
| `mitigatedBy` | `ApplicationSession` ∪ `Attack` | `Mitigation` | `RateLimit`, `Challenge`, `Block` |

### Hierarquia de classes auxiliares

```
Endpoint
├── AuthEndpoint          (rotas de autenticação)
├── APIEndpoint           (rotas de API)
└── StaticAsset           (recursos estáticos cacheáveis)

Identity
├── Cookie
├── Token                 (JWT etc.)
├── Username
└── TLSFingerprint        (JA3/JA4)

Behavior
├── UserBehavior
└── BotBehavior

Mitigation
├── RateLimit
├── Challenge             (CAPTCHA, prova de trabalho)
└── Block
```

### Alinhamento com STIX 2.1 e MITRE ATT&CK

- **STIX 2.1:** cadeia de evidência exportável como `indicator` + `observed-data` + `relationship`.
- **MITRE ATT&CK:** os três ataques coordenados mapeiam para **T1498.001** (Application Layer DoS) com refinamento por sub-técnica.

---

## 6. Três especializações de ataque coordenado

Todas subclasses de `ApplicationLayerAttack`, todas com a propriedade comum **`exhibitsCrossSessionStructure`** — i.e., múltiplas sessões compartilhando identidade, *fingerprint* TLS ou prefixo de IP enquanto convergem sobre o mesmo `Endpoint`.

### 6.1 `CoordinatedHTTPFlood`

**Padrão semântico:**

- Conjunto de sessões $\{s_1, \ldots, s_n\}$ ligadas por `relatedTo`.
- Taxa agregada de requisições contra o **mesmo** `Endpoint` excede $\tau_{\text{rate}}$.
- Cada sessão exibe `BotBehavior` (baixa entropia de rotas).

**Sinal estrutural que sustenta:** *fingerprint* TLS comum ou prefixo IP comum, mesmo com cookies/IPs diferentes.

### 6.2 `CredentialStuffing` (subclasse de `LoginFlood`)

**Padrão semântico:**

- Conjunto de sessões com `relatedTo` (identidade reaproveitada, *fingerprint* TLS ou prefixo IP).
- Todas com `targets` apontando para um `AuthEndpoint`.
- Razão agregada de falha de autenticação excede $\tau_{\text{fail}}$.

**Sinal estrutural que sustenta:** *username* repetindo entre sessões com identidade aparente diferente, ou *fingerprint* JA4 idêntico em milhares de sessões.

### 6.3 `CoordinatedAPIAbuse`

**Padrão semântico:**

- Múltiplas sessões com `hasIdentity` distintos (diferentes *tokens*).
- Mas `relatedTo` via *fingerprint* TLS ou prefixo de IP.
- Todas atingindo a **mesma** `APIEndpoint`.
- Taxa somada excede $\tau_{\text{api}}$, **mesmo que nenhuma sessão isolada exceda sua quota**.

**Sinal estrutural que sustenta:** mesma assinatura TLS + mesmo ASN + mesma `APIEndpoint`, com *tokens* aparentemente independentes.

---

## 7. Pipeline em tempo de execução vs. KGs estáticos

### Como KGs em cibersegurança são construídos hoje

Jia et al. (2018), Bonagiri et al. (2024) e o levantamento de Liu et al. (2022) — **KGs são construídos estaticamente a partir de texto**:

- CVEs e relatórios de vulnerabilidade.
- *Blogs* de inteligência de ameaças.
- Tickets de SOC, descrições de incidentes passados.

Resultado: o KG é um **registro pós-fato**, útil para enriquecimento e contexto — **não é mecanismo de detecção em tempo de execução**.

Liu et al. (2022) reconhecem a lacuna explicitamente:
> *"Ainda é pouco explícito como implementar o grafo de conhecimento para enfrentar dificuldades industriais reais em situações de ciberataque e defesa."*

### O que muda no paper

O *pipeline* opera em três fases por requisição:

1. **Extração de entidades** — instâncias de `HTTPRequest`, `ApplicationSession`, `Identity`, `Endpoint`.
2. **População de relações** — `hasIdentity`, `targets`, `exhibitsBehavior`, **`relatedTo`** (resolvida por *match* de identidade/fingerprint/prefixo na janela).
3. **Manutenção de janela** — sessões e relações ativas dentro de $W$ (padrão: 5 min); descarregadas após — mantém o grafo enxuto em produção.

**Diferencial:** o KG passa a ser **objeto vivo do plano de dados**, não registro pós-fato.

---

## 8. Cadeia de evidência e explicabilidade

Quando uma regra dispara, o motor emite um veredicto acompanhado de uma **cadeia de evidência** que enumera explicitamente:

- **Qual regra** disparou (`CoordinatedHTTPFlood` / `CredentialStuffing` / `CoordinatedAPIAbuse`).
- **Quais instâncias ontológicas** estão envolvidas — sessões, identidades, endpoints.
- **Quais valores observados** satisfizeram as condições.
- **Qual política de mitigação** é sugerida.

### Exemplo de cadeia (esquemático)

```json
{
  "verdict": "CredentialStuffing",
  "confidence": "high",
  "evidence_chain": {
    "rule": "credential_stuffing_v1",
    "sessions": ["s_a3f2", "s_b71c", "s_f98e", "..."],
    "identities_involved": 1247,
    "tls_fingerprint_shared": "ja4=t13d_1516_a09f8b...",
    "ip_prefix_observed": "203.0.113.0/24",
    "target_endpoint": "/api/auth/login",
    "auth_failure_ratio_aggregate": 0.94,
    "window_seconds": 300
  },
  "mitigation_suggested": {
    "policy": "Challenge",
    "scope": "fingerprint=ja4=t13d_1516_a09f8b..."
  }
}
```

Exportável em **JSON-LD** e **STIX 2.1**, compatível com SIEM.

### Por que isso é decisão e não hesitação

O analista de segurança não recebe "isto parece um ataque" — recebe:

- Qual endpoint está sob estresse.
- Quantas identidades estão envolvidas.
- Qual o *fingerprint* TLS comum.
- Qual o prefixo IP relevante.
- Qual mitigação aplicar e em qual escopo.

**Decisão tem fundamento; "hesitação fundada em ML" não.**

---

## 9. Por que isso é inovador

### Em uma frase

A combinação de **três escolhas** que, isoladas, já existiriam na literatura, mas que combinadas não existem:

1. **Sessão HTTP modelada como entidade ontológica de primeira classe** (não vetor de *features*).
2. **KG construído em tempo de execução** a partir do tráfego (não estaticamente de texto).
3. **Regras semânticas explícitas que dependem de `relatedTo`** entre sessões — habilitando raciocínio *cross-session* com cadeia de evidência auditável.

### O que sustenta a defesa científica do paper

| Eixo | Sustentação |
|---|---|
| **Lacuna confirmada por *survey***   | Odusami et al. (2020) — 47% dos 75 estudos usam *features* agregadas; **nenhum** trata sessão como entidade |
| **Lacuna confirmada pelos próprios autores ML** | Kemp et al. (2023) declara explicitamente: sem validação em tempo real, sem explicação |
| **Lacuna confirmada por *survey* de KGs** | Liu et al. (2022) — KGs hoje não enfrentam situações reais de ataque/defesa em tempo de execução |
| **Hipótese empírica testável** | Curva de *recall* vs. K — baselines caem, arcabouço com `relatedTo` mantém |
| **Ablação isola a contribuição** | (a) ML *features* → (b) ontologia sem `relatedTo` → (c) arcabouço completo |

### O que **não** está sendo afirmado

- **Não** estamos substituindo defesas volumétricas (Camada 3/4).
- **Não** estamos prometendo desempenho competitivo em ataque *single-source* de alto volume — métodos por limiar IP/sessão são competitivos nesse regime e o paper declara isso como limitação.
- **Não** estamos propondo um novo algoritmo de ML — a contribuição está na camada **representacional e de raciocínio**, sobre a qual ML pode ser uma das técnicas (mas não a única).

A vantagem do arcabouço cresce com o **grau de distribuição** da campanha. **É exatamente onde os detectores atuais falham.**

---

## Leitura sugerida (vinculada ao paper)

- **Para a tese:** [`papers/http-session/article.tex`](papers/http-session/article.tex) §1.
- **Para os baselines:** Fernandes et al. (2015), Bharathi & Sukanesh (2012), Kemp et al. (2023) — resumos em [`docs/leituras-pt/`](docs/leituras-pt/).
- **Para a lacuna em KGs:** Jia et al. (2018), Bonagiri et al. (2024), Liu et al. (2022).
- **Para o domínio:** Tripathi & Hubballi (2021), Odusami et al. (2020).
- **Para mais referências:** [`REFERENCIAS_EXPANDIDAS.md`](REFERENCIAS_EXPANDIDAS.md).
