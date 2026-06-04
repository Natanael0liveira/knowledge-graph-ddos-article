# KLAGE — Grafos de Conhecimento + LLMs para Detecção Explicável de Ameaças

> **Nota de leitura analítica** de *"Enhancing network security using knowledge graphs and large language models for explainable threat detection"*, Belcastro, Carlucci, Cosentino, Liò e Marozzo (2026), *Future Generation Computer Systems* 176:108160.
>
> **PDF original:** [`docs/pdfs/main.pdf`](../pdfs/main.pdf) — 15 páginas
> **DOI:** 10.1016/j.future.2025.108160 · **Código:** github.com/SCAlabUnical/KLAGE
> **Status:** ✅ Lido na íntegra (nota analítica, não tradução integral)
> **Tier:** 1 — **trabalho relacionado mais próximo** do nosso (KG + DDoS + explicabilidade). Citado como `belcastro2025klage`.

---

## 1. O que é o KLAGE

Metodologia que combina **Grafos de Conhecimento (KG) + Graph-BERT + XAI (LIME) + LLMs (GPT-4o)** para detecção de ameaças de rede *e* geração automática de relatórios legíveis. Pipeline de **4 estágios** (Fig. 1 do paper):

1. **Logs → fluxos → KG unificado.** *Logs* (Wireshark/tcpdump → PCAP) são agregados em **fluxos** (NetFlow/CICFlowMeter/sFlow, agrupados pela 5-tupla). Cada fluxo vira um KG; os KGs individuais são fundidos num **KG unificado**. Cada **nó = uma porta**; arestas `E_caused` (ataque→origem) e `E_connected` (origem→destino). Um nó-observador `N_attack` monitora cada tipo de ataque.
2. **Classificação por Graph-BERT + explicação LIME.** Graph-BERT classifica **nós** usando *Hop-based* e *Intimacy-based positional embeddings*, códigos estruturais de Weisfeiler-Lehman e **subgraph sampling** (k vizinhos via PageRank). Camadas *graph-transformer* com atenção + residual; *fine-tuning* com *cross-entropy*. Explicação **pós-hoc via LIME** (perturbação local).
3. **Poda do grafo** por *significance score* `S(n)=α·centralidade+β·similaridade+γ·intensidade de interação`, limiar `θ=μ_S+λσ_S`.
4. **Relatório por LLM.** O grafo podado + explicações LIME (JSON) viram *prompt* para o GPT-4o gerar relatório textual.

## 2. Avaliação e resultados

- **Datasets:** RT-IoT2022 (IoT industrial) + CIC-IoT2023 (IoT doméstico). Features NetFlow (portas, protocolo, duração, pacotes enviados/recebidos). **6 ataques:** ARP Poisoning, **DDoS Slowloris**, DoS SYN Flood, OS Detection, TCP Port Scan, Brute Force.
- **Detecção (Tabela 3):** KLAGE **acurácia 84,1%, precisão 83,5%, recall 84,7%, F1 84,1%** — supera 4 baselines GNN/BERT (Boyaci GNN 79%, Zou 78,6%, Hong GraphSAGE 79%, Ali BERT+MLP 79%) por >5%.
- **Custo:** Xeon 96-core + GPU A30 24GB; ~1h/100 épocas; 39s/lote (256), >2600 amostras/s, ~10GB GPU.
- **Relatórios:** ablação GPT-base/int/adv; LLM-as-judge (ChatGPT o1); avaliação por **10 especialistas** (GPT-adv preferido em ~60%). O relatório avançado domina em informatividade, consistência, compreensão e explicabilidade.

## 3. Como o KLAGE trata o DDoS Slowloris

O relatório GPT-adv para Slowloris descreve corretamente: alvo **porta 80/TCP**, **4–8 pacotes fwd, 3–13 bwd**, payload fwd 26–47 bytes, 0 bwd, conexões persistindo **>30s**, **<1 pacote/s** para evadir sistemas baseados em taxa, e — importante — reconhece **"campanha de movimento lateral coordenado envolvendo múltiplos hosts comprometidos"** e **"estratégia distribuída com hosts de origem distintos operando em uníssono"**. Ou seja: o KLAGE **reconhece qualitativamente** a natureza distribuída/coordenada — mas a **detecção** continua sendo classificação **por nó**, e a coordenação fica **latente nos embeddings**, sem relação simbólica nomeada. (O GPT-base *zero-shot* "tem dificuldade de identificar com confiança ataques furtivos/de baixa visibilidade" — mas isso é sobre a qualidade do *relatório*, não da detecção.)

## 4. Limitações declaradas pelos próprios autores (§5)

- KLAGE detecta ameaças **com padrões claros** (DDoS, ARP poisoning, varredura). **APTs e malware polimórfico** são **"além do escopo arquitetural atual"** — exigiriam análise longitudinal, telemetria de host e inspeção de memória.
- Detecção de **zero-day / gatilhos comportamentais inesperados** escapa por novidade/ausência de assinatura → futuro: **treinamento adversarial + injeção sintética de padrões anômalos**.
- **LIME é local e aproximado** ("pode não capturar o comportamento global do modelo") — explicação pós-hoc, não a decisão real.
- LLMs podem **alucinar / produzir fatos inexistentes** → futuro: estimativa de confiança.
- Futuro: **grafos de conhecimento temporais**, telemetria de host, aprendizado contínuo, Kafka/Flink para tempo real, edge.

## 5. Posicionamento vs. NOSSO trabalho (honesto)

| eixo | KLAGE | Nosso arcabouço |
|---|---|---|
| **Unidade de raciocínio** | **nó de rede (porta)** / fluxo | **sessão de aplicação** (identidade, JA4, comportamento) |
| **Como captura coordenação** | latente em *embeddings* Graph-BERT | **sub-relações `relatedBy_*` nomeadas e ponderadas** explícitas |
| **Explicação** | **pós-hoc (LIME)** aproximada + relatório LLM (pode alucinar) | **veredito = derivação simbólica** (a regra SPARQL/SWRL que disparou *é* a explicação; exata, auditável, consultável) |
| **Mitigação** | **nenhuma** (só relatórios para o analista) | **escopo cirúrgico derivado** do grafo + métrica de **dano colateral** |
| **Regime de ataque** | padrões "claros"; **furtivo/adaptativo (APT) fora do escopo** (declarado) | foco no **regime furtivo-distribuído** (sessões calibradas para parecer benignas) |

**O que genuinamente nos favorece:** (i) explicação **simbólica intrínseca** vs. LIME pós-hoc aproximada que os próprios autores admitem não capturar o comportamento global; (ii) **derivação de mitigação + dano colateral**, ausentes no KLAGE; (iii) a **sessão** é unidade mais natural que a **porta** para coordenação em Camada 7 (carrega identidade/JA4/comportamento).

**O que é honesto reconhecer a favor do KLAGE:** resolve um problema **mais amplo** (6 ataques, pipeline completo de relatório, validação com especialistas e LLM-as-judge); é um sistema maduro e publicado em A1. Nós somos **mais estreitos** (sessões HTTP, família Slowloris) porém **mais profundos** no eixo simbólico/mitigação.

**Sobre a comparação numérica (nosso §5.4):** no Slowloris real do CIC-IoT2023, nosso (d) F1=0,911 e até o **ML por-sessão forte** (0,900) superam o KLAGE (0,841) — **mas a comparação NÃO é controlada**: granularidade nó-vs-sessão, protocolos e *splits* distintos. A leitura defensável é **paridade de ordem de grandeza** + o diferencial qualitativo (veredito auditável, mitigação cirúrgica), **não** superioridade de detecção. Ademais, como o per-session forte já bate o KLAGE, **a dianteira não é atribuível ao raciocínio entre sessões** — exatamente como reportamos.

**Nuance importante sobre "furtivo":** o KLAGE trata o Slowloris como ataque de **padrão claro** que ele *detecta* (e nos dados convencionais ele e o ML por-sessão detectam mesmo). O "furtivo" que o KLAGE adia explicitamente é **APT/polimórfico**. Nosso "regime furtivo" é uma **construção** (Slowloris distribuído calibrado para mimetizar o benigno por sessão) — um ponto no espectro que nenhum dos dois valida em captura real. Honestidade preservada: nosso regime é o **caso idealizado** onde a coordenação entre sessões é a única pista.
