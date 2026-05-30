# Diagramas do Grafo de Conhecimento

Documentação visual da ontologia e do raciocínio sobre o grafo, focada na **família Slow HTTP DDoS distribuído** como caso experimental do paper. Para a tese e fundamentação, ver [`../CONCEITOS.md`](../CONCEITOS.md). Para o plano experimental, ver [`../TESTAGEM.md`](../TESTAGEM.md).

Todos os diagramas são produzidos em **Graphviz/DOT** com fontes versionados em [`figures/dot/`](figures/dot/), e renderizados em SVG (vetorial, para inclusão no paper) e PNG (para leitura em tela). Para regenerar após editar um `.dot`, ver a seção [Como regenerar](#como-regenerar) no fim deste documento.

---

## Lista de diagramas

### 1. Anatomia da `ApplicationSession`

A sessão HTTP como entidade ontológica de primeira classe, com as cinco relações tipadas: `hasIdentity`, `targets`, `exhibitsBehavior`, `relatedTo`, `mitigatedBy`.

| Recurso | Arquivo |
|---|---|
| Fonte | [`figures/dot/01-application-session-anatomy.dot`](figures/dot/01-application-session-anatomy.dot) |
| SVG (paper) | [`figures/svg/01-application-session-anatomy.svg`](figures/svg/01-application-session-anatomy.svg) |
| PNG (tela) | [`figures/png/01-application-session-anatomy.png`](figures/png/01-application-session-anatomy.png) |

**Quando usar no paper:** §3.2 (Ontologia Centrada em Sessão), ilustrando o núcleo do modelo.

---

### 2. Snapshot do grafo durante campanha Slow HTTP DDoS distribuído

Estado do grafo em `t = 180 s` de uma janela operacional `W = 300 s`. Mostra três amostras de sessões legítimas (de 500) e três amostras de sessões coordenadas (de 40), todas convergindo no mesmo `Endpoint`. As coordenadas se ligam por `relatedTo` e compartilham a mesma `SharedIdentity` (JA4 + ASN + prefixo IP).

| Recurso | Arquivo |
|---|---|
| Fonte | [`figures/dot/02-slow-http-campaign-snapshot.dot`](figures/dot/02-slow-http-campaign-snapshot.dot) |
| SVG | [`figures/svg/02-slow-http-campaign-snapshot.svg`](figures/svg/02-slow-http-campaign-snapshot.svg) |
| PNG | [`figures/png/02-slow-http-campaign-snapshot.png`](figures/png/02-slow-http-campaign-snapshot.png) |

**Quando usar no paper:** §3.3 (Construção do Grafo em Tempo de Execução) ou §5.4 (Análise da Vantagem *Cross-Session*), como exemplo trabalhado.

---

### 3. Regra `CoordinatedHTTPFlood` dispara, veredito e cadeia de evidência

Pipeline da detecção semântica: o *cluster* `relatedTo` mais o `Endpoint` ativam a regra; a regra dispara e produz o veredito como nó próprio; o veredito gera a cadeia de evidência exportável em JSON-LD/STIX 2.1 e referencia a `Mitigation` com escopo derivado.

| Recurso | Arquivo |
|---|---|
| Fonte | [`figures/dot/03-rule-fires-evidence-chain.dot`](figures/dot/03-rule-fires-evidence-chain.dot) |
| SVG | [`figures/svg/03-rule-fires-evidence-chain.svg`](figures/svg/03-rule-fires-evidence-chain.svg) |
| PNG | [`figures/png/03-rule-fires-evidence-chain.png`](figures/png/03-rule-fires-evidence-chain.png) |

**Quando usar no paper:** §3.4 (Regras de Detecção Semântica) ou §3.5 (Cadeia de Evidência e Explicabilidade).

---

### 4. Posicionamento da contribuição: quatro abordagens à mitigação de campanhas L7 coordenadas

Tabela comparativa em quatro colunas (ML sobre *features* agregadas; KG + neural + XAI pós-hoc, representado por KLAGE [Belcastro et al., FGCS 2026]; indústria proprietária; nossa proposta) avaliadas em oito dimensões: unidade de raciocínio, representação semântica, raciocínio *cross-session*, explicabilidade, mitigação acoplada, reprodutibilidade acadêmica, métrica de dano colateral em legítimos, e validação experimental em DDoS Slowloris.

A figura substitui a versão binária anterior (que opunha "limite global" a "escopo cirúrgico") por uma comparação honesta com três alternativas atuais. Reconhece que mitigação cirúrgica já é prática industrial e que detecção de Slowloris via KG já foi validada academicamente, e localiza nossa contribuição na combinação específica de sessão HTTP como entidade ontológica, raciocínio simbólico nativo, mitigação acoplada com escopo derivado, e métrica de dano colateral.

| Recurso | Arquivo |
|---|---|
| Fonte | [`figures/dot/04-mitigation-scope-comparison.dot`](figures/dot/04-mitigation-scope-comparison.dot) |
| SVG | [`figures/svg/04-mitigation-scope-comparison.svg`](figures/svg/04-mitigation-scope-comparison.svg) |
| PNG | [`figures/png/04-mitigation-scope-comparison.png`](figures/png/04-mitigation-scope-comparison.png) |

**Quando usar no paper:** §2.4 (Posicionamento deste Trabalho), como figura síntese que consolida o panorama de prior art e diferenciações; ou §1.4 (Contribuições), como antecipação visual dos quatro pontos de contribuição.

---

### 5. Hierarquia de classes da ontologia OWL

Visão estrutural da ontologia: `ApplicationSession` como classe central com as cinco relações tipadas, `ApplicationLayerAttack > SlowHTTPDDoSFamily > {CoordinatedHTTPFlood, ConnectionExhaustionAttack}`, e as classes auxiliares (`Identity` com `TLSFingerprint`/`Cookie`/`Token`, `Endpoint` com `APIEndpoint`/`StaticAsset`, `Behavior` com `User`/`Bot`, `Mitigation` com `RateLimit`/`Challenge`/`Block`).

| Recurso | Arquivo |
|---|---|
| Fonte | [`figures/dot/05-ontology-class-hierarchy.dot`](figures/dot/05-ontology-class-hierarchy.dot) |
| SVG | [`figures/svg/05-ontology-class-hierarchy.svg`](figures/svg/05-ontology-class-hierarchy.svg) |
| PNG | [`figures/png/05-ontology-class-hierarchy.png`](figures/png/05-ontology-class-hierarchy.png) |

**Quando usar no paper:** §3.2 (Ontologia Centrada em Sessão), figura introdutória da ontologia.

---

## Como regenerar

Pré-requisito: Graphviz instalado (`brew install graphviz` no macOS).

Para regenerar todos os diagramas após editar qualquer `.dot`:

```bash
cd docs/figures
for f in dot/*.dot; do
  name=$(basename "$f" .dot)
  dot -Tsvg "$f" -o "svg/$name.svg"
  dot -Tpng -Gdpi=150 "$f" -o "png/$name.png"
done
```

Para regenerar apenas um:

```bash
cd docs/figures
dot -Tsvg dot/01-application-session-anatomy.dot -o svg/01-application-session-anatomy.svg
dot -Tpng -Gdpi=150 dot/01-application-session-anatomy.dot -o png/01-application-session-anatomy.png
```

---

## Inclusão no paper LaTeX

Os SVGs já estão prontos para inclusão. Em `papers/http-session/article.tex`, adicione no preâmbulo (se ainda não existe):

```latex
\usepackage{graphicx}
\usepackage{svg}  % se for incluir SVG direto; alternativa: converter para PDF
```

E onde quiser usar:

```latex
\begin{figure}[htbp]
  \centering
  \includesvg[width=0.8\textwidth]{../../docs/figures/svg/01-application-session-anatomy}
  \caption{Anatomia da \texttt{ApplicationSession} com as cinco relações tipadas.}
  \label{fig:session-anatomy}
\end{figure}
```

Alternativa mais compatível (sem o pacote `svg`): converter SVG → PDF e usar `\includegraphics`:

```bash
# Pré-conversão (uma vez, após cada regeneração):
cd docs/figures
for f in svg/*.svg; do
  rsvg-convert -f pdf "$f" -o "${f%.svg}.pdf"
done
# (rsvg-convert vem do pacote librsvg: brew install librsvg)
```

E no `.tex`:

```latex
\includegraphics[width=0.8\textwidth]{../../docs/figures/svg/01-application-session-anatomy.pdf}
```

---

## Diagramas históricos

Versões anteriores deste documento usavam Mermaid e enquadravam o trabalho em torno de três vetores genéricos (HTTP Flood, Login Flood, API Abuse). O escopo atual concentra a avaliação experimental na família Slow HTTP DDoS distribuído (Slowloris, slow body, slow read, HULK, GoldenEye, HTTP/2 Rapid Reset, CONTINUATION Flood). A ontologia comporta `CredentialStuffing` e `CoordinatedAPIAbuse` como classes adicionais, mas elas não são instanciadas experimentalmente no paper atual e portanto não aparecem nos diagramas.
