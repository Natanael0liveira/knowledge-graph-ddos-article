# Plano de Endurecimento da Validade (pós-Fase B)

**Criado:** 2026-06-01 · **Para retomar:** 2026-06-02

A Fase B (Sprints 1–5) está completa e a tese tem evidência direcional, MAS uma
auto-auditoria cética encontrou ameaças reais à validade. Este plano ataca as que
são **gratuitas e factíveis com o que já temos** (dados locais + CPU). Nada aqui
exige download com conta, GPU ou API paga.

> Contexto completo das ameaças: ver conversa de 2026-06-01 e os caveats nos READMEs
> de sprint-3/4/5. Resumo das 5 ameaças abaixo.

## As 5 ameaças à validade (resumo)

1. **Circularidade sintética** — no S3/S4 geramos o ataque com JA4/endpoint//24
   compartilhados e a config (d) mede exatamente esses sinais → quase tautológico
   no sintético. (O S5 em dado real mitiga, mas não elimina.)
2. **Comparação KLAGE não-controlada** — granularidade nó-vs-sessão + protocolos/
   datasets diferentes. "0.911 > 0.841" é maçã-com-laranja.
3. **Baselines não-fiéis** — Fernandes/Bharathi/Kemp são operacionalizações nossas,
   não réplicas verificadas (±5% do paper original não foi checado).
4. **Pesos não calibrados** — o grid search saturou (todo w_i → AUC 1.0 no sintético).
5. **Generalização fina** — 1 dataset real (CIC-IoT2023), 1 ataque (Slowloris);
   família CIC é criticada por ser "fácil".

## Dados que JÁ temos (sem baixar nada)

| Dataset | Arquivo (DATA_ROOT) | Ataques rotulados |
|---|---|---|
| CICIDS2017 | `processed/sessions/cicids2017.parquet` | Slowloris, Slowhttptest, Hulk, GoldenEye, BENIGN |
| CIC-IoT2023 | `processed/sessions/cic-iot-2023.parquet` | HTTP-Flood, Slowloris, BENIGN |
| Sintético | gerador S2 (`scenario_stealth.yaml`, param K) | paramétrico |

`DATA_ROOT=/Volumes/Untitled/kg-ddos-data` · venv em `experiments/.venv` ·
Fuseki no SSD interno (`FUSEKI_DB`). Ver [RESUME.md](RESUME.md).

---

## O plano — 4 passos, ordem A → B → C → D

### Passo A — Generalização multi-ataque em dados REAIS  ⭐ maior retorno (mata #5, enfraquece #1)

**Ideia:** rodar (a) por-sessão × (d) cross-session **por tipo de ataque**, nos dois
datasets reais. Se (d) ≫ (a) se mantém em ataques que NÃO fabricamos, a tese deixa
de depender do sintético circular.

**Fazer:** criar `experiments/sprint-3/scripts/run_real_multiattack.py` (generalizar
`sprint-5/scripts/run_klage_comparison.py`):
- para cada ataque ∈ {Slowloris, Slowhttptest, Hulk, GoldenEye} (cicids2017) e
  {Slowloris, HTTP-Flood} (cic-iot-2023): tarefa binária ataque-vs-BENIGN.
- configs (a) FLOW e (d) completo; reusar `build_features` do `run_ablation`.
- reportar F1, AUC, dano colateral (FPR benigno) por ataque.
- saída: `sprint-3/results/real_multiattack.csv` + tabela impressa.

**Critério de sucesso (honesto):** documentar onde (d)≫(a) e onde NÃO. Esperado:
vantagem grande em ataques *furtivos/distribuídos* (Slowloris), pequena em ataques de
assinatura óbvia (Hulk/flood) — isso é coerente com a tese, não contra.

**Atenção:** Hulk/GoldenEye têm assinatura de fluxo forte → (a) pode já ir bem. Isso é
resultado válido (a tese é sobre o regime furtivo), reportar sem maquiar.

### Passo B — Sweep de robustez no sintético (ataca #1 direto)

**Ideia:** mostrar que (d) **degrada suavemente** conforme a coordenação some — provando
que mede coordenação real, não um sinal injetado tudo-ou-nada.

**Fazer:** `experiments/sprint-4/scripts/robustness_sweep.py`:
- variar `coordination_ja4_share` ∈ {1.0, 0.75, 0.5, 0.25, 0.0} e
  `coordination_temporal_jitter` ∈ {0, 0.5, 1.0}, K fixo (ex. 500), ~10 seeds.
- gerar (generator.py) + converter + medir AUC de (d).
- saída: curva AUC(d) × força-de-coordenação + figura.

**Critério:** AUC(d) cai monotonicamente quando ja4_share→0 (sem JA4 compartilhado,
sem sinal forte → detector perde poder). Se ficar 1.0 sempre, HÁ vazamento — investigar.

### Passo C — Calibração real de pesos (mata #4)

**Ideia:** o grid search saturou porque o sintético é fácil. Tornar difícil → os pesos
passam a importar.

**Fazer:** novo config `sprint-2/configs/scenario_hard.yaml` com sinais **parciais e
conflitantes** (ja4_share=0.5, prefix_dispersion alto, jitter=0.7, mais legítimo
coordenado). Re-rodar `sprint-4/scripts/weight_search.py` nesses cenários.

**Critério:** o grid deixa de dar AUC=1.0 em tudo; emerge um ótimo com sensibilidade
≠0. Se o ótimo ficar perto de (1.0, 0.6, 0.3) → valida a ponderação do paper; senão,
reportar os pesos empíricos honestamente.

### Passo D — Baselines justos + reescopo KLAGE (ataca #3 e #2, texto+CPU)

**Fazer:**
1. Tunar os 3 baselines em `sprint-3/scripts/baselines.py`: pequeno grid de
   hiperparâmetros (dar o MELHOR caso a eles, para a comparação ser justa, não
   prejudicada). Documentar que continuam sendo operacionalizações.
2. **Reescrever** a comparação KLAGE: em `sprint-5/README.md` e nos rascunhos do
   paper, trocar "superamos o KLAGE" por **"resultado na mesma ordem de grandeza,
   com mapeamento de granularidade explícito (nó vs sessão) e métrica adicional de
   dano colateral"**. Custo zero, fecha a maior fragilidade acadêmica.

---

## O que fica BLOQUEADO (tratar por declaração de limitação no paper)

- Rodar o **código do KLAGE** (precisa repo + GPU + LLM/API).
- **RT-IoT2022** e datasets **fora da família CIC** (download com conta/manual).
- → No paper: seção "Ameaças à Validade" + "Trabalho Futuro" honestas.

## Feito offline (2026-06-02, sem HD)

- ✅ **6 sub-propriedades `relatedBy_*` formalizadas no `.owl`** (com pesos via
  `coordinationWeight`). Fecha a lacuna paper↔ontologia (contribuição 1).
- ✅ **Passo A codado + smoke-testado:** `sprint-3/scripts/run_real_multiattack.py`
  (+ alvo `make -C sprint-3 multiattack`). Validado num parquet sintético (ataque
  furtivo → (a) AUC=0.5, (d) AUC=1.0). **Pronto para rodar nos dados reais quando o
  HD voltar** — é o primeiro comando da próxima sessão online.
- ⏳ **Descoberto:** namespace da ontologia (`security.example.org/ontology/ddos#`) ≠
  namespace dos dados em runtime (`kg-ddos.example/ontology#` em `load_to_fuseki.py`).
  As instâncias carregadas não são tipadas pela ontologia. Alinhar (mudar o
  `load_to_fuseki.py` para o namespace da ontologia + recarregar) — precisa do HD.

## Fora deste plano (implementação, não validação)

- **Pilar 2** (reasoner SWRL, veredicto-como-derivação) e **Pilar 4** (cadeia de
  evidência JSON-LD/STIX + mitigação cirúrgica de escopo derivado): são contribuições
  do paper ainda NÃO codificadas. Factíveis sem custo, mas é outra frente.
- Redação da §5 do `.tex` com as tabelas/figuras.

## Ordem de execução amanhã

1. **A** (run_real_multiattack.py) — começa aqui, maior retorno.
2. **B** (robustness_sweep.py).
3. **C** (scenario_hard.yaml + weight_search).
4. **D** (tunar baselines + reescopo textual).

Cada passo: criar script → rodar → commitar com resultado honesto no README do sprint
correspondente → atualizar este arquivo marcando ✅.
