# Estrutura do Paper — `papers/http-session/article.tex`

> **Título:** *Grafos de Conhecimento Centrados em Sessão HTTP para Detecção Explicável de DDoS*
> **Idioma:** Português
> **Veículo-alvo:** *Computers & Security* (Elsevier, Qualis A2)
> **Formato:** preprint, 12pt — alvo de 8–10 páginas
> **Fonte LaTeX:** [`papers/http-session/article.tex`](papers/http-session/article.tex)

Este documento é o **mapa seção-a-seção** do paper. Para cada seção indica: (i) o estado atual no `.tex`, (ii) o que ainda precisa ser produzido, (iii) as referências que sustentam o argumento. Para a visão de projeto, ver [`README.md`](README.md). Para fundamentação conceitual, ver [`CONCEITOS.md`](CONCEITOS.md).

---

## Resumo (`abstract`)

**Estado:** ✅ escrito (200–300 palavras, em português).

**Tese carregada pelo resumo:**

1. Campanhas coordenadas de Camada 7 imitam tráfego legítimo em baixas taxas e atravessam defesas por assinatura, limiar e quota.
2. O sinal mora na **correlação estrutural entre sessões** (identidade, *fingerprint* TLS, prefixo IP), não em qualquer sessão isolada.
3. Meta-análise de 75 estudos (Odusami et al., 2020) mostra que 47% dos detectores usam *features* agregadas de sessão; **nenhum trata a sessão como entidade raciocinável**.
4. KGs em cibersegurança são construídos estaticamente a partir de texto de *threat intel*, não como mecanismo de detecção em tempo de execução.
5. Propomos: ontologia OWL com sessão como entidade de primeira classe, três especializações de ataque coordenado, *pipeline* em tempo de execução, regras semânticas com cadeia de evidência *cross-session*, avaliação parametrizada por grau de distribuição com ablação.

**Palavras-chave:** Grafo de Conhecimento; Detecção de DDoS; Camada 7 HTTP; Sessão como Entidade Semântica; Raciocínio *Cross-Session*; IA Explicável.

---

## §1 Introdução

**Estado:** ✅ escrita completa.

### §1.1 Contexto e Motivação

- Volume de Camada 7 dobra a cada trimestre; incidente de 292k req/s por 13 dias [Tripathi & Hubballi, 2021].
- 93% dos operadores reportam DDoS de Camada 7 em 2016, contra 86% em 2013 [Odusami et al., 2020].
- HTTP visa três classes de endpoint: autenticação (Login Flood), API (abuso de API), processamento custoso (HTTP Flood).
- Variantes mais danosas são **coordenadas**: *credential stuffing*, abuso de API por frota de *tokens*, HTTP Flood de baixa intensidade por *botnet*.
- Cada requisição isolada é indistinguível de legítima; o sinal mora no padrão de uso da sessão e na estrutura *entre* sessões [Kemp et al., 2023; Bharathi & Sukanesh, 2012; Fernandes et al., 2015].

### §1.2 Definição do Problema — três deficiências do estado da arte

1. **Sessão como *feature aggregate*, não como entidade.** 47% dos métodos usam estatísticas agregadas de sessão; nenhum dos 75 estudos trata a sessão como entidade raciocinável.
2. **Ausência de explicação ontológica.** Detectores ML reportam métricas competitivas mas emitem rótulos binários sem fundamentação semântica. Em operação, "parece um ataque" é hesitação, não decisão.
3. **Ausência de raciocínio *cross-session*.** Campanhas coordenadas têm assinatura fraca por sessão, estrutura clara em conjunto. KGs textuais não capturam estrutura de tráfego em tempo de execução [Liu et al., 2022].

### §1.3 Questões de Pesquisa

- **QP1** — Como modelar a sessão HTTP em OWL com fidelidade para sustentar raciocínio sobre campanhas coordenadas?
- **QP2** — Quais regras semânticas detectam ataques sub-limiares em sessões individuais mas discerníveis pela estrutura *cross-session*?
- **QP3** — Como apresentar a decisão como cadeia de evidências auditável?
- **QP4** — Qual é o ganho empírico do raciocínio em nível de sessão sobre detecção baseada em *features* agregadas, controlando para o mesmo conjunto subjacente de atributos?

### §1.4 Contribuições

1. Ontologia OWL com sessão como entidade de primeira classe + três especializações de ataque coordenado, alinhada a STIX 2.1 e MITRE ATT&CK.
2. *Pipeline* de construção de KG em tempo de execução (vs. KGs estáticos de texto de *threat intel*).
3. Regras semânticas explicáveis que produzem cadeias de evidência *cross-session*.
4. Avaliação empírica com ablação isolando o ganho do raciocínio em nível de sessão.
5. Implementação de referência em código aberto.

### §1.5 Organização do Artigo

- §2 trabalhos relacionados; §3 abordagem; §4 metodologia; §5 resultados; §6 conclusão.

---

## §2 Trabalhos Relacionados

**Estado:** 🔄 esqueleto guiado com referências centrais já citadas — falta desenvolver a prosa.

### §2.1 Grafos de Conhecimento em Cibersegurança

**Argumento central:** KGs em cibersegurança são predominantemente construídos *estaticamente* a partir de texto de *threat intel* (CVEs, relatórios, *blogs*), e **não como mecanismo de detecção em tempo de execução**.

**Referências centrais a desenvolver:**
- Jia et al. (2018) — *practical approach to constructing a KG for cybersecurity* — exemplo canônico de construção textual
- Bonagiri et al. (2024) — KG aplicado a soluções práticas, ainda em registro de pós-fato
- Liu et al. (2022) — *survey* recente reconhecendo a lacuna: *"ainda é pouco explícito como implementar o KG para enfrentar dificuldades industriais reais"*

### §2.2 Detecção de Ataques DDoS de Camada 7 sobre HTTP

**Três famílias:**

1. **Perfilamento estatístico de tráfego/sessão** — Fernandes et al. (2015) com PCA sobre fluxo; Bharathi & Sukanesh (2012) com PCA sobre matriz comportamental.
2. **Aprendizado de máquina sobre *features* de fluxo ou sessão** — Kemp et al. (2023) como representante recente. **Limitação reconhecida pelos próprios autores:** metodologia não validada em tempo real, sem explicação ontológica.
3. **Levantamentos de domínio** — Tripathi & Hubballi (2021) como referência canônica recente.

**Análise crítica unificadora:** todas as famílias tratam a sessão como agregado de *features*, não como entidade.

### §2.3 Modelagem de Sessão em Detecção de Anomalias

**Argumento central:** Odusami et al. (2020) mostram que 47% dos estudos usam *features* agregadas de sessão. O estado da arte trata sessão como **vetor de estatísticas**, não como **objeto raciocinável** — o que limita raciocínio *cross-session* para campanhas distribuídas.

### §2.4 Posicionamento deste Trabalho

Síntese das três lacunas (sessão como agregado, ausência de explicação, ausência de raciocínio *cross-session*) e posicionamento como **primeiro arcabouço** que modela explicitamente a sessão HTTP como entidade semântica de primeira classe.

---

## §3 Abordagem Proposta

**Estado:** 🔄 esqueleto detalhado em prosa + algoritmo + figura tikz — falta especificar a ontologia em Turtle e formalizar as regras em SPARQL/SWRL.

### §3.1 Visão Geral do Sistema (Figura 1, `tikz`)

Quatro estágios: (i) ingestão de eventos HTTP, (ii) elevação a instâncias ontológicas, (iii) execução de regras semânticas, (iv) geração de cadeia de evidências.

### §3.2 Ontologia Centrada em Sessão

**Classe central:** `ApplicationSession` com relações tipadas:

| Relação | Domínio → Imagem |
|---|---|
| `hasIdentity` | `ApplicationSession` → `Identity` (`Cookie`, `Token`, `Username`, `TLSFingerprint`) |
| `targets` | `ApplicationSession` → `Endpoint` (`AuthEndpoint`, `APIEndpoint`, `StaticAsset`) |
| `exhibitsBehavior` | `ApplicationSession` → `Behavior` (`UserBehavior`, `BotBehavior`) |
| `relatedTo` | `ApplicationSession` → `ApplicationSession` — habilitador do raciocínio *cross-session* |
| `mitigatedBy` | `ApplicationSession` ∪ `ApplicationLayerAttack` → `Mitigation` (`RateLimit`, `Challenge`, `Block`) |

**Três especializações** de `ApplicationLayerAttack`, com propriedade comum `exhibitsCrossSessionStructure`:

- `CoordinatedHTTPFlood`
- `CredentialStuffing` (subclasse de `LoginFlood`)
- `CoordinatedAPIAbuse`

### §3.3 Construção do Grafo em Tempo de Execução (`Algoritmo 1`)

```
Entrada: fluxo de requisições R, ontologia O, janela W
Para cada requisição r ∈ R:
    s ← ResolverSessao(r)
    i ← ResolverIdentidade(r)
    e ← ResolverEndpoint(r.path)
    KG.adicionar(s, i, e)
    KG.instanciarRelacao(s, hasIdentity, i)
    KG.instanciarRelacao(s, targets, e)
    KG.ligarSessoesPorIdentidade(s)   // popula relatedTo
    KG.purgarFora(W)                  // janela operacional, padrão W=5min
```

### §3.4 Regras de Detecção Semântica

Todas dependem de `relatedTo`. Em prosa (versão SPARQL/SWRL a ser produzida):

- **Credential Stuffing:** múltiplas sessões com `relatedTo` (identidade reaproveitada, *fingerprint* TLS ou prefixo de IP) dentro da janela $W$, todas com `targets` apontando para um `AuthEndpoint`, com razão agregada de falha de autenticação acima de $\tau_{\text{fail}}$.
- **HTTP Flood distribuído:** conjunto de sessões com `relatedTo`, taxa agregada contra um mesmo `Endpoint` excede $\tau_{\text{rate}}$, baixa entropia de rotas por sessão (`BotBehavior`).
- **Abuso de API por múltiplas identidades:** múltiplas sessões com `hasIdentity` distintos (diferentes *tokens*) mas `relatedTo` via *fingerprint* TLS ou prefixo IP, todas atingindo a mesma `APIEndpoint`, taxa somada excede $\tau_{\text{api}}$ (mesmo que nenhuma sessão isolada exceda sua quota).

### §3.5 Cadeia de Evidência e Explicabilidade

Veredicto + cadeia explicita: regra disparada, instâncias ontológicas envolvidas, valores observados, política de mitigação. Exportável em **JSON-LD** e **STIX 2.1**, compatível com SIEM.

---

## §4 Metodologia Experimental

**Estado:** 🔄 esqueleto detalhado — falta produzir o tráfego sintético e configurar os experimentos.

### §4.1 Cenários de Avaliação por Grau de Distribuição (§ **central** da metodologia)

| Cenário | Origens distintas (K) | Caracterização | Hipótese |
|---|---|---|---|
| **A — Concentrado** | 1 | Ataque clássico *single-source* de alto volume | Baselines competitivos; ganho marginal do *cross-session* |
| **B — Moderadamente distribuído** | 10 ≤ K ≤ 100 | *Botnets* pequenas, operações com *proxies* limitados | Baselines começam a perder *recall*; arcabouço mantém via `relatedTo` |
| **C — Altamente distribuído** | K ≥ 1000 | *Credential stuffing* massivo, frota de *tokens*, *botnet* ampla | Baselines caem perto do aleatório; **arcabouço preserva detecção** |

**Money figure:** curva de *recall* vs. grau de distribuição — *baselines* descendentes, arcabouço estável.

### §4.2 Conjunto de Dados

- **Primário:** tráfego sintético parametrizado pelo *pipeline* Python que acompanha o paper. Parâmetros: número de sessões legítimas concorrentes, K, distribuição de identidades por origem, janela temporal, tipo de ataque.
- **Secundário (consistência):** subconjuntos de CICIDS2017 (Slowloris, Slow HTTP) e CIC-DDoS2019 (componentes HTTP).
- **Futuro:** tráfego real anonimizado sujeito a aprovação ética.

### §4.3 Configuração Experimental

- *Hardware*, *software*, parâmetros, divisão treino/validação/teste, calibração de limiares por cenário.
- Janela $W$ de manutenção do grafo (padrão: 5 min).
- $n \ge 30$ execuções por cenário com *seeds* diferentes para intervalos de confiança.

### §4.4 Baselines

Todos consomem o **mesmo conjunto subjacente de atributos**:

- **Perfilamento estatístico** (aproximação de Fernandes et al., 2015) — PCA sobre estatísticas agregadas de sessão.
- **Matriz de comportamento** (aproximação de Bharathi & Sukanesh, 2012) — *k*-means sobre matriz de *features* por sessão.
- **ML supervisionado** (aproximação de Kemp et al., 2023) — Random Forest e SVM sobre o mesmo vetor de *features* de sessão.

**Por que esses baselines:** todos consomem o mesmo material subjacente — a ablação isola a **representação semântica de sessão**, não a disponibilidade de atributos.

### §4.5 Métricas de Avaliação

1. **Padrão de classificação por cenário:** precisão, *recall*, F1, AUC, FPR.
2. **Recall por *campanha*** (não por sessão): fração da campanha detectada como tal — captura o ganho *cross-session* diretamente.
3. **Qualidade da explicação:** análise qualitativa de completude e acionabilidade das cadeias de evidência.

### §4.6 Análise de Ablação

| Configuração | Componente |
|---|---|
| **(a)** | ML baseline com mesmas *features* agregadas — sem ontologia |
| **(b)** | Ontologia **sem** `relatedTo` — sessões como nós isolados do grafo |
| **(c)** | Arcabouço completo — sessões ligadas por `relatedTo` via identidade, *fingerprint* TLS, prefixo IP |

- **(a) → (c):** contribuição total
- **(b) → (c):** ganho específico do raciocínio *cross-session*
- Esperamos diferença (b)→(c) pequena em A e dominante em C.

---

## §5 Resultados e Discussão

**Estado:** ⏳ pendente — depende da execução experimental.

### §5.1 Desempenho Geral por Cenário

Tabela: F1, FPR, AUC vs. três baselines, por cenário (A, B, C) × três ataques × intervalos de confiança.

### §5.2 Curva de *Recall* por Grau de Distribuição (**figura central**)

Curva descendente íngreme para baselines entre B e C; arcabouço com `relatedTo` mantém *recall* estável.

### §5.3 Análise por Tipo de Ataque Coordenado

Para cada um dos três ataques: nível mínimo de K em que os baselines começam a falhar + sinal estrutural específico (*fingerprint* TLS, prefixo IP, identidade reaproveitada) que sustenta a detecção pelo arcabouço.

### §5.4 Análise da Vantagem *Cross-Session* (§ **central**)

No Cenário C: fração de campanhas detectadas como coordenadas (não apenas sessões isoladas) — validação da hipótese central.

### §5.5 Avaliação da Qualidade da Explicação

Análise qualitativa de cadeias de evidência geradas; se viável, estudo com analistas avaliando completude e acionabilidade.

### §5.6 Significância Estatística

Testes pareados (*paired t-test*, Wilcoxon) sobre as $n$ execuções por cenário, com correção de Bonferroni para múltiplas comparações.

### §5.7 Limitações

Três limitações **declaradas explicitamente**:

1. **Vantagem regime-específica:** em Cenário A, métodos por limiar IP/sessão são competitivos. O paper **complementa** defesas volumétricas, não as substitui.
2. **Dependência de identificação de sessão/identidade:** ambientes com instrumentação parcial degradam o desempenho.
3. **Custo de manutenção do grafo, sensibilidade a $W$, generalização para outros protocolos** ficam como direções.

---

## §6 Conclusão

**Estado:** 🔄 esqueleto curto — produzir versão final ao fim da redação.

**Conteúdo previsto:**

- Síntese das contribuições: ontologia centrada em sessão, *pipeline* em tempo de execução, regras semânticas explicáveis, ablação que isola a camada semântica.
- Direções futuras:
  1. Extensão da ontologia para outros protocolos (DNS, TLS *handshake* — bridge ao paper engavetado em [`papers/cdn-crosssurface/`](papers/cdn-crosssurface/)).
  2. Integração com plataformas SOAR para resposta automatizada.
  3. Avaliação em ambientes de produção com dados reais anonimizados.
  4. Estudos com analistas de segurança para validação operacional das cadeias de evidência.

---

## Apêndices

### Apêndice A — Detalhes da Ontologia

A versão completa em **Turtle** e **RDF/XML** será disponibilizada no repositório.

### Apêndice B — Reprodutibilidade

Código-fonte, *datasets* sintéticos, *scripts* experimentais — repositório público após aceitação, licença permissiva.

---

## Checklist de produção até submissão

| Item | Estado |
|---|---|
| Resumo escrito | ✅ |
| §1 Introdução completa | ✅ |
| §2 Trabalhos Relacionados — escrita | 🔄 |
| §3 Ontologia formalizada em Turtle/RDF | ⏳ |
| §3 Regras formalizadas em SPARQL/SWRL | ⏳ |
| §3 Algoritmo de construção (pseudocódigo) | ✅ |
| §4 Gerador sintético parametrizado por K | ⏳ |
| §4 Implementação dos 3 baselines (Fernandes, Bharathi, Kemp) | ⏳ |
| §4 *Datasets* secundários (CICIDS2017, CIC-DDoS2019) preparados | ⏳ |
| §5 Execução experimental ($n \ge 30$ por cenário) | ⏳ |
| §5 Análise estatística (intervalos, testes pareados, Bonferroni) | ⏳ |
| §5 *Money figure* (curva de *recall* × K) | ⏳ |
| §6 Conclusão final | ⏳ |
| Tradução PT → EN para submissão internacional | ⏳ |
| Revisão por par interna | ⏳ |
| Carta de submissão + declaração de COI | ⏳ |

Para o **plano de ação** detalhado por fase e cronograma, ver [`MELHORIAS_QUALIS_A2A3.md`](MELHORIAS_QUALIS_A2A3.md).
