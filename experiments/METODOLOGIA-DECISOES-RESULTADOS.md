# Metodologia, Decisões e Resultados — Experimentos (Fase B)

Documento-mestre que descreve **cada etapa** dos experimentos em quatro ângulos:
**(1) por que decidimos fazer assim**, **(2) o que os cálculos representam**,
**(3) os resultados**, **(4) o resultado prático esperado**. É o alicerce conceitual
para a consolidação do paper.

> **A tese, em uma frase.** Campanhas coordenadas de DDoS de Camada 7 (Slow HTTP DoS
> distribuído) ficam *sub-limiares em cada sessão isolada* — o sinal de ataque mora na
> **estrutura entre sessões** (mesmo *fingerprint* TLS, identidade reaproveitada,
> convergência de endpoint). Modelamos isso como objeto raciocinável numa ontologia e
> mostramos que a detecção **por sessão falha onde a *cross-session* acerta**.

> **Como ler as métricas (glossário rápido).**
> - **ROC AUC** — probabilidade de o detector dar nota maior a um ataque que a um
>   benigno. **0,5 = chute; 1,0 = perfeito.** Independe do limiar de corte.
> - **F1** — média harmônica de precisão (dos que acusei, quantos eram ataque) e
>   *recall* (dos ataques reais, quantos peguei). Só é alta se as DUAS forem boas.
> - **Ω(S)** — "score de coordenação" de um conjunto S de sessões: soma ponderada dos
>   pares ligados por cada sub-relação (definido no Sprint 1 / Pilar 2).
> - **IC 95%** — faixa onde a média real cai 95% das vezes (incerteza).
> - **p / Bonferroni** — chance de o resultado ser sorte (Bonferroni = versão rígida).
> - **Cohen's d** — tamanho do efeito em desvios-padrão (>0,8 já é "grande").
> - **KS D** — distância entre duas distribuições (0 = idênticas).

---

## Sprint 1 — Pipeline de Extração e Grafo de Conhecimento

**Por que decidimos assim.** A tese exige raciocinar sobre *sessões* e suas relações,
não sobre pacotes ou fluxos. Então a primeira decisão foi **elevar o tráfego bruto
(PCAP) a um grafo RDF onde a sessão HTTP é entidade de primeira classe**. Escolhas e
seus porquês:
- **JA4 (via tshark)** como identidade do cliente: é o *fingerprint* do *handshake*
  TLS — o sinal de coordenação **mais caro de falsificar** para o atacante (peso alto).
- **Fluxos (CICFlowMeter) → sessões**: agrega pacotes em unidades de comportamento.
- **Fuseki/TDB2 (triplestore RDF)**: permite regras simbólicas em SPARQL/SWRL sobre o
  grafo — sem isso não há "veredicto como derivação".
- **Decisão de infraestrutura crítica:** o banco TDB2 foi movido para **SSD interno**
  e carregado com **`tdb2.tdbloader` nativo (ARM)**, porque em disco exFAT + JVM
  emulada a carga travava (~5 h e falhava); na nova forma são ~2 min. Decisão de
  engenharia, mas que viabilizou todo o resto.
- **Dois *datasets* reais, por quê:** **CIC-IoT2023** (tem rótulos oficiais e é o
  *mesmo* dataset do KLAGE → comparação direta) e **CICIDS2017** (família Slow HTTP
  completa: Slowloris, Slowhttptest, Hulk, GoldenEye → testa generalização entre
  variantes do ataque). Um dá comparabilidade com o estado-da-arte; o outro, amplitude.
- **Rotulagem do CICIDS2017, por quê assim:** o PCAP de quarta-feira não traz rótulos.
  Rotular **só por janela temporal** marcaria como ataque também o tráfego legítimo que
  ocorre durante a janela. Então rotulamos por **par-atacante** (`172.16.0.1 →
  192.168.10.50:80`) **mais** a janela do *burst* — a mesma lógica dos rótulos oficiais
  do CIC —, verificada contra os *bursts* reais observados a cada 5 min.

**O que os cálculos representam (gates G1–G4).** São *checkpoints* de qualidade —
cada um valida uma pré-condição antes de prosseguir:
- **G1 (≥5 JA4 distintos):** a extração de *fingerprint* funciona.
- **G2 (≥50% de cobertura JA4 no tráfego TLS):** mede *qualidade da extração*, não a
  composição do tráfego — por isso medimos sobre o subconjunto TLS (porta 443/SNI),
  não sobre tudo (HTTP/DNS puro não tem JA4 por natureza).
- **G3 (ROC AUC ≥ 0,85):** o sinal de coordenação **existe e é aprendível**.
- **G4 (SPARQL `coordinatedHTTPFlood` retorna ≥1 cluster):** o grafo **responde** e a
  regra simbólica detecta campanha.

**Resultados.** CICIDS2017 (4,55M triplas) e CIC-IoT2023 (9,75M triplas) carregados;
gates passam nos dois (JA4 cobre 98,6% / 68,6% do TLS; G4 retorna clusters reais).

**Resultado prático esperado.** Ter o **substrato** — um grafo de sessões consultável —
sobre o qual todo o raciocínio cross-session, a detecção e a mitigação operam.

---

## Sprint 2 — Gerador Sintético Calibrado

**Por que decidimos assim.** Os *datasets* públicos rotulam *flows*, **não campanhas
coordenadas**; e não controlam o **grau de distribuição K** (nº de origens). Sem
*ground truth* de coordenação não dá para medir a vantagem cross-session. Então
construímos um gerador que produz campanhas com verdade perfeitamente conhecida.
Duas decisões-chave:
- **Calibrar o legítimo a partir do real** (duração, requisições, JA4) — para que o
  tráfego benigno sintético seja realista, e o teste seja **justo**.
- **Modo *stealth*** (ataque com features por-sessão amostradas do benigno): cada
  sessão atacante é *individualmente indistinguível* de um usuário. Foi a decisão que
  tornou o experimento honesto — sem ela, o ataque tem assinatura óbvia e a tese nem
  chega a ser testada.

**O que os cálculos representam.** O **teste KS (Kolmogorov–Smirnov)** mede a maior
distância entre a distribuição do legítimo *sintético* e a do *real*. **D ≤ 0,02
significa "quase idênticas"** → prova que **não trapaceamos**: o detector acerta o
ataque porque o sinal existe, não porque o benigno foi feito artificialmente fácil.
Usamos **quantis empíricos** (inverse-CDF) na calibração porque o histograma de bins
largos borrava distribuições concentradas (duração ~0, 1 requisição).

**Resultados.** KS D = 0,022 (duração) e 0,013 (requisições) — passa. Reprodutível
bit-a-bit (mesma *seed* → mesmo arquivo).

**Resultado prático esperado.** Um **"laboratório de campanhas"** onde conhecemos a
verdade e **controlamos a dificuldade** (K, furtividade, dispersão) — permitindo medir
exatamente onde a vantagem cross-session aparece.

---

## Sprint 3 — Baselines e Ablação

**Por que decidimos assim.** Para provar que o ganho vem da **estrutura entre sessões**
(e não de "mais features" ou de um classificador melhor), comparamos quatro
configurações sobre **o mesmo input e o mesmo classificador**, variando **apenas o
conjunto de features**:
- **(a)** ML só com features de fluxo por-sessão (estado-da-arte por-sessão).
- **(b)** ontologia, mas **sem** as relações `relatedBy_*` (sessões isoladas).
- **(c)** só `relatedByNetworkProximity` (o sinal de rede, peso baixo).
- **(d)** arcabouço completo (família `relatedBy_*` ponderada).
Mais **3 baselines acadêmicos** (Fernandes/Bharathi/Kemp) como referência externa.
**Decisão anti-circularidade (crítica):** os *clusters* de detecção são formados de
modo **label-agnóstico** (por endpoint+janela), nunca usando o rótulo — senão o
resultado seria trivialmente circular.

**Decisão de escopo "3 limpas", por quê:** das seis sub-relações da família
`relatedBy_*`, só **três têm dado a nível de sessão** nos *datasets*: TLSFingerprint
(JA4), EndpointConvergence (endpoint) e NetworkProximity (/24). As outras três
—ReusedIdentity (cookie/token), TemporalPattern (cadência por requisição) e
PayloadSignature (UA/content-type)— exigiriam instrumentação ausente. Decidimos usar
**apenas as três computáveis exatamente**, em vez de aproximar as demais (o que
introduziria ruído e desviaria das definições do paper). Isso vale tanto para o Ω(S)
quanto para as *features* de (c)/(d). É também uma limitação honesta declarada.

**O que os cálculos representam.** A **ROC AUC por configuração** isola contribuições:
**(a)→(d)** = contribuição total; **(c)→(d)** = ganho específico dos sinais de peso
alto (JA4) sobre a proximidade de rede. Δ grande = vantagem cross-session real.

**Resultados (campanha furtiva).** (a) e os 3 baselines ficam **no acaso (AUC ~0,5)**;
(d) atinge **~1,0**. A vantagem só aparece no regime furtivo — em ataque de assinatura
óbvia, (a) já resolve (resultado honesto, não escondido).

**Resultado prático esperado.** Demonstrar que **um detector que ignora a estrutura
entre sessões é cego** à campanha furtiva distribuída — exatamente o ponto cego do
estado-da-arte por-features.

---

## Sprint 4 — Execução Estatística

**Por que decidimos assim.** Um resultado isolado pode ser sorte. Para *afirmar* a
vantagem com rigor de publicação, repetimos **n = 30 vezes** (seeds diferentes) e
aplicamos estatística formal.

**O que os cálculos representam.**
- **IC 95% por *bootstrap*:** a incerteza da média (reamostragem).
- **Wilcoxon pareado:** testa se (d) > (c) de forma consistente seed-a-seed (não-
  paramétrico, não assume normalidade).
- **Correção de Bonferroni:** endurece o p-valor porque fazemos várias comparações
  (evita falso positivo estatístico).
- **Cohen's d:** o *tamanho* da diferença, em desvios-padrão.

**Resultados.** No cenário distribuído, **(d)−(c): p_Bonferroni = 2,2×10⁻⁵, Cohen's
d = 2,91** (efeito enorme); (d)−(a) ainda mais forte (d = 36). A vantagem é
**estatisticamente inquestionável** no regime distribuído.

**Caveat honesto.** Este resultado é **sintético** e parcialmente circular: a campanha
é gerada com os sinais (JA4, endpoint) que (d) mede. Prova o *mecanismo*, não que
ataques reais coordenam assim. Quem fecha essa lacuna é a validação em **dados reais**
(ver `DEEP-DIVE-FINDINGS.md`: 6 ataques reais, (a) ~acaso → (d) 0,96–1,0).

**Resultado prático esperado.** Transformar "funciona numa rodada" em "**funciona com
significância estatística**" — o padrão exigível para a §5 do paper.

---

## Sprint 5 — Comparação com o Estado-da-Arte (KLAGE)

**Por que decidimos assim.** Precisamos nos confrontar com o melhor trabalho
comparável (KLAGE: KG + Graph-BERT, F1 = 84,1% em DDoS Slowloris) **no mesmo dataset**
(CIC-IoT2023). **Decisão de honestidade:** *não* é um confronto controlado —
granularidades diferentes (eles classificam **nós de rede**, nós **sessões**),
protocolos e cobertura distintos.

**O que os cálculos representam.** **F1** (equilíbrio precisão/recall — escolhido em
vez de acurácia porque as classes são desbalanceadas) e **dano colateral** (fração de
legítimos atingidos pela mitigação) — métrica que produtos comerciais reportam mas a
academia de Camada 7 não usa sistematicamente.

**Resultados (dados reais).** O Slowloris do CIC-IoT2023 é per-sessão indistinguível
do benigno → **(a) colapsa (F1 = 0,18, AUC ≈ acaso)**; **(d) atinge F1 = 0,911**,
**mesma ordem** do KLAGE (0,841). Afirmação defensável: *competitivo* com o SOTA em
nível de nó, **acrescentando** veredicto simbólico auditável e dano colateral
mensurável (que o KLAGE não tem).

**Resultado prático esperado.** Mostrar que a abordagem em nível de sessão **se equipara
ao estado-da-arte** no ataque-alvo e **vai além** em explicabilidade e mitigação.

---

## Pilar 2 — Raciocínio Simbólico (veredicto como derivação)

**Por que decidimos assim.** O veredicto precisa ser **auditável**: a regra que
disparou + os fatos que a satisfizeram, não um score de caixa-preta interpretado *a
posteriori*. **Decisão honesta sobre a divisão de linguagens:** SWRL instancia as
sub-relações **par-a-par** (regras de Horn); a **agregação Ω(S) ≥ τ é SPARQL** (SWRL
não soma/agrega). Os pesos vêm da **ontologia** (`coordinationWeight`), não
*hard-coded*.

**O que os cálculos representam.** **Ω(S) = Σᵢ wᵢ · |pares ligados por relatedBy_i em
S|** — a *massa de evidência de coordenação* dentro do conjunto S. Pesos refletem o
**custo de evasão** (JA4/identidade = 1,0; endpoint = 0,6; rede = 0,3): premia a
coordenação que o atacante **não consegue esconder barato**.

Duas decisões de cálculo: **(i)** o conjunto candidato S é o **cluster de detecção =
`(endpoint, janela 300s)`** — agrupar por alvo+tempo é o mínimo que define "campanha
contra um endpoint"; **(ii)** Ω é computado em **O(N), não O(N²)**: em vez de
materializar todas as arestas par-a-par (bilhões para milhões de sessões), contamos,
para cada valor compartilhado por *n* sessões, os **C(n,2) = n(n−1)/2** pares — soma
equivalente, tratável. Por isso a regra roda mesmo em grafos grandes.

**Resultados.** A regra `coordinatedHTTPFlood` dispara emitindo a **derivação**
(quais sub-relações, quantos pares, com que peso, somando a Ω) — não um número opaco.

**Resultado prático esperado.** **Explicabilidade nativa:** o analista vê *por que* algo
foi detectado, e pode auditar/consultar a evidência.

---

## Pilar 4 — Cadeia de Evidência e Mitigação Cirúrgica

**Por que decidimos assim.** Detecção sem ação é incompleta, e o bloqueio **global**
(limitar o endpoint inteiro) **machuca usuários legítimos**. Então derivamos
automaticamente o **escopo mínimo** que distingue a campanha (tipicamente o par
*JA4 + endpoint*) e emitimos a evidência em **JSON-LD + STIX 2.1** (para integração
com SOAR).

**O que os cálculos representam.** **Decomposição de Ω** (qual sinal sustentou a
detecção) + **dano colateral**: fração de legítimos que cai no escopo **cirúrgico**
(JA4-específico) vs no **global** (endpoint inteiro). A diferença é o tráfego legítimo
poupado.

**Resultados.** Em sintético **calibrado** (n = 30, com IC): escopo inclui o JA4 em
30/30; **cirúrgico 0,00% [0–0] vs global 22,5% [22,1–23,0] → redução de 100%** do dano
colateral. **Caveat honesto:** no CIC-IoT2023 a vantagem **não se manifesta** — é uma
LAN (atacante e legítimo no mesmo /24) e não-TLS (sem JA4), então não há discriminador;
a vantagem **depende** de o atacante ter um sinal de peso alto que o legítimo não tem.

**Resultado prático esperado.** **Parar a campanha sem derrubar o usuário legítimo** —
quando há um discriminador (TLS/rede) observável. Em produção (TLS visível, atacantes
dispersos) é onde essa promessa se realiza plenamente; em laboratório LAN/não-TLS, não.

---

## Endurecimento da Validade (auto-auditoria cética)

**Por que decidimos assim.** Antes de fechar o paper, listamos as ameaças à validade e
as atacamos — porque "resultado bonito" sem ceticismo é frágil.

| Ameaça | O que fizemos | Veredito |
|---|---|---|
| Circularidade do sintético (plantamos o sinal que medimos) | Passo A: 6 ataques **reais** | ✅ mitigada (detecção real) |
| Generalização fina (1 dataset/ataque) | 6 ataques × 2 datasets reais | ✅ ampliada |
| Comparação KLAGE não-controlada | reescrita como "mesma ordem", não "superamos" | ✅ honesta |
| Pesos não calibrados | tentado em cenário difícil — satura | ❌ permanece teórico (declarado) |
| Mitigação só em toy | reproduzida em sintético calibrado (n=30, IC) | ✅ fortalecida |

---

## Decisões transversais (guiaram todas as etapas)

Três princípios atravessam todos os sprints e explicam *por que* o trabalho tem a
forma que tem:

- **Honestidade científica acima do resultado bonito.** Reportamos o que falha
  (calibração de pesos que satura; mitigação que não se manifesta no CIC; comparação
  KLAGE que não é controlada), declaramos *caveats* em cada etapa e atacamos a
  circularidade explicitamente. Decisão: um resultado defensável vale mais que um
  número alto — porque é o que sobrevive a um revisor cético.
- **Reprodutibilidade por construção.** *Seeds* fixas, `Makefile` por sprint, logs,
  artefatos versionados (figuras, JSONs) e commits descritivos. Decisão: qualquer
  etapa deve rodar de novo com um comando e dar o mesmo número.
- **A "descoberta do *stealth*".** O achado mais importante de método: num ataque com
  assinatura de fluxo óbvia, a detecção por-sessão já resolve — então a tese **só é de
  fato testada** quando o ataque é *furtivo* (per-sessão indistinguível do benigno).
  Essa percepção reorientou o experimento: o regime furtivo/distribuído é onde a
  contribuição vive, e é onde concentramos a avaliação.

## Síntese — o resultado prático geral que esperamos

Um arcabouço que, sobre tráfego de aplicação web, **(i) detecta** campanhas L7
distribuídas e furtivas que a análise por-sessão (e o estado-da-arte por-features)
**não vê** — provado em **dados reais** (6 ataques) e com **significância estatística**
(sintético, p<0,01, d=2,91); **(ii) explica** o veredicto como derivação simbólica
auditável; e **(iii) mitiga cirurgicamente**, poupando o tráfego legítimo (provado em
sintético calibrado: 0% vs 22,5% de colateral).

**Limites honestos, que delimitam o "esperado":** a vantagem de detecção é **regime-
específica** (cresce com a distribuição/furtividade; é pequena em ataque single-source
óbvio); a mitigação cirúrgica **exige TLS observável + atacantes dispersos** — condição
de **produção**, ausente nos *datasets* de laboratório; e a calibração de pesos é
teórica (custo de evasão), não empírica. O passo que falta para a promessa completa é
**avaliação em tráfego de produção anonimizado**.
