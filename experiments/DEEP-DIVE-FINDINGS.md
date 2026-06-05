# Achados do "ir fundo" em dados reais (2026-06-02)

Execução da bateria de hardening + pilares sobre os dados reais (HD reconectado).
Tom: honesto, incluindo os resultados que NÃO favorecem a tese.

## Passo A — Generalização multi-ataque (DETECÇÃO) — ✅ detecção, mas ganho entre sessões ≈ 0

`make -C sprint-3 multiattack`. Detecção ataque-vs-BENIGN, (a) por-sessão × (d) entre sessões.
A coluna AUC(a) abaixo é o baseline **magro** (3 features) — preservada por registro
histórico; ela **não** é o baseline justo:

| dataset | ataque | AUC(a) magro | AUC(d) |
|---|---|---|---|
| cic-iot-2023 | HTTP-Flood | 0,517 | 0,964 |
| cic-iot-2023 | Slowloris | 0,554 | 0,991 |
| cicids2017 | GoldenEye | 0,563 | 1,000 |
| cicids2017 | Hulk | 0,722 | 1,000 |
| cicids2017 | Slowhttptest | 0,634 | 1,000 |
| cicids2017 | Slowloris | 0,582 | 1,000 |

**Reauditoria (baseline forte):** com as 8–9 features de fluxo por sessão (baseline
**forte**), o ML por-sessão **já atinge AUC 0,98–1,00 sozinho** nesses 6 ataques; o (d)
entre sessões fica ~1,00 → **o ganho do raciocínio entre sessões é ≈ 0**. A aparente
"fraqueza por-sessão" das colunas acima era artefato do baseline magro.

**Conclusão honesta:** em ataques reais **convencionais** (Hulk, GoldenEye, Slowloris,
Slowhttptest, HTTP-Flood) a coordenação entre sessões **NÃO é necessária** — eles têm
assinatura de fluxo por sessão. Esses datasets não contêm o regime furtivo-distribuído;
ataca circularidade (ataques não fabricados) e generalização (6 ataques/2 datasets), mas
a vantagem entre-sessões só se manifesta no sintético furtivo (Sprint 3/4).
**Caveat:** cicids2017 (d)=1,000 é parcialmente circular (rótulos por IP ↔ `share_net`);
cic-iot-2023 usa rótulos oficiais (0,96–0,99).

## Passo B — Sweep de robustez — ⚠️ a "redundância de endpoint" era artefato do cenário

Numa versão antiga (legítimos **fora** do endpoint atacado) o AUC(d) não caía quando o JA4
sumia (1,000→0,999), o que se interpretou como **redundância de sinais** — a convergência de
endpoint carregaria sozinha. **Essa conclusão foi superada** (ver §4 de isolamento, cenário
realista de mesmo serviço): quando os legítimos compartilham o endpoint atacado, a
convergência de endpoint deixa de discriminar e o (d) cai a ≈ acaso junto com o JA4. Ou seja,
**não há redundância real** — a detecção e a mitigação cirúrgica dependem de um discriminador
de peso alto (JA4 / identidade reaproveitada) que os legítimos não compartilham.

## Passo C — Calibração de pesos — ❌ não alcançável

Mesmo no `scenario_hard` (sinais parciais), o grid satura: pesos do paper (1,0/0,6/0,3)
dão AUC=0,972 vs melhor 1,0, e o "melhor" (0,3/0,3/1,0) degeneradamente favorece rede
(contradiz a tese). **Calibração empírica não é viável neste sintético**; os pesos
seguem justificados pelo argumento teórico (custo de evasão). Confirma a limitação #4.

## Pilar 4 em cluster REAL — ⚠️ mitigação cirúrgica NÃO se manifesta no CIC-IoT2023

A maquinaria roda em dado real (decompõe Ω, deriva escopo, calcula colateral). Mas a
**vantagem cirúrgica não aparece** no CIC-IoT2023:
- vítima dedicada (`:8080`): nenhum legítimo no endpoint → 0% cirúrgico E global.
- endpoint compartilhado (`192.168.137.1:53`, DNS): atacantes e legítimos **no mesmo
  /24** (LAN) e **sem JA4** (não-TLS) → escopo derivado pega os legítimos → cirúrgico =
  global = 31,8%, redução 0%.

**Conclusão honesta:** a redução de dano colateral é real **quando há discriminador de
peso alto** (JA4 ou /24 distinto), mas **não é demonstrável nos datasets de lab**
(LAN + não-TLS). Só aparece no toy (JA4 distinto). Reforça a necessidade de tráfego de
produção. (§5.5 do paper atualizado com esse caveat.)

## Síntese

- **Tese de DETECÇÃO (entre sessões > por-sessão):** ✅ no regime **furtivo-distribuído** (sintético); em dados reais convencionais um por-sessão **forte** já basta (ganho entre-sessões ≈ 0).
- **Tese de MITIGAÇÃO cirúrgica:** ✅ em princípio / ❌ não demonstrável nos datasets atuais.
- **Calibração de pesos:** permanece teórica (não empírica).
- **Robustez:** **não** há redundância de endpoint no cenário realista de mesmo serviço — ao
  perder o JA4, o (d) cai a ≈ acaso (AUC 0,475); a detecção depende de um discriminador de peso
  alto (JA4 / identidade reaproveitada).

## Atualização — Item #3 fechado (mitigação cirúrgica em sintético calibrado)

`pillar4-evidence-mitigation/scripts/collateral_eval.py` sobre 30 cenários stealth
calibrados (K=1000), no **cenário realista de mesmo serviço** (os legítimos acessam o
**mesmo** serviço atacado em `:443`): JA4 no escopo em 30/30; **cirúrgico 0,00% [0,00–0,00]**
vs **global 100%** → **redução de 100%** do dano colateral. O global é agora 100% por
definição: um *rate-limit* global no serviço atacado bloqueia **todos** os legítimos desse
serviço. **Correção de mecanismo:** o escopo é derivado do **subconjunto coordenado** (as
sessões que compartilham o JA4 modal = assinatura da campanha), **não** do cluster
`(endpoint, janela)` cru. Um bug anterior derivava do cluster inteiro, onde os legítimos
diluíam o JA4 do atacante abaixo do limiar de cobertura e degradavam o escopo para o endpoint
todo (= global); restringir ao subconjunto coordenado restaura o 0% cirúrgico. Continua
sintético (condições que o gerador modela; KS-validado); produção real permanece trabalho
futuro. §5.5 do paper atualizado.

Pendentes: #1 (isolar JA4 com endpoint disperso — redesign de cluster) e #2 (calibração
de pesos com objetivo mais difícil) — médio valor, opcionais.

## Atualização — #3 Calibração de pesos a nível de SESSÃO (objetivo mais difícil)

`sprint-4/scripts/weight_calibration_session.py` sobre o `scenario_hard` (8 seeds,
features z-score, AUC por sessão). Agora **é discriminativo** (spread 0,33), mas:
- Melhor: w(tls,ep,net)=(0,3, 1,0, 0,9) → AUC 0,974; pesos do paper (1,0/0,6/0,3) → 0,682.
- AUC de cada sinal sozinho: **share_ja4=0,345 (anti-discriminativo!)**, cluster_size=0,890, share_net=0,950.
- **Causa:** o benigno sintético compartilha JA4 de um pool pequeno (39 distintos, herdado
  do CIC), então benignos têm *mais* JA4 compartilhado que atacantes parcialmente
  coordenados → JA4 inverte de sinal. É **artefato da baixa diversidade de JA4 benigno**,
  não refutação: na internet real o JA4 benigno é altamente diverso (a premissa do paper).
- **Conclusão:** calibrar pesos no sintético dá números enganosos; os pesos teóricos
  (custo de evasão) se mantêm; calibração fiel exige diversidade de JA4 realista (produção).

## Atualização — #4 Isolamento do JA4 (com diversidade de JA4 benigno realista)

`sprint-4/scripts/ja4_isolation.py` (+ novo param `benign_ja4_pool` no gerador). No
**cenário realista de mesmo serviço** (legítimos acessam o endpoint atacado em `:443`), com
benigno de JA4 diverso (pool=2000, ~internet), varrendo `coordination_ja4_share` — JA4-only
(detector usando SOMENTE `share_ja4`) vs arcabouço completo (d):

| ja4_share | AUC(JA4-only) | AUC(d) |
|---|---|---|
| 1,00 | 0,999 | 0,996 |
| 0,00 | 0,31 | **0,475 ≈ acaso** |

**Conclusão corrigida:** quando os legítimos compartilham o endpoint atacado, a convergência
de endpoint **NÃO compensa** a perda do JA4 — o (d) completo cai a ≈ acaso (0,475) junto com
o sinal JA4. Logo, tanto a detecção quanto (sobretudo) a mitigação cirúrgica **dependem de um
discriminador de peso alto** que os atacantes compartilham e os legítimos não: JA4 (botnet com
mesmo stack) ou identidade/credencial reaproveitada (*credential stuffing*). Contra um atacante
que randomiza o JA4 sem reaproveitar identidade, o arcabouço ainda sinaliza a anomalia agregada,
mas **perde separação por-sessão e precisão cirúrgica** — o que alinha e reforça a limitação de
adversário adaptativo. Requisito: diversidade de JA4 benigno realista (o artefato identificado
no #3); com o pool pequeno de lab, o JA4 inverte de sinal.

## Atualização — §5.6 Análise qualitativa das cadeias de evidência (clusters reais)

`pillar4-evidence-mitigation/scripts/qualitative_evidence.py` sobre 7 clusters de ataque
reais (5 CICIDS2017 + 2 CIC-IoT2023): **7/7 cadeias completas** (regra, |S|, sub-relações
+pesos, Ω, escopo) e **7/7 acionáveis** (escopo concreto não-vazio, tipicamente
endpoint+/24). Exemplos JSON-LD/STIX salvos em `results/chains/`. Sub-relações ativadas:
EndpointConvergence+NetworkProximity (TLS não ativa — ataques reais não-TLS). A força do
escopo depende de discriminador de peso alto: no CICIDS2017 o atacante (172.16.0.0/24) é
distinto dos legítimos → cirúrgico efetivo; em LAN não-TLS recai sobre legítimos. Estudo
com analistas humanos = trabalho futuro. §5.6 e §5.8 do paper atualizados.
