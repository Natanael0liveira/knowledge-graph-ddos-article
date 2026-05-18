# Leituras e Links — Validação de *Prior Art*

> **Última atualização:** 2026-05-18
> **Contexto:** [`01-mitigacao-cirurgica-prior-art.md`](01-mitigacao-cirurgica-prior-art.md).

Catálogo plano de links a acessar, organizado por **prioridade**.
Cada entrada: link, prioridade, **por que ler** e **o que verificar**.

Marcar como ✅ quando lido; produzir resumo em [`docs/leituras-pt/`](../leituras-pt/) e atualizar a entrada aqui.

---

## 🔴 CRÍTICO — ler antes de fechar §1 e §2 do paper

### 1. KnowGraph: Knowledge-Enabled Anomaly Detection via Logical Reasoning on Graph Data

- **Link arxiv:** https://arxiv.org/abs/2410.08390
- **Link HTML:** https://arxiv.org/html/2410.08390v1
- **PDF direto:** https://arxiv.org/pdf/2410.08390
- **alphaXiv:** https://www.alphaxiv.org/abs/2410.08390
- **DBLP:** https://dblp.org/rec/journals/corr/abs-2410-08390.html
- **ResearchGate:** https://www.researchgate.net/publication/384886296_KnowGraph_Knowledge-Enabled_Anomaly_Detection_via_Logical_Reasoning_on_Graph_Data
- **Venue:** ACM CCS 2024 (top-tier de segurança — Qualis A1)

**Por que ler:** trabalho acadêmico mais próximo em filosofia — raciocínio lógico explícito sobre grafo para detecção de anomalia. Embora não cubra L7 DDoS, é o vizinho mais próximo que aparecerá no peer review se não citarmos.

**O que verificar:**
- A formalização do raciocínio é em weighted first-order logic (PGM) ou em OWL/DL?
- A unidade semântica é nó genérico, transação, ou entidade tipada com relações específicas?
- Como geram explicação? É cadeia de evidência ou *attribution score*?
- Avaliam por *false positive rate* em legítimos ou só por precision/recall?
- Eles abrem código? Ontologia?

**Como diferenciar nosso paper:** domínio (L7 HTTP DDoS vs. fraude/intrusão), formalismo (OWL+SPARQL/SWRL vs. PGM+FOL), unidade semântica (sessão como entidade ontológica de primeira classe vs. grafo genérico), saída (escopo de mitigação derivado automaticamente vs. score).

---

### 2. Enhancing network security using knowledge graphs and large language models for explainable threat detection (Wang et al., 2025)

- **Link:** https://www.sciencedirect.com/science/article/pii/S0167739X25004546
- **Venue:** *Future Generation Computer Systems* (Elsevier, Qualis A1, IF ~7)

**Por que ler:** publicação recente, em journal forte, combinando KG + LLM para *explainable threat detection*. **Esta é a leitura de risco mais alta** — pode ser prior art próximo demais.

**O que verificar (CRÍTICO):**
- Modela sessão HTTP como entidade ontológica? Ou trabalha em nível de log genérico de rede?
- Cobre L7 DDoS coordenado especificamente, ou é IDS genérico?
- Como representa identidade compartilhada / *fingerprint*? Como relação tipada ou como atributo?
- A "explicabilidade" deles é cadeia de evidência sobre o grafo ou *summary* gerado por LLM?
- Avaliam dano colateral em legítimos?

**Possível resultado A — modelam sessão como entidade:** prior art muito próximo, precisamos reposicionar nosso paper como complementar (diferenciar pela ablação *cross-session* e pelo escopo automático de mitigação).

**Possível resultado B — trabalham em nível de log/IP genérico:** vizinho confortável, citamos em §2.1 como abordagem KG+LLM e diferenciamos pelo nível semântico.

**Importante:** primeiro acesso retornou 403 (paywall). Tentar via:
- VPN institucional UFRGS
- Sci-Hub se permitido na sua política
- Solicitar PDF aos autores via ResearchGate
- Periódico via biblioteca CAPES

---

## 🟡 IMPORTANTE — ler antes da submissão final

### 3. Automated and Explainable Denial of Service Analysis for AI-Driven Intrusion Detection Systems

- **Link arxiv:** https://arxiv.org/abs/2511.04114
- **PDF:** https://arxiv.org/pdf/2511.04114
- **Venue:** arxiv 2025

**Por que ler:** competidor direto na "explainable DDoS" — usa TPOT + SHAP. É XAI clássico aplicado a DDoS. Precisa ser citado em §2.2 ou §2.3 como representante da família "ML + post-hoc XAI" e diferenciado da nossa abordagem (representação semântica desde o início, não pós-explicação de ML opaco).

**O que verificar:** cobre L7 ou só lower-layer? Avalia em CICIDS2017/CIC-DDoS2019?

---

### 4. Cloudflare — JA4 fingerprints and inter-request signals

- **Link blog:** https://blog.cloudflare.com/ja4-signals/
- **Docs JA3/JA4:** https://developers.cloudflare.com/bots/additional-configurations/ja3-ja4-fingerprint/
- **Docs cf.bot_management.ja4:** https://developers.cloudflare.com/ruleset-engine/rules-language/fields/reference/cf.bot_management.ja4/
- **Docs variables:** https://developers.cloudflare.com/bots/reference/bot-management-variables/
- **Signals Intelligence:** https://developers.cloudflare.com/bots/additional-configurations/ja3-ja4-fingerprint/signals-intelligence/

**Por que ler:** referência industrial canônica para mitigação cirúrgica por JA4. Reconhecer e citar é honestidade intelectual — diferencia nosso paper como **formalização acadêmica reprodutível** do que Cloudflare faz em produto fechado.

**O que verificar:** como descrevem o agrupamento de sessões por JA4? Como derivam o escopo de mitigação? Há paper técnico/whitepaper além do blog?

---

### 5. AWS WAF — Anti-DDoS Managed Rule Group e *scope-down statements*

- **Introdução geral:** https://aws.amazon.com/blogs/networking-and-content-delivery/introducing-the-aws-waf-application-layer-ddos-protection/
- **Automating L7 mitigation com Shield Advanced:** https://docs.aws.amazon.com/waf/latest/developerguide/ddos-automatic-app-layer-response.html
- **AMR Best Practices:** https://docs.aws.amazon.com/waf/latest/developerguide/waf-managed-protections-best-practices.html
- **Mitigate DDoS attacks (re:Post):** https://repost.aws/knowledge-center/waf-mitigate-ddos-attacks
- **Customize L7 DDoS response:** https://aws.amazon.com/blogs/security/how-to-customize-your-response-to-layer-7-ddos-attacks-using-aws-waf-anti-ddos-amr/
- **DDoS prevention rule group:** https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-anti-ddos.html
- **Enable automatic mitigation:** https://docs.aws.amazon.com/waf/latest/developerguide/ddos-automatic-app-layer-response-config.html

**Por que ler:** **A AWS desencoraja explicitamente o uso de *scope-down statements* para DDoS "porque diminui acurácia".** Isso é argumento forte: a infraestrutura para mitigação escopada existe, mas falta o mecanismo confiável de derivação automática — **exatamente o gap que nosso arcabouço preenche**.

**O que verificar:** documentar a frase exata da AWS sobre "scope-down decreases efficacy" para citar literalmente no paper como motivação.

---

### 6. DataDome — False Positive Rate e impacto em conversão

- **9 Questions for Bot Management on FPR:** https://datadome.co/learning-center/bot-solution-provider-false-positives/
- **How FPR Impact Conversion Rates:** https://datadome.co/bot-management-protection/how-false-positive-rates-impact-e-commerce-conversion-rates/
- **DataDome CAPTCHA:** https://datadome.co/products/datadome-captcha/
- **Why CAPTCHA Not Enough:** https://datadome.co/guides/captcha/traditional-captcha-obsolete/

**Por que ler:** **DataDome auto-reporta FPR < 0.01% em CAPTCHAs servidos** — métrica de produto, não acadêmica. Isso é evidência de que "dano colateral em legítimos" é medido em indústria sem benchmark acadêmico público — gap que nossa métrica preenche.

**O que verificar:** como DataDome mede FPR? Há metodologia transparente? Algum *whitepaper* técnico?

---

### 7. Castle.io — Anatomia, detecção e defesa de Credential Stuffing

- **Link:** https://blog.castle.io/credential-stuffing-attacks-anatomy-detection-and-defense/

**Por que ler:** descreve em linguagem informal o que nosso paper formaliza: *credential stuffing* detectado via JA4 + correlação entre sessões. Boa fonte para reescrever §1.1 com framing operacional.

**O que verificar:** mencionam métricas? Há paper técnico associado?

---

## 🟢 RECOMENDADO — ler durante a escrita

### 8. Filigran — STIX 2.1 Indicator Patterning and Detection Development

- **Link:** https://filigran.io/blog/stix-2-1-indicator-patterning-and-detection-development/

**Por que ler:** detalha como produzir indicadores STIX 2.1 com *patterns*. Útil para detalhar §3.5 (exportação da cadeia de evidência).

---

### 9. OASIS — STIX 2.1 especificação oficial

- **OS (Official Standard):** https://docs.oasis-open.org/cti/stix/v2.1/os/stix-v2.1-os.html
- **CS01 (Committee Specification):** https://docs.oasis-open.org/cti/stix/v2.1/cs01/stix-v2.1-cs01.html
- **CSPRD01:** https://docs.oasis-open.org/cti/stix/v2.1/csprd01/stix-v2.1-csprd01.html

**Por que ler:** especificação canônica. Verificar exatamente como mapear cadeia de evidência → `Indicator` + `Observed-Data` + `Relationship` + `Course-of-Action`.

---

### 10. Imperva — Adaptive Threshold para L7 DDoS

- **Link:** https://www.imperva.com/blog/imperva-adaptive-threshold-for-layer-7-ddos-attacks-reduces-risk-of-business-disruption/

**Por que ler:** abordagem alternativa para o mesmo problema (FP em legítimos) — limiar adaptativo em vez de escopo cirúrgico. Útil para §2.2 como contraste.

---

### 11. Akamai — Modern Layer 7 DDoS Protections (2024)

- **Link:** https://www.akamai.com/blog/security/why-modern-layer-7-ddos-protections-crucial-web-security-2024

**Por que ler:** outro panorama industrial. Útil como referência geral para §1.1.

---

### 12. On the Accuracy of Formal Verification of Selective Defenses for TDoS Attacks

- **Link arxiv:** https://arxiv.org/pdf/1709.04162

**Por que ler:** trabalho acadêmico que usa o termo "selective defenses" — embora em domínio diferente (TDoS, telefonia), legitima o vocabulário acadêmico de "seletividade" e pode ser citado para sustentar o framing.

---

### 13. ScrapFly — JA3/JA4 TLS Fingerprint (técnico)

- **Link:** https://scrapfly.io/web-scraping-tools/ja3-fingerprint?algo=ja4

**Por que ler:** referência prática para JA4. Útil para Apêndice/Implementação.

---

### 14. When Handshakes Tell the Truth: Detecting Web Bad Bots via TLS Fingerprints

- **Link arxiv (verificar):** https://arxiv.org/pdf/2602.09606
- **Nota:** o número arxiv parece anômalo (2602 = fevereiro 2026); pode ser pre-print recente. **Verificar disponibilidade real e citação correta antes de incluir no `.bib`.**

**Por que ler:** se confirmado, é trabalho acadêmico próximo sobre detecção de bots via TLS fingerprinting — pode reforçar nossa fundamentação.

---

## Acesso aos PDFs

Verificar [`docs/pdfs/`](../pdfs/) — alguns destes PDFs talvez já estejam baixados. Quando obter PDF de qualquer um dos itens **CRÍTICO** ou **IMPORTANTE**, mover para `docs/pdfs/` e produzir resumo em [`docs/leituras-pt/`](../leituras-pt/) seguindo o formato dos resumos existentes.

---

## Checklist de leitura (para preencher conforme leituras forem completadas)

- [ ] **🔴 1.** KnowGraph (CCS '24) — arxiv 2410.08390
- [ ] **🔴 2.** Wang et al. KGs+LLM (FGCS 2025) — S0167739X25004546
- [ ] **🟡 3.** Automated Explainable DoS (arxiv 2511.04114)
- [ ] **🟡 4.** Cloudflare JA4 + Bot Management (blog + docs)
- [ ] **🟡 5.** AWS WAF Anti-DDoS AMR (docs + blog)
- [ ] **🟡 6.** DataDome — FPR e conversão
- [ ] **🟡 7.** Castle.io — Credential Stuffing
- [ ] **🟢 8.** Filigran — STIX 2.1 Indicators
- [ ] **🟢 9.** OASIS STIX 2.1 spec
- [ ] **🟢 10.** Imperva — Adaptive Threshold
- [ ] **🟢 11.** Akamai L7 DDoS 2024
- [ ] **🟢 12.** Selective defenses TDoS (arxiv 1709.04162)
- [ ] **🟢 13.** ScrapFly JA3/JA4
- [ ] **🟢 14.** When Handshakes Tell the Truth (verificar arxiv ID)
