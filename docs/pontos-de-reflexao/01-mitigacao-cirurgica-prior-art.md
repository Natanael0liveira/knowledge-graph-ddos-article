# Mitigação Cirúrgica — Análise de *Prior Art*

> **Data da varredura:** 2026-05-18
> **Contexto:** validação do argumento de que a **mitigação cirúrgica via cadeia de evidência + escopo derivado do *cluster*** pode ser apresentada como contribuição central do paper [`papers/http-session`](../../papers/http-session/), ao lado da representação ontológica e do raciocínio *cross-session*.

---

## Insight que motivou a varredura

> "Sem nossa contribuição, o ataque é mitigado no limite global da configuração, sem o benefício da relação e com afetação do tráfego legítimo."

A intuição: o estado da arte **estuda detecção** mas tipicamente ignora o **dano colateral em legítimos** que a mitigação aplicada como consequência da detecção provoca. Se `relatedTo` permite identificar o discriminador do *cluster* (JA4, ASN, par JA4+endpoint), a mitigação pode ser **escopada** a esse discriminador em vez de aplicada globalmente.

Antes de promover isso à contribuição central, foi necessário verificar:

1. A métrica de "dano colateral em legítimos" já é usada em literatura acadêmica de detecção de DDoS Camada 7?
2. Existe trabalho acadêmico que formalize detecção *cross-session* via ontologia OWL (não GNN, não ML opaco)?
3. A indústria publicou metodologia de *bot management* em peer review?
4. STIX 2.1 com indicador escopado é usado em fluxo automático detecção→mitigação?

---

## *Prior art* que apareceu

### Academia revisada

| Trabalho | Onde publicou | O que faz | O que NÃO faz |
|---|---|---|---|
| **KnowGraph** (Yang et al., CCS '24) | ACM CCS 2024 | ML + raciocínio lógico de primeira ordem ponderado sobre grafos para detecção de anomalia | Domínios: fraude no eBay + intrusão de rede. Não usa OWL. Não foca em sessão HTTP. Não cobre L7 DDoS. Sem métrica de dano colateral. |
| **KLAGE — Belcastro et al. (FGCS 2026, online out/2025)** [`belcastro2025klage`] ✅ **Lido em 2026-05-30** | Future Generation Computer Systems, vol. 176 | Graph-BERT sobre logs de rede + LIME (XAI pós-hoc) + LLM (GPT-4o) para relatório. Avalia DDoS Slowloris como um dos seis ataques sobre RT-IoT2022 e CIC-IoT2023, atingindo F1 = 84,1\%. Código aberto. | (i) modela em nível de **nó de rede** (porta, IP), não de sessão HTTP; (ii) usa **embeddings aprendidos** (Graph-BERT), não OWL/SWRL simbólico; (iii) explicação via LIME pós-hoc + relatório LLM, não cadeia de evidência simbólica em JSON-LD/STIX; (iv) **não trata mitigação** (não há `mitigatedBy` nem escopo derivado); (v) não mede dano colateral em legítimos. |
| **Automated and Explainable DoS** (arxiv 2511.04114) | arxiv 2025 | TPOT + SHAP sobre *features* de pacote | Lower-layer (pacote), não L7 HTTP. XAI clássico via SHAP, não via grafo. Sem sessão semântica. |
| **Selective defenses for TDoS** (arxiv 1709.04162) | arxiv 2017 | Verificação formal de defesas seletivas em DoS telefônico | Domínio diferente (telefonia), mas conceito de "seletividade" aparece. |
| Surveys: Tripathi & Hubballi (2021), Odusami et al. (2020), Liu et al. (2022) | ACM Comput. Surv., IJCS, Electronics | Já citados no `.tex` — confirmam o gap | — |

### Indústria — produtos e *engineering blogs*

| Fonte | O que faz | Por que importa |
|---|---|---|
| **Cloudflare Bot Management (JA4 + signals)** | Detecta campanhas coordenadas via JA4 + sinais entre requisições; aplica mitigação escopada em escala global | Confirma que **mitigação cirúrgica por *fingerprint* já é prática industrial**. Sem paper acadêmico revisado. |
| **DataDome** | Auto-reporta FPR < 0.01% em CAPTCHAs servidos; mede impacto em conversão de e-commerce | Confirma que dano colateral é monetizado e medido em produto, **não em academia**. |
| **Castle.io blog** | Descreve detecção de *credential stuffing* via JA4 + correlação entre sessões | Descrição informal do que nosso paper formaliza. |
| **Akamai Bot Manager** | Agrupa sessões por *device fingerprint* + sinais comportamentais; *challenges* seletivos | Mesma prática, caixa preta. |
| **Auth0 / A10** | Descrevem 8+ detecções de *credential stuffing* incluindo análise de *token reuse* entre sessões | Mais um vendor confirmando *cross-session* como prática. |
| **AWS WAF Anti-DDoS AMR** | Suporta *scope-down statements* + *label-matched statements* | **A própria AWS desencoraja escopo seletivo "porque diminui acurácia"** — i.e., a infraestrutura existe mas falta o mecanismo confiável de derivação automática. **Gap aberto.** |
| **Imperva — Adaptive Threshold L7** | Ajusta limiar dinamicamente para reduzir FP | Reconhece o problema do FP em legítimos, mas via limiar adaptativo, não via escopo. |

### Padrões

| Padrão | Estado |
|---|---|
| **STIX 2.1** (OASIS) | Permite indicadores com *patterns*, *labels*, *granular markings*. Suporta *Course of Action* SDO. **Não documenta derivação automática de escopo a partir de regra de detecção** — esse é o nosso encaixe. |
| **OWASP Top 10 / OWASP API Security** | Cobertura conceitual de Broken Authentication, Excessive Resource Consumption — referenciar para enquadramento de ameaça. |
| **MITRE ATT&CK T1498.001** | Application Layer DoS — destino do mapeamento da nossa ontologia. |

---

## Veredicto por componente da contribuição

| Componente | *Prior art*? | Onde | Sustentação no paper |
|---|---|---|---|
| Sessão HTTP como entidade ontológica de primeira classe em OWL | ❌ Não encontrado em academia revisada | KLAGE modela nó de rede, não sessão HTTP | **Defensável como contribuição principal** |
| Construção de KG em tempo de execução para detecção | ⚠️ Vizinho próximo | KLAGE (FGCS 2026) já constrói KG a partir de logs e detecta DDoS Slowloris | Reposicionar: nossa abordagem é simbólica (OWL+SWRL); KLAGE é neural (Graph-BERT) com explicação pós-hoc (LIME) |
| Raciocínio *cross-session* via identidade/JA4/prefixo | ⚠️ Indústria + KLAGE implícito | Cloudflare, DataDome, Castle, Auth0; KLAGE captura coordenação em embeddings sem nomear | Posicionar como "primeira formalização explícita e auditável da relação `relatedTo` em ontologia OWL, em contraste com captura implícita em embeddings" |
| Regras simbólicas explícitas em SPARQL/SWRL sobre KG de tráfego (em vez de GNN/ML opaco) | ⚠️ Vizinho | KnowGraph (CCS '24, weighted FOL); KLAGE (Graph-BERT + LIME) | Diferenciar: nosso é OWL+SWRL/SPARQL nativos; KnowGraph é PGM+FOL ponderado; KLAGE é classificação neural + XAI pós-hoc |
| Cadeia de evidência via STIX 2.1/JSON-LD a partir da regra ontológica disparada | ⚠️ Padrão existe; formato textual em KLAGE | OASIS STIX 2.1; KLAGE gera texto natural via LLM | Derivação simbólica a partir do *match* da regra é nossa parte |
| **Derivação automática do escopo de `mitigatedBy` a partir do discriminador do *cluster*** | ❌ Não encontrado em academia | AWS *scope-down statements* existe mas desencorajado por falta de mecanismo confiável; KLAGE não trata mitigação | **Defensável como contribuição** |
| **Métrica acadêmica de dano colateral em legítimos para L7 DDoS** | ❌ Não encontrado sistematicamente | *Vendors* auto-reportam (DataDome FPR < 0,01\%); KLAGE reporta apenas Acc/Prec/Rec/F1 | **Defensável como contribuição metodológica** |

---

## Síntese atualizada após leitura completa de KLAGE (2026-05-30)

A leitura integral de KLAGE [`belcastro2025klage`] mudou o que pode ser declarado como contribuição inédita. KLAGE constrói grafos de conhecimento a partir de logs de rede, classifica nós via Graph-BERT, explica via LIME e gera relatórios via LLM. Cobre seis ataques sobre os *datasets* RT-IoT2022 e CIC-IoT2023, **incluindo DDoS Slowloris**, com F1 = 84,1\%. Disponibiliza código aberto. **Não podemos mais afirmar "primeiro arcabouço acadêmico aberto que aplica KG à detecção".**

A contribuição genuína passa a ser tridimensional, diferenciada explicitamente de KLAGE em três eixos:

1. **Unidade de raciocínio.** KLAGE modela grafo de tráfego em nível de **nó de rede** (porta, IP). Nossa proposta modela a **sessão HTTP** como entidade ontológica de primeira classe, com identidade composta (cookie, *token*, *username*, JA4) e relações tipadas. KLAGE não tem `ApplicationSession`, não tem `hasIdentity`, não modela JA4 como assinatura do cliente.

2. **Representação semântica.** KLAGE usa **Graph-BERT** (embeddings aprendidos) e **LIME** (explicação pós-hoc do classificador). Nossa proposta é **simbólica nativa**: a regra `CoordinatedHTTPFlood` é uma fórmula em SPARQL/SWRL avaliada por um *reasoner* OWL. A cadeia de evidência é a derivação simbólica, não a saída de um classificador interpretado depois.

3. **Mitigação com escopo derivado.** KLAGE termina no relatório. **Não trata mitigação.** Nossa proposta acopla detecção, cadeia de evidência e derivação automática de escopo de `mitigatedBy` ao discriminador do *cluster*.

E uma quarta dimensão, metodológica: KLAGE reporta Acc/Prec/Rec/F1. Não mede dano colateral em legítimos. Essa métrica permanece como contribuição metodológica.

**Contribuições remanescentes que precisam de *framing* cuidadoso** (existem em indústria, ausentes em academia revisada):

5. Raciocínio *cross-session* por JA4/identidade/prefixo. Declarar como "primeira formalização acadêmica auditável e reprodutível do que produtos comerciais fazem em caixa preta e que KLAGE captura apenas implicitamente nos embeddings".
6. Cadeia de evidência exportável em STIX 2.1/JSON-LD a partir da regra ontológica disparada.

---

## Reformulação proposta do *abstract* (substitui qualquer claim de "primeiro arcabouço")

> Campanhas coordenadas de DDoS de Camada 7 sobre HTTP, em particular a família Slow HTTP DDoS distribuído, sustentam taxas baixas por sessão e passam por defesas baseadas em assinatura, limiares e quotas por IP, sessão ou *token*. Trabalhos recentes mostram que grafos de conhecimento podem aprimorar a detecção e a explicabilidade, mas o estado atual da literatura combina KG com classificadores neurais e explicação pós-hoc, sem modelar a sessão HTTP como entidade ontológica raciocinável nem acoplar o veredito a uma política de mitigação derivada. Este artigo propõe um arcabouço que modela a sessão HTTP como objeto semântico de primeira classe em OWL, com relações tipadas para identidade do cliente, *endpoint* alvo, sinais comportamentais e mitigação aplicável. Regras simbólicas em SPARQL/SWRL operam sobre *clusters* de sessões correlacionadas pelo *fingerprint* TLS, pela identidade compartilhada ou pelo prefixo de IP, produzindo veredictos com cadeias de evidência que percorrem o grafo. O discriminador do *cluster* detectado é usado para derivar automaticamente o escopo da mitigação. A avaliação isola, sob a mesma base de atributos de tráfego, o ganho do raciocínio em nível de sessão frente a detectores que consomem *features* agregadas, e introduz uma métrica de fração de tráfego legítimo afetada pela mitigação resultante — métrica que produtos comerciais auto-reportam sem benchmark acadêmico público e que não é usada sistematicamente na literatura de detecção de Camada 7. A implementação é disponibilizada como código aberto.

---

## Riscos a observar no peer review

| Risco | Mitigação |
|---|---|
| Revisor cita KLAGE como prior art próximo | Reconhecer explicitamente em §2.1. Diferenciar nos três eixos: unidade de raciocínio (sessão vs. nó de rede), representação (simbólica vs. embeddings), e mitigação acoplada (presente vs. ausente) |
| Revisor da Cloudflare/Akamai aponta que mitigação por JA4 já existe em produto | Reconhecer explicitamente. Diferenciar pela reprodutibilidade acadêmica, abertura do código/ontologia, e formalização auditável da derivação do escopo |
| Revisor pede comparação numérica com KLAGE em DDoS Slowloris | Usar RT-IoT2022 ou CIC-IoT2023 (mesmos *datasets* de KLAGE) como secundários no Cenário A; reportar F1 lado a lado, e dano colateral em legítimos (que KLAGE não reporta) |
| Revisor pede "compare com KnowGraph" | Citar e diferenciar: OWL+SWRL vs. PGM+FOL ponderado; L7 HTTP vs. fraude/intrusão; sessão como entidade vs. grafo genérico |
| Revisor pede comparação com GNN puro | Citar como direção complementar — GNN aprende *embeddings* opacos; nosso arcabouço produz cadeia de evidência simbólica. Lo et al. (2022) como representante |
| Revisor pergunta "como o escopo é realmente derivado?" | Detalhar em §3.5: o discriminador do *cluster* é o conjunto mínimo de propriedades compartilhadas que define o conjunto `relatedTo` que satisfez a regra disparada |
| Revisor pede dataset real para a métrica de dano colateral | Reconhecer como limitação; propor avaliação com tráfego sintético parametrizado por mistura legítimo/ataque com proporção controlada |

---

## Próximos passos antes da submissão

1. ✅ Adicionar KLAGE [`belcastro2025klage`] a [`../../shared/references.bib`](../../shared/references.bib) — concluído 2026-05-30.
2. **Atualizar §2.1 do `.tex`** desenvolvendo a subseção em prosa real, com KLAGE como referência central de KG aplicado à detecção em runtime, diferenciado nos três eixos acima.
3. **Reescrever Abstract e §1.4 Contribuições** com a versão reformulada acima — substituir "primeiro arcabouço" pela diferenciação tridimensional honesta.
4. **Considerar incluir RT-IoT2022 ou CIC-IoT2023 como dataset secundário** em §4.2, especificamente para comparação direta com KLAGE em DDoS Slowloris.
5. **Adicionar §3.5 — Derivação Automática de Escopo de Mitigação** (atual §3.5 sobre cadeia de evidência; expandir para cobrir o algoritmo de derivação do discriminador do *cluster*).
6. **Adicionar §4.5 — Métrica de Dano Colateral em Legítimos** (extensão da subseção de métricas).
