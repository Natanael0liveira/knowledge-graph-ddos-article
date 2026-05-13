# Grafos de Conhecimento Centrados em Sessão HTTP para Detecção Explicável de DDoS

> **Foco do repositório:** desenvolvimento do paper [papers/http-session](papers/http-session/) — submissão alvo *Computers & Security* (Elsevier, Qualis A2).

---

## 📋 Tese central

A **sessão HTTP**, tratada como entidade ontológica de primeira classe ligada por relações tipadas a identidade, *endpoint* e comportamento, habilita raciocínio *cross-session* que detectores baseados em *features* agregadas de sessão estruturalmente não conseguem realizar.

Em uma frase: campanhas coordenadas de Camada 7 (HTTP Flood distribuído, *credential stuffing*, abuso de API por frota de *tokens*) ficam **sub-limiares em qualquer sessão isolada**; o sinal de ataque mora na estrutura *entre* sessões — ligadas por identidade reaproveitada, *fingerprint* TLS ou prefixo de cliente. Esse é o sinal que perdemos quando reduzimos a sessão a um vetor numérico.

---

## 🎯 O que este paper propõe

| Eixo | Estado da Arte | Nossa Abordagem |
|---|---|---|
| Representação da sessão | Vetor de *features* agregadas (taxa, duração, contagens) | **Entidade ontológica** com identidade, alvo, comportamento, mitigação |
| Raciocínio | Por sessão isolada | **Cross-session** via `relatedTo` (identidade, *fingerprint* TLS, prefixo IP) |
| Saída | Rótulo binário | **Cadeia de evidência** sobre múltiplas sessões |
| KGs em cibersegurança | Construídos estaticamente a partir de texto de *threat intel* | **Construído em tempo de execução** a partir do tráfego HTTP |
| Ataques modelados | HTTP Flood genérico, Slowloris | **Coordinated HTTP Flood, Credential Stuffing, Coordinated API Abuse** |

A novidade central — e o que sustenta a submissão a Qualis A2 — é tratar a sessão HTTP como **objeto raciocinável** em vez de agregado de estatísticas, e modelar três especializações de ataque coordenado como subclasses ontológicas com regras semânticas explícitas.

---

## 📁 Estrutura do repositório

```
knowledge-graph-ddos-article/
│
├── README.md                       # Este arquivo — visão do projeto
├── ESTRUTURA_DO_ARTIGO.md          # Mapa seção-a-seção do paper http-session
├── CONCEITOS.md                    # Fundamentação: ontologia, sessão como entidade, raciocínio cross-session
├── MELHORIAS_QUALIS_A2A3.md        # Roadmap A2 — gap, plano de ação, baselines
├── REFERENCIAS_EXPANDIDAS.md       # Referências expandidas alinhadas ao paper
│
├── papers/
│   ├── http-session/               # ◀ FOCO ATIVO
│   │   ├── README.md
│   │   ├── article.tex             # Introdução completa; §2–§6 + Apêndice como esqueletos guiados
│   │   ├── article.pdf             # Saída de compilação
│   │   └── references.bib          # → symlink para shared/references.bib
│   │
│   └── cdn-crosssurface/           # Engavetado — direção futura (DNS↔HTTP em CDNs)
│       └── ...
│
├── shared/
│   └── references.bib              # Bibliografia compartilhada
│
├── ontology/
│   └── ddos_ontology.owl           # Ontologia OWL (a ser refinada para o foco em sessão)
│
├── src/
│   └── graph_builder/
│       └── knowledge_graph_ddos.py # Implementação de referência (pipeline em tempo de execução)
│
├── docs/
│   ├── knowledge_graph_diagram.md
│   ├── mathematical_formalization.tex
│   ├── leituras-pt/                # Resumos em PT-BR de papers relacionados
│   └── pdfs/                       # PDFs originais dos papers referenciados
│
├── ARTIGOS/
└── results/
```

---

## 🧩 Os quatro pilares do paper

### 1. Ontologia centrada em sessão (OWL)

A classe central é `ApplicationSession`, com cinco relações tipadas:

| Relação | Significado |
|---|---|
| `hasIdentity` | Liga a sessão à identidade do cliente (cookie, *token* JWT, *username*, *fingerprint* TLS) |
| `targets` | Liga a sessão ao endpoint alvo (`AuthEndpoint`, `APIEndpoint`, `StaticAsset`) |
| `exhibitsBehavior` | Liga a sessão a um perfil comportamental (`UserBehavior`, `BotBehavior`) |
| `relatedTo` | **Liga sessões entre si** quando compartilham identidade, *fingerprint* ou prefixo — habilitador do raciocínio *cross-session* |
| `mitigatedBy` | Liga sessão/ataque a política aplicável (`RateLimit`, `Challenge`, `Block`) |

Três especializações concretas de ataque coordenado, todas subclasses de `ApplicationLayerAttack` com a propriedade comum `exhibitsCrossSessionStructure`:

- **`CoordinatedHTTPFlood`** — múltiplas sessões com `relatedTo` convergindo no mesmo `Endpoint` a taxa agregada elevada
- **`CredentialStuffing`** (subclasse de `LoginFlood`) — múltiplas sessões com `relatedTo` contra `AuthEndpoint`, alta razão de falha de autenticação
- **`CoordinatedAPIAbuse`** — múltiplas identidades (`hasIdentity` distintos) mas `relatedTo` via *fingerprint*/prefixo, mesma `APIEndpoint`

### 2. Pipeline de construção em tempo de execução

Cada requisição HTTP é elevada a instâncias ontológicas; sessões viram nós **persistentes** dentro de uma janela operacional $W$ (padrão: 5 min). Diferencial vs. literatura: KGs em cibersegurança hoje são construídos *estaticamente* a partir de texto de *threat intel* (CVEs, blogs, relatórios) — não capturam estrutura de tráfego em tempo de execução.

### 3. Regras semânticas explicáveis

Todas as regras de detecção dependem de `relatedTo`; **nenhuma é satisfeita por uma sessão isolada**. Quando disparam, emitem veredicto + cadeia de evidência exportável em JSON-LD e STIX 2.1.

### 4. Avaliação por grau de distribuição

A *money figure* do paper é a curva de *recall* parametrizada pelo grau de distribuição da campanha:

| Cenário | Origens distintas | Hipótese |
|---|---|---|
| **A** — Concentrado | 1 | Baselines competitivos; ganho marginal |
| **B** — Moderadamente distribuído | 10 ≤ K ≤ 100 | Baselines começam a perder *recall*; raciocínio *cross-session* mantém |
| **C** — Altamente distribuído | K ≥ 1000 | Baselines caem perto do aleatório; **arcabouço completo preserva detecção** |

Ablação isola três configurações:

- **(a)** ML baseline com mesmas *features* agregadas
- **(b)** Ontologia **sem** `relatedTo` (sessões isoladas)
- **(c)** Arcabouço completo com `relatedTo`

Diferença (a)→(c) = ganho total; diferença (b)→(c) = ganho específico do raciocínio *cross-session*.

---

## ❓ Questões de pesquisa

- **QP1** — Como modelar a sessão HTTP em OWL com fidelidade para sustentar raciocínio sobre campanhas coordenadas, em vez de meramente agregar *features*?
- **QP2** — Quais regras semânticas detectam ataques sub-limiares em sessões individuais mas discerníveis pela estrutura *cross-session*?
- **QP3** — Como apresentar a decisão como cadeia de evidências auditável, ligando sessões, identidades e *endpoints*?
- **QP4** — Qual é o ganho empírico do raciocínio em nível de sessão sobre detecção baseada em *features* agregadas, controlando para o mesmo conjunto de atributos subjacentes?

---

## 🚀 Como compilar o paper

```bash
cd papers/http-session/
export LC_ALL=C
pdflatex -interaction=nonstopmode article.tex
bibtex article
pdflatex -interaction=nonstopmode article.tex
pdflatex -interaction=nonstopmode article.tex
```

O arquivo `references.bib` em `papers/http-session/` é *symlink* para [shared/references.bib](shared/references.bib).

---

## 📊 Estado do projeto

| Componente | Status | Descrição |
|---|---|---|
| §1 Introdução (paper) | ✅ Escrita completa | Contexto, problema, QPs, contribuições |
| §2 Trabalhos Relacionados | 🔄 Esqueleto guiado | Subseções marcadas, referências centrais já citadas |
| §3 Abordagem Proposta | 🔄 Esqueleto guiado | Ontologia, pipeline, regras descritas em prosa |
| §4 Metodologia | 🔄 Esqueleto guiado | Cenários A/B/C definidos; baselines listados |
| §5 Resultados | ⏳ Pendente | Aguarda execução experimental |
| §6 Conclusão | ⏳ Pendente | Curta — síntese + extensões |
| Ontologia OWL refinada para sessão | ⏳ Pendente | Versão atual em `ontology/` é precursora multi-vetor |
| Pipeline em tempo de execução | 🔄 Em refatoração | `src/graph_builder/` precisa de recorte para foco em sessão |
| Baselines (Fernandes, Bharathi, Kemp) | ⏳ Pendente | Implementação para ablação |
| Gerador sintético parametrizado por K | ⏳ Pendente | Necessário para Cenários A/B/C |

---

## 🎓 Veículo-alvo

**Primário:** *Computers & Security* (Elsevier, Qualis A2, IF≈3.5)

**Alternativas:** *Journal of Network and Computer Applications* (Elsevier, A2), *Journal of Cybersecurity* (Oxford, A2)

Para o roadmap detalhado até A2, ver [`MELHORIAS_QUALIS_A2A3.md`](MELHORIAS_QUALIS_A2A3.md).

---

## 📌 O que ficou fora do escopo

- **DNS/CDN cross-surface**: trabalho relacionado, formalizado em [papers/cdn-crosssurface](papers/cdn-crosssurface/) e engavetado como direção subsequente. A decisão foi recortar para um primeiro paper com contribuição mais defensável (sessão como entidade) antes de partir para o segundo (correlação DNS↔HTTP em CDNs).
- **Defesas volumétricas (Camada 3/4)**: o paper assume que ataques volumétricos clássicos são tratados em camadas anteriores; complementa, não substitui.
- **Resposta automatizada (SOAR)**: a cadeia de evidência é exportável em STIX 2.1, mas a integração SOAR fica como extensão.

---

## 📚 Documentos de apoio

- [`ESTRUTURA_DO_ARTIGO.md`](ESTRUTURA_DO_ARTIGO.md) — mapa seção-a-seção do paper, com o que está escrito vs. o que precisa ser produzido
- [`CONCEITOS.md`](CONCEITOS.md) — fundamentação: ontologia, OWL, sessão como entidade, raciocínio *cross-session*
- [`MELHORIAS_QUALIS_A2A3.md`](MELHORIAS_QUALIS_A2A3.md) — análise de *gap*, plano de ação, baselines, validação estatística
- [`REFERENCIAS_EXPANDIDAS.md`](REFERENCIAS_EXPANDIDAS.md) — referências expandidas alinhadas ao escopo do paper
- [`docs/knowledge_graph_diagram.md`](docs/knowledge_graph_diagram.md) — diagramas conceituais
- [`docs/mathematical_formalization.tex`](docs/mathematical_formalization.tex) — formalização matemática (em desenvolvimento)
- [`docs/leituras-pt/`](docs/leituras-pt/) — resumos em PT-BR dos papers que sustentam a fundamentação

---

## 🔗 Links úteis

- [STIX 2.1](https://oasis-open.github.io/cti-documentation/stix/intro) — exportação da cadeia de evidência
- [MITRE ATT&CK T1498.001](https://attack.mitre.org/techniques/T1498/001/) — Application Layer DoS
- [Protégé](https://protege.stanford.edu/) — editor da ontologia OWL
- [CICIDS2017](https://www.unb.ca/cic/datasets/ids-2017.html) — *dataset* secundário (Slowloris/Slow HTTP)
- [CIC-DDoS2019](https://www.unb.ca/cic/datasets/ddos-2019.html) — *dataset* secundário (componentes HTTP)
- [Computers & Security — guia para autores](https://www.sciencedirect.com/journal/computers-and-security/publish/guide-for-authors)

---

*Foco: sessão HTTP como entidade semântica de primeira classe para detecção explicável de DDoS de Camada 7.*
*Última atualização: Maio 2026.*
