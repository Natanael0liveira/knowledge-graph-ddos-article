# Achados do "ir fundo" em dados reais (2026-06-02)

Execução da bateria de hardening + pilares sobre os dados reais (HD reconectado).
Tom: honesto, incluindo os resultados que NÃO favorecem a tese.

## Passo A — Generalização multi-ataque (DETECÇÃO) — ✅ forte

`make -C sprint-3 multiattack`. Detecção ataque-vs-BENIGN, (a) por-sessão × (d) cross-session:

| dataset | ataque | AUC(a) | AUC(d) |
|---|---|---|---|
| cic-iot-2023 | HTTP-Flood | 0,517 | 0,964 |
| cic-iot-2023 | Slowloris | 0,554 | 0,991 |
| cicids2017 | GoldenEye | 0,563 | 1,000 |
| cicids2017 | Hulk | 0,722 | 1,000 |
| cicids2017 | Slowhttptest | 0,634 | 1,000 |
| cicids2017 | Slowloris | 0,582 | 1,000 |

**Em 6 ataques reais, por-sessão é fraco e cross-session quase perfeito.** Ataca
circularidade (ataques não fabricados) e generalização (6 ataques/2 datasets).
**Caveat:** cicids2017 (d)=1,000 é parcialmente circular (rótulos por IP ↔ `share_net`);
cic-iot-2023 usa rótulos oficiais (0,96–0,99) e é o resultado limpo.

## Passo B — Sweep de robustez — ⚠️ redundância, não isolamento

AUC(d) NÃO cai quando o JA4 some (1,000→0,999); (a) fica em ~0,54. Motivo: os
atacantes sempre convergem no mesmo endpoint → `cluster_size`/convergência carregam
sozinhos. Mostra **redundância de sinais** (a tese da soma ponderada), mas **não isola
o JA4** → não dispele a circularidade (isso é o Passo A). Refinamento: dispersar
também o endpoint.

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

- **Tese de DETECÇÃO (cross-session > por-sessão):** ✅ sustentada em dados reais, 6 ataques.
- **Tese de MITIGAÇÃO cirúrgica:** ✅ em princípio / ❌ não demonstrável nos datasets atuais.
- **Calibração de pesos:** permanece teórica (não empírica).
- **Robustez:** sinais redundantes (perde JA4, endpoint carrega).

## Atualização — Item #3 fechado (mitigação cirúrgica em sintético calibrado)

`pillar4-evidence-mitigation/scripts/collateral_eval.py` sobre 30 cenários stealth
calibrados (K=1000): JA4 no escopo em 30/30; **cirúrgico 0,00% [0,00–0,00]** vs
**global 22,5% [22,1–23,0]** → **redução 100%** do dano colateral, com IC. Eleva o
toy a resultado calibrado+estatístico. Continua sintético (condições que o gerador
modela; KS-validado); produção real permanece trabalho futuro. §5.5 do paper atualizado.

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

`sprint-4/scripts/ja4_isolation.py` (+ novo param `benign_ja4_pool` no gerador). Com
benigno de JA4 diverso (pool=2000, ~internet) e detector usando SOMENTE `share_ja4`
(sem cluster_size/endpoint), varrendo `coordination_ja4_share`:

| ja4_share | AUC(JA4-only) | AUC(d) |
|---|---|---|
| 1,00 | 1,000 | 0,982 |
| 0,75 | 0,857 | 0,960 |
| 0,50 | 0,703 | 0,934 |
| 0,25 | 0,556 | 0,910 |
| 0,00 | 0,407 | 0,747 |

**JA4 isolado como sinal:** a detecção JA4-only acompanha o ja4_share (1,0→0,41) →
o método responde ao sinal genuíno de coordenação, **não a um artefato** (resposta
direta à circularidade). O (d) completo permanece alto via **redundância** (endpoint
carrega quando o JA4 some) — coerente com o Passo B. Requisito: diversidade de JA4
benigno realista (o artefato identificado no #3); com o pool pequeno de lab, o JA4
inverte de sinal.

## Atualização — §5.6 Análise qualitativa das cadeias de evidência (clusters reais)

`pillar4-evidence-mitigation/scripts/qualitative_evidence.py` sobre 7 clusters de ataque
reais (5 CICIDS2017 + 2 CIC-IoT2023): **7/7 cadeias completas** (regra, |S|, sub-relações
+pesos, Ω, escopo) e **7/7 acionáveis** (escopo concreto não-vazio, tipicamente
endpoint+/24). Exemplos JSON-LD/STIX salvos em `results/chains/`. Sub-relações ativadas:
EndpointConvergence+NetworkProximity (TLS não ativa — ataques reais não-TLS). A força do
escopo depende de discriminador de peso alto: no CICIDS2017 o atacante (172.16.0.0/24) é
distinto dos legítimos → cirúrgico efetivo; em LAN não-TLS recai sobre legítimos. Estudo
com analistas humanos = trabalho futuro. §5.6 e §5.8 do paper atualizados.
