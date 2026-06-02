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
