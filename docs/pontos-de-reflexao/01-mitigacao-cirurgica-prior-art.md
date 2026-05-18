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
| **KGs + LLM para *explainable threat detection*** (ScienceDirect, 2025) | Future Generation Computer Systems | Graph-BERT sobre logs de rede + KG enriquecido + LLM para relatório explicável | Foco em comunicação geral, não em sessão como entidade de primeira classe. *Full text* não acessado nesta varredura (paywall) — verificar. |
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
| Sessão HTTP como entidade ontológica de primeira classe em OWL, para detecção em tempo de execução | ❌ Não encontrado | — | **Defensável como contribuição principal** |
| Raciocínio *cross-session* via identidade/JA4/prefixo | ⚠️ Indústria | Cloudflare, DataDome, Castle, Auth0 | Reposicionar como "primeira formalização acadêmica auditável e reprodutível do que produtos comerciais fazem em caixa preta" |
| Regras simbólicas explícitas em SPARQL/SWRL sobre KG de tráfego (em vez de GNN/ML opaco) | ⚠️ Vizinho | KnowGraph (CCS '24) com weighted FOL, mas não em L7 DDoS | Diferenciar: nosso é OWL+SWRL/SPARQL, dele é PGM+FOL ponderado; nosso é L7 HTTP, dele é fraude/intrusão |
| Cadeia de evidência via STIX 2.1 gerada automaticamente a partir da regra disparada | ⚠️ Padrão existe | OASIS STIX 2.1 | Derivação automática a partir do *match* da regra ontológica é nossa parte |
| **Derivação automática do escopo de `mitigatedBy` a partir do discriminador do *cluster*** | ❌ Não encontrado explicitamente | AWS *scope-down statements* existe mas desencorajado por falta de mecanismo confiável | **Defensável como contribuição** |
| **Métrica acadêmica de dano colateral em legítimos para L7 DDoS** | ❌ Não encontrado sistematicamente | Vendors auto-reportam | **Defensável como contribuição metodológica** |

---

## Síntese

**Três componentes genuinamente novos em literatura acadêmica revisada de L7 DDoS HTTP:**

1. Modelagem ontológica da sessão HTTP como entidade de primeira classe em OWL para detecção em tempo de execução.
2. Derivação automática do escopo de mitigação a partir do discriminador do *cluster* detectado.
3. Métrica de dano colateral em tráfego legítimo como critério de avaliação experimental.

**Dois componentes que precisam de framing cuidadoso** (existem em indústria, sem academia revisada):

4. Raciocínio *cross-session* por JA4/identidade/prefixo — não declarar como invenção; declarar como "primeira formalização acadêmica reprodutível".
5. Cadeia de evidência exportável em STIX 2.1 — o formato existe; a derivação automática a partir de regra ontológica é nossa parte.

---

## Reformulação proposta do *abstract* (substitui o claim de "mitigação cirúrgica genial")

> Apresentamos o primeiro arcabouço acadêmico aberto que modela a sessão HTTP como entidade ontológica de primeira classe em OWL para detecção em tempo de execução de campanhas coordenadas de Camada 7. Sobre essa representação, regras simbólicas operam sobre *clusters* de sessões ligadas pela relação `relatedTo` (identidade compartilhada, *fingerprint* TLS, prefixo de IP) e produzem três saídas acopladas: o veredicto, uma cadeia de evidência auditável exportável em STIX 2.1, e um escopo de mitigação derivado automaticamente do discriminador do *cluster*. O arcabouço é avaliado por precisão, *recall*, F1 e por uma métrica adicional de **fração de tráfego legítimo afetada pela mitigação resultante** — métrica que produtos comerciais de *bot management* auto-reportam sem benchmark acadêmico público e que, até onde verificamos, não é usada sistematicamente na literatura de detecção de DDoS de Camada 7.

---

## Riscos a observar no peer review

| Risco | Mitigação |
|---|---|
| Revisor da Cloudflare/Akamai aponta que "isso já existe em produto" | Reconhecer explicitamente em §2 e diferenciar pela **reprodutibilidade acadêmica, abertura do código/ontologia, e formalização auditável** |
| Revisor pede "compare com KnowGraph" | Citar e diferenciar: OWL+SWRL vs. PGM+FOL ponderado; L7 HTTP vs. fraude/intrusão; sessão como entidade ontológica de primeira classe vs. grafo genérico |
| Revisor pede comparação direta com GNN para detecção de campanha | Discutir como direção complementar — GNN aprende *embeddings* opacos; nosso arcabouço produz cadeia de evidência simbólica. Citar Lo et al. (2022) como representante |
| Revisor pergunta "como o escopo é realmente derivado?" | Detalhar em §3.5: o discriminador do *cluster* é o conjunto mínimo de propriedades compartilhadas que define o conjunto `relatedTo` que satisfez a regra disparada. Algoritmo formal pode entrar no Apêndice |
| Revisor pede dataset real para a métrica de dano colateral | Reconhecer como limitação; propor avaliação com tráfego sintético parametrizado por mistura legítimo/ataque, com proporção controlada |

---

## Próximos passos antes da submissão

1. **Ler em profundidade os dois papers vizinhos** marcados como **CRÍTICO** em [`02-leituras-e-links.md`](02-leituras-e-links.md).
2. **Atualizar §2.1 do `.tex`** com KnowGraph e KGs+LLM 2025 como vizinhos diferenciados.
3. **Atualizar `abstract` do `.tex`** com a versão reformulada acima.
4. **Adicionar §3.5 — Derivação Automática de Escopo de Mitigação** (já existe §3.5 sobre cadeia de evidência; expandir para cobrir escopo).
5. **Adicionar §4.5 — Métrica de Dano Colateral em Legítimos** (extensão da subseção de métricas).
6. **Atualizar [`shared/references.bib`](../../shared/references.bib)** com entradas BibTeX dos itens marcados como **CRÍTICO** e **IMPORTANTE** em [`02-leituras-e-links.md`](02-leituras-e-links.md).
