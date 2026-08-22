# NOMS submission — session-centric KG for L7 DDoS

Versão em **inglês**, formato **IEEE 2-colunas**, do artigo que está em
`papers/http-session/` (versão longa em português, formato Elsevier).
A versão original permanece intacta — esta é um documento separado, não uma
substituição.

## Regras do NOMS (CFP NOMS 2026 — reverificar quando sair o CFP de 2027)

| Item | Regra |
|---|---|
| Formato | IEEE 2-column (IEEEtran conference), PDF único, inglês |
| Full paper | **até 8 páginas de texto principal**, auto-contido |
| Extras | referências + apêndice opcional; **máx. 12 páginas no total** |
| Revisão | **single-blind** — autores identificados, sem anonimização |
| Excesso | papers acima do limite são *rejected without review* |
| Artifact Evaluation | trilha voluntária, badge impresso no paper (nosso código open source se aplica) |

Fontes: <https://noms2026.ieee-noms.org/call-technical-session-paper> e
<https://noms2026.ieee-noms.org/submission-guidelines>.

## Ocupação atual

```
pp. 1–8   texto principal (Seções I–VII)   -> NO LIMITE de 8 páginas
pp. 8–9   referências (22 entradas)
pp. 9–11  apêndices A–E
total     11 páginas                       -> limite é 12
```

Apêndices: A instanciação das `relatedBy_*` · B calibração de pesos ·
C limitações adicionais · D modelo de custo + sensibilidade a W · E reprodutibilidade.

⚠️ **O corpo está no limite.** Qualquer resultado novo precisa entrar como linha
de tabela existente ou ir para o apêndice, ou algo tem de sair.

Estrutura seguindo o padrão observado em papers NOMS (ver
`docs/pdfs/noms-referencia/`): Introduction · Related Work · Approach ·
Evaluation Methodology · Results · Discussion and Limitations · Conclusion.

## Build

```bash
pdflatex article && bibtex article && pdflatex article && pdflatex article
```

`IEEEtran.cls` e `IEEEtran.bst` estão versionados aqui porque o TeX Live local
é a instalação *basic* e não os traz. O preâmbulo também tem um fallback de
fonte: o IEEEtran usa URW Courier (`pcr`) para `\texttt`, ausente no TeX Live
basic; se as métricas não existirem, cai para `cmtt`. No Overleaf e em
instalações completas nada disso é acionado e a fonte IEEE padrão é usada.

## Figuras

Todas geradas em inglês por um script único, a partir dos mesmos artefatos de
resultado dos experimentos:

```bash
experiments/.venv/bin/python papers/http-session-noms/figures/make_figures_en.py
```

| Arquivo | Uso | Fonte dos dados |
|---|---|---|
| `fig1_ontology.png` | Fig. 1 (banner 2 colunas): ontologia + família `relatedTo` + acoplamento regra→veredito→mitigação | desenho |
| `fig2_regime.png` | Fig. 2: ataques reais convencionais × campanha furtiva-distribuída | `experiments/sprint-3/results/real_multiattack_strong.csv`, `experiments/sprint-6-noms/results/canonical_realistic.json` |
| `fig3_collateral.png` | Fig. 3: derivação de escopo modal × enriquecimento, ao longo do eixo de realismo | `experiments/sprint-6-noms/results/realistic_consolidated.csv` |
| `fig4_latency.png` | Apêndice D: latência das duas camadas × \|S_W\| | `experiments/sprint-6-noms/results/latency_summary.json` |

As Figs. 2 e 5 são *listings* em `verbatim` dentro do `.tex` (regras SWRL/SPARQL
e cadeia de evidência JSON-LD), fiéis a
`experiments/pillar2-symbolic-reasoning/rules/relatedBy.swrl` e
`experiments/pillar4-evidence-mitigation/results/chains/chain_cicids2017_DoS-Other.jsonld`.

## O que mudou em relação à versão portuguesa

- **37 páginas (1 coluna, 12pt) → 10 páginas (2 colunas, 10pt)**; ~12,2k → ~8k palavras.
- Abstract de ~450 → 235 palavras; adicionado `IEEEkeywords`.
- Removidas as subseções "Questões de Pesquisa" e "Organização do Artigo"
  (fora do padrão IEEE/NOMS); contribuições viraram lista na Introduction.
- Enquadramento reforçado para gestão de redes e serviços: parágrafo sobre o
  problema do operador na Introduction, subseção *Operational placement* na
  Discussion, referências NOMS em Related Work.
- **Novo**: Tabela I de posicionamento, subseção *Threat Model*, Fig. 2 com as
  regras SWRL/SPARQL, Fig. 5 com a cadeia de evidência real, §V-F com a
  **medição de latência/throughput** (Fig. 6) e §VI com a análise de
  **paralelismo e particionamento**.
- **Experimentos novos** (Sprint 6, ver `experiments/sprint-6-noms/`): a Tabela III
  ganhou o bloco de **quatro famílias de ML** — (a) fica no acaso em todas, então
  o colapso é da representação e não do aprendiz. O modelo de custo das duas
  camadas e o sweep de W ficam no **Apêndice D**; o corpo (§V-F) guarda só o que
  é acionável: admissão em microssegundos e a regra de escolha de W.
- **Cenário canônico trocado (Sprint 6).** As tabelas de detecção passaram a vir do
  cenário **realista de produção** (JA4 benigno Zipf α=1,5 com cabeça de 39%; botnet em
  25 stacks TLS), não mais do sintético plano/monolítico. (a) e (b) seguem no acaso nas
  quatro famílias; (d) fica em 0,927 (K=50) e 0,982 (K=1000), com d=+22,4 sobre (a).
- **Resultado negativo publicado como contribuição.** §III-E mostra que derivar o escopo
  pela propriedade que o cluster mais compartilha seleciona um fingerprint **legítimo**
  contra botnet heterogênea (0% do ataque, 39–61% dos usuários); §V-D mede a substituição
  por **enriquecimento** sobre perfil histórico: 85–90% de cobertura a 0,00% de colateral,
  invariante à fragmentação, com as duas condições de contorno (adversário e desvio de
  perfil) medidas.
- **Delimitações declaradas** (em vez de deixar o revisor achar):
  §IV diz que a config (d) é um *proxy em nível de feature* da representação
  cross-session, então a ablação isola representação e **não evidencia a camada
  simbólica**; §VI repete isso como limitação, com o número que a torna concreta
  (regressão logística sobre as mesmas 3 features cross-session dá 0,961) e
  aponta onde a ontologia de fato se paga — derivação auditável e escopo de
  mitigação. A Introdução voltou a explicar por que HTTP/2 motiva mas não é
  avaliado, e a cobertura de família de ataque saiu do apêndice para o corpo.
- As 11 limitações viraram 4 no corpo (regime-específica, avaliação sintética,
  dependência de discriminador, cobertura/KLAGE) + 5 no Apêndice C.
- Citações adicionadas que faltavam: CICIDS2017, CIC-IoT2023, JA4+, STIX 2.1,
  OWL 2 Profiles, ECH. Removidas as 5 entradas de DNS que não eram citadas.

## Pendências antes de submeter

1. Reverificar o CFP do NOMS 2027 (limite de páginas, datas, template) — o site
   ainda não existe; NOMS 2027 está previsto para maio/2027, local a definir.
2. Decidir sobre `\section*{Acknowledgment}` (financiamento/bolsa) — removido nesta versão.
3. Preencher a URL pública do repositório no Apêndice E (Reproducibility) antes do camera-ready.
