# Guia de estudo do artigo NOMS

*Calibrated Scoping of Application-Layer DDoS Mitigation with a Session-Centric Knowledge Graph*

Este guia ensina o artigo bloco a bloco, na ordem em que ele aparece. Em cada
bloco você encontra: o que o bloco diz, por que ele está ali, as fórmulas e siglas
que ele usa, os números que vale saber de cor e a pergunta que um avaliador
provavelmente faria. As referências de linha são do `.tex` em inglês
(`papers/http-session-noms/article.tex`), que é a versão submetida.

Se o tempo for curto, leia nesta ordem: **seção 1** (o artigo em um minuto),
**seção 2** (o que mudou), **seção 17** (números de cor) e **seção 18**
(perguntas difíceis).

---

## Sumário

1. O artigo em um minuto
2. O que mudou nas últimas rodadas, e por quê
3. Título e resumo
4. I. Introdução
5. II. Trabalhos relacionados (Tabela I)
6. III. O grafo de conhecimento centrado na sessão (Fig. 1)
7. IV. Metodologia de avaliação
8. V-A. Ablação (sem tabela desde a rodada 8)
9. V-B. A regra como detector (Tabela II)
10. V-C. Dano colateral (Fig. 2)
11. V-D. Tráfego de produção (Tabelas III e IV)
12. V-E. Custo e a janela W
13. VI. Discussão e limitações
14. VII. Conclusão
15. Apêndices A a F (Tabela V, Figs. 3 e 4, Listagens 1 e 2)
16. As fórmulas, uma a uma, com exemplos numéricos
17. Números para saber de cor
18. Perguntas difíceis e como responder
19. Glossário de siglas e símbolos
20. Estado do trabalho e onde cada coisa está

**Numeração dos elementos flutuantes (versão atual, rodada 8).** Fig. 1 = ontologia;
Fig. 2 = colateral; Fig. 3 = custo (Apêndice D); Fig. 4 = pontos de operação em
produção (Apêndice E). Tabela I = trabalhos relacionados; II = a regra como detector;
III = o escopo em produção, por endpoint; IV = piso de calibração e WAF; V = a regra
por janela (Apêndice E). Listagem 1 = regra SWRL e agregação SPARQL; Listagem 2 =
cadeia de evidência. Na rodada 8 saíram a tabela da ablação (os números estão no
texto de V-A) e a tabela do laboratório (os números estão no Apêndice C); antes já
tinham saído a Fig. 2 do *pipeline* e a figura de regime.

---

## 1. O artigo em um minuto

**O problema.** Um DDoS lento e distribuído na camada de aplicação (a família
*Slow HTTP DoS*: Slowloris, HULK, GoldenEye) usa muitas origens, cada uma mandando
pouco tráfego. Nenhuma origem cruza um limiar por origem, e cada sessão, olhada
sozinha, parece legítima.

**A virada do artigo.** Perceber que um endpoint está sob ataque é quase fácil:
basta contar quantas origens distintas chegaram nele na janela. O difícil é
**decidir quem bloquear sem bloquear os próprios usuários do serviço**. O artigo
trata essa decisão, o **escopo da mitigação**, como um **teste estatístico
calibrado**: só entra no escopo a impressão digital TLS cuja presença no alarme é
improvável sob o tráfego normal, num nível calibrado para um orçamento de falsos
alarmes.

**A proposta.** Um grafo de conhecimento (OWL) em que a sessão HTTP é entidade de
primeira classe, ligada a outras sessões por seis relações tipadas e ponderadas
pelo custo de evasão. Uma regra (SPARQL/SWRL) dispara o alarme, e o escopo vem de
um **teste binomial de enriquecimento** em relação a um perfil de tráfego normal.

**Os achados principais.**

1. Em campanhas furtivas geradas, a detecção por sessão fica no acaso (AUC ≈ 0,50)
   em quatro famílias de classificador. Atributos entre sessões chegam a 0,93–0,98,
   mas **só dentro de uma mesma estrutura de botnet**: treinado com 5 pilhas e
   testado com 25 ou 100, o modelo cai para 0,61 e 0,63; treinado com 25, vai a 0,48
   com 5 e 0,75 com 100.
2. O escopo "natural" (a impressão mais comum do agrupamento) é **prejudicial**: com
   a botnet em cinco ou mais pilhas TLS, bloqueia 0% do ataque e 39% do legítimo. O
   teste bloqueia 90% até 25 pilhas sem colateral observado. Um filtro de
   impressões **inéditas** faz o mesmo em pilhas novas (com 0,03% de colateral), mas
   não bloqueia nenhuma pilha que clientes reais compartilham, onde o teste bloqueia
   85% (a 2,23% de colateral).
3. Em oito dias de tráfego da CDN da Azion, **frotas legítimas impõem um piso de
   calibração**: a menor botnet que o teste binomial consegue apontar é 16% da
   janela do endpoint mais movimentado (7% com as frotas conhecidas isentas) e 4 a
   12 janelas inteiras nos endpoints pequenos. Uma **referência beta-binomial**, que
   modela as frotas, rebaixa o piso para 3% e para 0,9–2,8 janelas e dispensa a
   lista de frotas conhecidas.
4. Acima do piso, **todo escopo calibrado** bloqueia 67–71% de uma botnet do tamanho
   da janela do endpoint mais movimentado. A configuração binomial dispara em 0,1%
   das janelas limpas; a beta-binomial e um **z-score calibrado para o mesmo
   orçamento** disparam em 0,4% e bloqueiam tanto ou mais com 100 atacantes, com
   alarmes mais leves. A binomial paga a taxa menor de falsos alarmes com um piso
   mais alto. Num **dia novo analisado com o protocolo fixado de antemão**, a
   configuração binomial dá 2 falsos alarmes em 1.152 janelas (compatível,
   P = 0,27), nas mesmas janelas do z-score calibrado.
5. No **regime furtivo** (botnet de um décimo da janela), o escopo aponta a botnet
   em toda janela, mas o gatilho de volume deixa passar a maior parte dela (dispara
   em 0,7–42% das janelas, conforme o dia).
6. O que o grafo acrescenta é operacional e **medido**: a consulta de contagens é
   compilada a partir da ontologia e reproduz as exportações da Azion em dois dias;
   o STIX 2.1 exportado passa no validador em modo estrito.

**A honestidade como argumento.** O artigo diz o que o grafo *não* acrescenta (a
AUC e o gatilho), que um z-score calibrado compete com o teste acima do piso, que o
filtro de inéditas empata com o teste em pilhas geradas, que o modelo aprendido não
se transfere entre números de pilhas, onde o método não alcança (abaixo do piso),
que a decisão de ter um dia novo foi registrada antes de lê-lo e que a
beta-binomial foi construída depois disso (*post hoc*).

---

## 2. O que mudou nas últimas rodadas, e por quê

O artigo passou por várias rodadas de revisão independente. As duas últimas
(rodadas 7 e 8) foram leituras de conjunto comparadas com artigos excelentes do
NOMS, e as duas deram *weak reject* (a 7, no quartil inferior; a 8, no terceiro
quartil, com confiança 4 de 5). Os itens delas foram todos atacados, e é daí que
vem a versão atual. As rodadas, em ordem:

### Rodada 1 e 2: o método de contagem e a produção

- **Contar em origens, não em sessões.** Em produção uma "sessão" é uma conexão, e
  um cliente abre muitas (5,8 por cliente no endpoint de API). Contado em
  conexões, o escopo produzia filtro em 60,1% das janelas limpas. Agora Ω, o
  mínimo k_min e o teste contam **origens distintas** (endereços de origem).
- **Nível calibrado λ_e.** Frotas legítimas que entram em atividade ao mesmo tempo
  quebram a independência que o teste binomial assume. O nível do teste passou a
  ser calibrado por endpoint nos dias anteriores, como τ.
- **Tráfego de produção da Azion** (4 endpoints, anonimizados como E1–E4), com
  botnet injetada e protocolo *rolling* (cada dia testado com o que os dias
  anteriores ensinaram).
- **Fig. 1 redesenhada** em tons de cinza.

### Rodada 3: o enquadramento

- **O gatilho é volume.** Um limiar no número de origens distintas concorda com
  Ω ≥ τ em 86–99,6% das janelas.
- **Modelo aprendido com o perfil**, para a comparação ser justa: ele iguala ou
  supera a regra, mas precisa dos rótulos da própria campanha.
- **Condições (iv) e (v) da regra removidas** (nunca estavam ativas).

### Rodada 4 e itens 2 e 3

- A porta de origens e a união foram declaradas como escolhidas nos dias de teste.
- **Frotas conhecidas** (item 2): impressões que o teste aponta com frequência na
  calibração saem do escopo e da calibração do nível. A fração de 5% das janelas foi
  escolhida em três dias e testada em dois dias reservados.
- **O valor do grafo, medido** (item 3): pesos lidos da ontologia; um compilador
  gera o SQL de contagens a partir dela; no banco de logs da Azion, para 23/09, a
  consulta devolveu exatamente as origens e os pares /24 exportados nas 1.152
  janelas; o STIX 2.1 passou a ser válido em modo estrito.

### Rodada 6: coerência matemática e linguística

Contas, notação e texto conferidos no EN e no PT ("3,3 vezes" em vez de "três
vezes"; "pelo menos tantas janelas" em vez de "as mesmas"; a mediana dos alarmes;
S_W como único nome do conjunto de sessões ativas; a regra antes da construção).

### Rodada 7: o escopo como certificação

O revisor comparou o artigo com os melhores do NOMS e listou o que faltava. O que
foi feito, item a item:

- **Enquadramento.** Título novo (*Certified Scoping...*, trocado na rodada 8), resumo
  e contribuições contados como certificação: o teste certifica impressões, e isso
  tem um piso.
- **Produção no corpo.** Virou a seção V-D, com duas tabelas (IV e V). Antes estava
  no Apêndice E.
- **Linhas de base em pé de igualdade.** Dois z-scores novos com o limiar calibrado
  para o mesmo orçamento do teste (produzir filtro em no máximo 1% das janelas
  livres de ataque): um contra o perfil e um contra o próprio histórico de cada
  impressão. No sintético, o filtro de impressões inéditas entrou na Tabela III, e
  um modo "compartilhado" sorteia as pilhas da botnet da cauda do perfil, como a
  injeção de produção faz.
- **O piso de certificação** (hoje piso de calibração, Tabela IV), dito em III-G.
- **O WAF como verdade parcial**: a tabela do piso diz que fração dos clientes que o
  escopo bloquearia o WAF também bloqueou.
- **Um dia novo com o protocolo fixado de antemão** (25/09): configuração e métricas escritas antes de
  abrir o dia, com os *hashes* das exportações
  (`experiments/sprint-6-noms/results/fresh_day_protocol.md`). A consulta compilada
  da ontologia também rodou nesse dia.
- **O MLP corrigido.** O 0,235 abaixo do acaso era artefato: a parada antecipada
  avaliava um *holdout* por acurácia, e com 4,8% de ataques "tudo benigno" já é a
  melhor acurácia, então os pesos da época 7 eram restaurados. Sem parada
  antecipada, o MLP fica em 0,862 (K = 50) e 0,952 (K = 1000).
- **Fig. 2 (pipeline) removida**, a formulação simbólica fundida em III-F.
- **Trabalhos relacionados**: DOTS (RFC 8811 e 9132), D3FEND e detecção de bots por
  grafo (IM 2019).
- **Orçamento de páginas mantido**: 12 páginas, corpo em 8.
- **Passada final de estilo** no EN: resumo em 248 palavras; ponto e vírgula entre
  orações virou ponto; frases acima de 45 palavras divididas (de 11,5% para 2,4%).
- **Auditoria**: `make audit` confere 180 números e frases contra os resultados,
  com 0 divergências.
- **Versão em português** reconstruída na estrutura nova e revisada por duas
  leituras independentes: fidelidade ao inglês (26 correções, entre elas "85% das
  pilhas", que era "85% do ataque em pilhas compartilhadas") e língua (170
  correções: "dano colateral" por extenso, "em relação a" no lugar de "contra",
  palavras-chave do Algoritmo 1 em português, frases longas divididas).

**Resultados honestos da rodada 7** (o que não saiu a favor do método):

- No sintético, o filtro de inéditas **empata** com o teste até 25 pilhas, porque as
  pilhas geradas nunca aparecem no vocabulário benigno. A vantagem do teste só
  aparece em pilhas compartilhadas.
- Em produção, o z-score calibrado bloqueia **tanto ou mais** que o teste, a quatro
  vezes os falsos alarmes nos dias de teste (20 contra 5), e com alarmes mais
  leves. No dia novo, os dois dão os **mesmos 2 falsos alarmes, nas mesmas
  janelas**. A vantagem do teste é a taxa menor de falsos alarmes nos dias de teste
  e o piso calculável.
- No regime furtivo, o gargalo é o **gatilho**, não o escopo: com as frotas
  conhecidas, o escopo aponta a botnet de 0,1× em toda janela, mas o gatilho de
  origens só dispara em 0,7–42% delas. No dia novo, não disparou nenhuma vez.

### Rodada 8: o escopo como teste calibrado

Um revisor novo leu o artigo inteiro contra os melhores do NOMS e deu *weak reject*
(confiança 4 de 5, terceiro quartil). Cada afirmação dele foi conferida antes de
agir. O que mudou:

- **Enquadramento e título.** *Certified* virou *Calibrated*: o nível do teste é
  calibrado num orçamento de falsos alarmes, e num nível de 10⁻⁶⁰ o p-valor é um
  escore com limiar empírico, não uma certificação. O piso passou a se chamar
  **piso de calibração**.
- **Referência beta-binomial** (`--overdispersion`). As frotas tornam as contagens
  sobredispersas; uma beta-binomial ajustada por impressão digital (correlação φ
  dentro da janela, pelo método dos momentos) rebaixa o piso várias vezes (E1: 16%
  → 3% da janela; endpoints pequenos: 4–12 → 0,9–2,8 janelas), sobe o nível de E1
  para 7 × 10⁻⁵ e dispensa as frotas conhecidas (nenhuma se qualifica). O custo: 22
  falsos alarmes em 5.643 janelas (0,4%), o ponto de operação do z-score calibrado,
  e 1,3% no console, acima do orçamento (o z-score calibrado também passa, 1,1%). Foi
  construída **depois** de o dia novo ser lido: a configuração avaliada e registrada
  continua sendo a binomial.
- **Tabela III por endpoint.** Cada endpoint com binomial, beta-binomial e z-score
  calibrado, com botnets do tamanho da janela (1×) e de um décimo dela (0,1×), mais o
  agregado e o dia novo. Os números agregados de 100 e 1.000 atacantes foram para o
  texto. A tabela do piso (IV) ganhou as colunas da beta-binomial.
- **Generalização entre estruturas de botnet** (`cross_m_generalization.py`). O
  modelo aprendido (d) cai para 0,48–0,75 quando o número de pilhas muda, contra
  0,95–0,995 no mesmo número com outras sementes. Os testes usam metades disjuntas de
  sementes: com a mesma semente, o gerador repete as sessões benignas, e até (a)
  chegaria a 0,88–0,94 por memorização.
- **Erros corrigidos.** O d de Cohen de (d)−(a) é 22,3, não 22,4 (o valor é 22,349);
  o filtro de inéditas tem 0,03% de colateral, não zero; "o teste e o z-score
  coincidem" virou "no ponto de operação de"; "todo escopo calibrado bloqueia 71%"
  virou 67–71% (71% vale só em pilhas novas); a causa "a correlação é ajustada na
  própria amostra" saiu, porque o z-score calibrado também passa do orçamento no
  console; e o BCCC-cPacket-Cloud-DDoS-2024 aponta a fraca representação da camada de
  aplicação como deficiência dos 16 conjuntos que analisa (o texto anterior atribuía
  essa falha ao próprio BCCC, cujos 17 cenários de DDoS são todos baseados em TCP).
- **Artefato.** A ontologia perdeu os 10 indivíduos `DetectionRule`, teve os
  comentários traduzidos para o inglês, e `belongsToIdentity` virou `hasIdentity`;
  os nomes da III-B agora batem com a OWL (`LoginEndpoint`, `APIEndpoint`,
  `StaticEndpoint`, `Mitigation`). O protocolo do dia novo ganhou um adendo datado,
  sem alterar o texto registrado (`fresh_day_protocol_addendum.md`).
- **Trabalhos relacionados.** SynchroTrap (contas que agem em sincronia), Kill-Bots
  e Speak-up (ataques que imitam picos legítimos), URCA e Hamsa (derivar um filtro de
  um alarme) e a telemetria do DOTS (RFC 9244). Saíram três linhas da Tabela I, e as
  tabelas da ablação e do laboratório viraram texto.
- **Auditoria reescrita:** `make audit` confere 221 números e frases, com as tabelas
  identificadas pelos rótulos LaTeX, e 0 divergências. EN: 12 páginas, corpo em 8,
  resumo com 249 palavras.

---

## 3. Título e resumo (linhas 99–123)

**Título.** *Calibrated Scoping of Application-Layer DDoS Mitigation with a
Session-Centric Knowledge Graph.* As palavras que mandam são **calibrated
scoping**: a contribuição é o escopo da mitigação, decidido por um teste cujo nível
é calibrado num orçamento de falsos alarmes; o grafo é a camada onde a decisão é
derivada, especificada e exportada.

**O resumo, frase a frase** (249 palavras, dentro do limite de 250 do IEEE; o
`pdftotext` conta 250 porque separa "1 152" em duas):

1. *Uma campanha distribuída de Slow HTTP DoS mantém cada origem abaixo dos limiares
   por origem, e a mitigação passa a depender do escopo: quais clientes bloquear,
   poupando os usuários legítimos.* O problema, posto como decisão de gerência.
2. *Sobre um grafo de conhecimento centrado na sessão, um teste binomial de
   enriquecimento só bloqueia uma impressão TLS quando a sua fração nas origens do
   alarme é improvável sob o tráfego normal, num nível calibrado para um orçamento
   de falsos alarmes.* O método e o enquadramento numa frase.
3. *Em tráfego gerado, o escopo natural, a impressão mais comum do agrupamento,
   bloqueia 0% de uma botnet em cinco ou mais pilhas e 39% do tráfego legítimo.* O
   gancho.
4. *O teste bloqueia 90% até 25 pilhas sem colateral observado, como um filtro de
   impressões inéditas a 0,03%, e 85% a 2% de colateral em pilhas que clientes reais
   compartilham, onde esse filtro não bloqueia nenhuma.* A solução, com o empate dito
   e o colateral de cada um (85% é a fração do ataque, não das pilhas).
5. *Um modelo aprendido entre sessões (AUC 0,98) cai para 0,48–0,75 com outro número
   de pilhas.* Por que importa uma regra sem rótulos.
6. *Em oito dias de quatro endpoints de uma CDN, frotas de clientes sincronizadas
   impõem um piso de calibração: a menor botnet que a binomial aponta é 16% da janela
   do endpoint mais movimentado e 4–12 janelas nos pequenos.* O limite, medido.
7. *Uma beta-binomial que modela as frotas rebaixa o piso para 3% e 0,9–2,8 janelas,
   no ponto de operação de um z-score calibrado para o mesmo orçamento, 0,4% das
   janelas limpas.* A correção, com o seu preço.
8. *Todo escopo calibrado bloqueia 67–71% de uma botnet do tamanho da janela do
   endpoint mais movimentado.* Acima do piso, todos funcionam.
9. *Um dia novo, analisado como planejado de antemão, dá à binomial 2 falsos alarmes
   em 1.152 janelas.* A confirmação fora da amostra, da configuração registrada.
10. *A ontologia é compilada numa consulta de contagens que reproduz as contagens de
    origens e de pares /24 da operadora em dois dias, e o escopo sai em STIX 2.1.* O
    fecho, restrito ao verificado.

O regime furtivo saiu do resumo na rodada 8 (está em V-D e na conclusão).

---

## 4. I. Introdução (linhas 131–173)

**Parágrafo 1: o contexto.** Ataques de camada de aplicação crescem (HTTP/2 Rapid
Reset, CVE-2023-44487: 398 milhões de requisições por segundo; um pico de 201
milhões de ~20 mil máquinas; Cloudflare: 6.500 ataques hipervolumétricos no 2º
trimestre de 2025). Defesas volumétricas absorvem o grande; o difícil é o lento e
distribuído.

**Parágrafo 2: o que resta de discriminativo.** O que sobra está **entre** sessões:
a mesma impressão digital em muitas origens, convergindo num endpoint. Por isso o
problema é de **gerência de rede e serviço** (NOMS): agir exige decidir quem, com
que evidência, com que filtro.

**Parágrafo 3: as três lacunas.** A meta-análise de 75 estudos: 47% dos detectores
tiram atributos de sessões, mas as achatam num vetor. O KLAGE usa grafo, mas
(1) raciocina sobre nós de rede; (2) a coordenação fica implícita em *embeddings*;
(3) para num relatório, sem escopo de mitigação.

**Parágrafo 4: o enquadramento e as quatro contribuições.** O escopo é tratado como
um teste estatístico calibrado, sobre um grafo de sessões HTTP.

- **(i)** O escopo natural bloqueia usuários e nenhum atacante quando a botnet se
  espalha; o escopo por enriquecimento, em relação a um perfil livre de ataque,
  bloqueia o ataque, inclusive nas pilhas compartilhadas, que o filtro de inéditas
  perde, e dispensa rótulos, enquanto um modelo aprendido falha com outro número de
  pilhas.
- **(ii)** Em oito dias de CDN, medimos até onde o escopo calibrado alcança: o piso
  imposto pelas frotas, a referência beta-binomial que o rebaixa várias vezes, e o
  regime furtivo em que o escopo aponta a botnet e o gatilho a deixa passar. Mais as
  linhas de base calibradas no mesmo orçamento e o dia novo com a configuração
  fixada de antemão.
- **(iii)** A ontologia OWL com seis sub-propriedades (três exercitadas), da qual a
  consulta de contagens é compilada; em dois dias de produção ela reproduz as
  exportações janela a janela; o escopo sai em STIX 2.1.
- **(iv)** O colateral reportado como taxa de falsos positivos do filtro, em janelas
  limpas e de ataque.

**Pergunta provável:** "Por que isso é NOMS e não segurança pura?" Porque a
contribuição é a decisão operacional (o escopo, o seu piso, o custo em usuários
legítimos, a exportação para SOAR e DOTS), medida em tráfego de produção.

---

## 5. II. Trabalhos relacionados (linhas 174–202, Tabela I)

**Tabela I** compara quatro trabalhos (PCA sobre sessões, o supervisionado de Kemp,
os sinais JA4 da Cloudflare e o KLAGE) com este em quatro dimensões: unidade de
raciocínio, relação entre sessões, forma da explicação, e se há escopo de
mitigação e colateral. Só este trabalho tem todas as colunas preenchidas. Na
rodada 8 saíram as linhas de três trabalhos que continuam citados no texto.

- **Grafos de conhecimento em segurança:** a primeira onda era estática (CVE,
  relatórios). O **D3FEND** (MITRE) é um grafo OWL de contramedidas mapeado ao
  ATT&CK, também estático. Uma revisão diz que ainda não se sabe usar KG em
  problemas industriais reais. O KLAGE é o mais próximo (grafo a partir de logs).
- **Modelos aprendidos em tarefas vizinhas:** dependências entre dispositivos,
  sequências de ataque, e **detecção de bots por grafo** (IM 2019: classifica hosts
  de um grafo de fluxos por grau, agrupamento e centralidade). Os três operam sobre
  entidades de rede e nenhum deriva escopo. No nível de contas, o **SynchroTrap**
  encontra coordenação agrupando contas que agem em sincronia.
- **Detecção de DDoS L7:** perfilamento estatístico (PCA) e aprendizado
  supervisionado. Nenhum mantém relação entre sessões. **Kill-Bots** e **Speak-up**
  defendem de ataques que imitam picos legítimos admitindo clientes que resolvem um
  desafio ou gastam banda, e medem o serviço que os legítimos conservam. **URCA**
  (extração de anomalias) e **Hamsa** (assinaturas conferidas em tráfego normal)
  derivam um filtro de um alarme, mas sobre atributos de fluxo ou de *payload*, sem
  impressões de cliente.
- **Modelagem de sessão:** nenhum dos 75 estudos mantém a sessão como objeto.
  Plataformas industriais (sinais por JA4) são proprietárias.
- **DOTS (IETF):** o canal de sinalização (RFC 9132, arquitetura na RFC 8811) leva
  um pedido de mitigação do domínio atacado ao mitigador, com o escopo dado pelos
  recursos atacados; o canal de dados (RFC 8783) instala filtros sobre campos de
  rede e de transporte; a telemetria (RFC 9244) reporta os maiores emissores por
  prefixo de origem. **Nenhum atributo expressa uma impressão digital de cliente da
  camada de aplicação**, como o JA4. Isso reaparece na Discussão: pelo DOTS, o
  escopo se alargaria para o endpoint ou para prefixos de endereço.
- **Fronteira:** nenhum trabalho tem, junto, sessão como unidade, relações
  explícitas e escopo derivado com colateral.

---

## 6. III. O grafo de conhecimento centrado na sessão (linhas 203–354)

### Fig. 1 (a ontologia)

Três colunas: **Session** (a `ApplicationSession` ligada a `Identity`, `Endpoint`,
`IPAddress/ASN`, `Behavior`); **relatedTo** (sessões ligadas pelas seis
sub-relações, com a espessura seguindo o peso e um traço por sub-relação);
**Verdict** (`CoordinatedHTTPFlood` → cadeia de evidência → `CourseOfAction`). A
convergência de endpoint liga todos os pares de sessões do endpoint; só alguns
estão desenhados.

### III-A. Grafos de conhecimento (linha 217)

- **RDF:** fatos como triplas ⟨sujeito, predicado, objeto⟩.
- **OWL 2 RL:** perfil com inferência polinomial por encadeamento para frente, o que
  torna viável materializar por janela (OWL 2 DL não é).
- **SWRL:** regras de Horn. **SPARQL:** consulta e agrega.
- **JA4:** *hash* do *ClientHello* do TLS, identifica a pilha TLS do cliente e
  sobrevive à rotação de IP.

### III-B. A ontologia (linha 230)

Classe central `ApplicationSession`, ligada por `hasIdentity` a uma `Identity`,
`originatesFrom` ao `IPAddress`, `targets` a um `Endpoint` (`LoginEndpoint`,
`APIEndpoint`, `StaticEndpoint`), `exhibitsBehavior` a um perfil e `mitigatedBy` a
uma `Mitigation` (`RateLimitPolicy`, `ChallengeResponse`, `WAFRule`), cujo escopo a
cadeia de evidência carrega. Desde a rodada 8 os nomes batem com a OWL.
Hierarquia: `ApplicationLayerAttack` → `SlowHTTPDoSFamily` →
`ConnectionExhaustionAttack` e `CoordinatedHTTPFlood` (a classe que a regra
deriva). Alinhada a STIX 2.1 e ATT&CK.

### III-C. Modelo de ameaça (linha 245)

O defensor vê, por requisição, JA4, origem, endpoint, tempo e identidade, e pode
perfilar o tráfego normal. O atacante controla K dispositivos e pode fazer cada
sessão estatisticamente igual a uma legítima. O dano é capacidade esgotada. O JA4
é difícil de mudar porque vem da biblioteca TLS do dispositivo (linhagem Mirai).
Bots que imitam navegador ficam fora do modelo e são avaliados como fronteira.

### III-D. A família `relatedTo` ponderada (linha 266)

Seis sub-propriedades de `relatedTo`, cada uma com `coordinationWeight` w_i;
**três delas são exercitadas** (TLS, endpoint, rede). O texto justifica só as duas
pontas: a pilha TLS é fixada pela biblioteca de cada dispositivo, e o JA4 ordena as
extensões, então sobrevive à aleatorização que quebra o JA3; as botnets se espalham
por prefixos e o NAT de operadora torna o /24 um discriminador pobre, então a
proximidade de rede é o elo mais fraco. Os pesos usados: TLS 1,0, endpoint 0,6,
rede 0,3. O Apêndice B **corrobora a ordem**, não os valores absolutos.

### III-E. A regra de detecção (linhas 277–300)

> Ω(S) = Σ_i w_i · |E_i(S)|

E_i(S) é o conjunto de **pares de origens distintas** ligadas pela sub-relação i.
A regra `CoordinatedHTTPFlood` vale quando existe S com (i) ao menos k_min = 5
origens, (ii) todas as sessões visando o mesmo endpoint e (iii) Ω(S) ≥ τ_cluster.
Só **mitiga** quando o teste de enriquecimento aponta uma impressão.

**"Na escala da janela, Ω é volume."** O termo de endpoint, 0,6 · C(n, 2), é 91%
de Ω na campanha da Listagem 2. Por isso um limiar em origens distintas, calibrado
como τ, serve de gatilho ao menos tão bem, e o discriminador vem do teste.

### III-F. Construção em tempo de execução (linha 301)

Janela deslizante W = 5 min. JA4 exato, endpoint e prefixo são **relações de
equivalência**: particionam S em classes, e |E_i(S)| = Σ_k C(n_k, 2). Admitir uma
sessão é inserir sua origem numa classe (tempo constante), e Ω não precisa de
aresta de par. Só as relações não transitivas comparam pares. **A formulação
simbólica agora mora aqui:** o SWRL escreve cada sub-relação como regra de Horn (o
DTW entra como comparação embutida com um limiar), e, como o SWRL não soma, uma
consulta SPARQL agrega os tamanhos das classes com os pesos lidos das anotações
(Listagem 1).

### III-G. Cadeia de evidência e escopo derivado (linhas 319–354)

Quando a regra dispara, sai a cadeia de evidência em JSON-LD e STIX 2.1.

**Por que o escopo por frequência falha:** a impressão mais comum do agrupamento é
a da população legítima.

**O teste de enriquecimento** (exemplo na seção 16). Admite toda impressão f que
seja **enriquecida**, c(f)/n ≥ ρ · b(f), com ρ = 3, e **improvável sob a referência**,
P[X ≥ c(f)] < λ_e / |F|, com X ~ Bin(n, b(f)).

**λ_e calibrado:** o maior valor até 0,01 em que o escopo produz filtro em no
máximo 1% das janelas sem ataque.

**O piso (frase nova):** entre n origens, o teste só aponta uma pilha a partir da
menor contagem c com P[X ≥ c] < λ_e/|F|. Quanto menor o nível, maior essa contagem
e maior a menor botnet que ele consegue apontar. É o **piso de calibração**,
medido na seção V-D.

**A variante (frase nova da rodada 8):** como as frotas também tornam as contagens
sobredispersas, o artigo avalia uma variante cuja referência é uma beta-binomial
ajustada por impressão nas janelas de calibração (seção 16).

**Sem rótulos:** se o adversário se esconde numa impressão popular, nada fica
enriquecido e o sistema recusa o escopo.

---

## 7. IV. Metodologia de avaliação (linhas 355–437)

**Cada fonte responde a uma pergunta:** o gerador calibrado (mecanismo sob
campanhas controladas), as capturas de laboratório (ataques convencionais e
KLAGE), oito dias de produção (falsos alarmes reais e detecção de botnet
injetada) **e um nono dia analisado com todas as escolhas fixadas de antemão**.

**Cenários por K:** reportamos K = 50 (botnet pequena, cada origem dentro do seu
limite de taxa) e K = 1000 (campanha espalhada por centenas de ASNs e prefixos).
Cada campanha é dividida 70/30 entre sessões de treino e de teste.

**O gerador.** Popularidade das impressões benignas em Zipf de expoente α (medida
na Azion: 6,33 M requisições, 495 impressões, top-1 38,4%, top-10 93,8%; α = 1,5 e
2,0 cercam a curva; canônico 1,5). Composição da botnet: 90% em M pilhas (M = 25
canônico), o resto em impressões únicas. Modo adversarial: a botnet usa as
impressões benignas mais comuns. Sessões benignas calibradas no CICIDS2017 (KS:
D = 0,003 e 0,002, p > 0,8).

**Linhas de base de detecção:** RF forte (8–9 atributos), repetida com HGB, MLP e
regressão logística; três acadêmicas reimplementadas.

**Configurações da ablação:** (a) ML sem ontologia; (b) ontologia sem sub-relações;
(c) só proximidade de rede; (d) representação completa, como atributos.

**Linhas de base de escopo (parágrafo novo):**

- a impressão **modal** do agrupamento;
- o filtro de **inéditas**: impressões ausentes do perfil e vistas em ao menos
  k_min origens;
- o **z-score** por impressão contra o perfil, z > 3, sem calibração;
- em produção, dois z-scores **calibrados** para o orçamento do teste: o mesmo
  z-score contra o perfil e um z-score de cada impressão contra o **próprio
  histórico** de calibração;
- o modo **compartilhado** no sintético: as pilhas da botnet sorteadas do perfil
  fora das dez impressões mais comuns, como na injeção de produção.

**Métricas:** AUC, F1, precisão, revocação e **dano colateral** (a taxa de falsos
positivos do filtro que o operador implantaria).

---

## 8. V-A. Ablação (linhas 443–479, sem tabela)

A tabela da ablação saiu na rodada 8, para dar lugar à Tabela III por endpoint. Os
números continuam os mesmos e estão no texto:

| Configuração | K = 50 | K = 1000 |
|---|---|---|
| (a) ML por sessão forte | 0,498 | 0,503 |
| (b) ontologia sem relatedBy | 0,500 | 0,502 |
| (c) só NetworkProximity | 0,499 | 0,659 |
| **(d) entre sessões** | **0,927** | **0,982** |
| HGB (a / d) | 0,502 / 0,921 | 0,501 / 0,990 |
| **MLP (a / d)** | **0,493 / 0,862** | **0,494 / 0,952** |
| Regressão logística (a / d) | 0,488 / 0,873 | 0,495 / 0,799 |
| Três linhas de base acadêmicas | 0,499–0,518 | 0,495–0,509 |

**Leitura:**

- Por sessão, tudo fica no acaso (0,488–0,503 em todas as famílias; as acadêmicas
  entre 0,495 e 0,518). O colapso está na **representação**.
- **Wilcoxon:** (d)−(c) e (d)−(a) significativos em K = 1000 (p_Bonf = 7,5 × 10⁻⁹,
  d de Cohen 13,5 e **22,3**; até a rodada 7 o artigo dizia 22,4, mas o valor é
  22,349). Uma diferença estável entre sorteios de um gerador.
- **Parágrafo novo da rodada 8: a separabilidade não se transfere.** Com M pilhas, a
  evidência entre sessões é **não monotônica** (um atacante divide a impressão com
  algumas dezenas de pares; um legítimo da cabeça, com centenas). Árvores recortam a
  faixa do meio (0,92–0,99), o MLP chega a 0,86 e 0,95, e a regressão logística,
  monotônica em cada atributo, fica em 0,87 e 0,80. **Treinado com 5 pilhas e
  testado com 25 ou 100, (d) cai para 0,61 e 0,63; treinado com 25 e testado com 5,
  para 0,48** (e 0,75 com 100, no Apêndice C): a floresta aprende a faixa que um M
  produz. A regra não usa rótulos, lê um perfil de tráfego normal e mantém cerca de
  90% até 25 pilhas.
- **O cuidado com o vazamento.** Para uma mesma semente, o gerador sorteia todas as
  sessões benignas antes de qualquer coisa que dependa de M, então a tabela benigna é
  idêntica em M = 5, 25 e 100. Um teste com a mesma semente mediria memorização (até
  (a), sem nenhum atributo entre sessões, chegaria a 0,88–0,94). Por isso o treino e o
  teste usam metades disjuntas das sementes.
- **Laboratório:** no CIC-IoT2023, um classificador forte por sessão já chega a F1
  0,900 e a representação entre sessões a 0,911, ambos acima do 0,841 do KLAGE, numa
  comparação não controlada (Apêndice C).

---

## 9. V-B. A regra como detector (linhas 480–530, Tabela II)

Aqui não há classificador: as sessões que casam com o escopo **são** o conjunto
sinalizado, e o classificador é forçado ao ponto de operação da regra.

| Cenário | Regra | FPR | F1 | **Inéditas** | Aprendido (d) | + perfil |
|---|---|---|---|---|---|---|
| M = 1 | 89,8% | 0,00% | 0,946 | 89,8% | 91,7% | 85,9% |
| M = 5 | 90,0% | 0,00% | 0,948 | 90,0% | 88,6% | 91,7% |
| M = 25 | 90,3% | 0,00% | 0,949 | 90,3% | 36,4% | 87,4% |
| M = 100 | 38,6% | 0,00% | 0,556 | 88,1% | 17,6% | 86,9% |
| **M = 25, compartilhada** | **85,4%** | **2,23%** | **0,910** | **0,0%** | – | – |
| M = 25, adversarial | 30,4% | 3,78% | 0,452 | 0,0% | 7,8% | 6,6% |

**Leitura honesta:**

- Contra botnet monolítica ou pouco fragmentada, o modelo aprendido compete.
- Com 25 pilhas, a regra abre vantagem sobre o modelo sem perfil (90,3% contra
  36,4%, e 66,8% com 1% de FPR). Com o perfil como atributos, o modelo iguala (87,4%)
  e supera em 100 pilhas (86,9% contra 38,6%), mas **treina com os rótulos da
  campanha**.
- **O filtro de inéditas empata com a regra até 25 pilhas** (as pilhas geradas nunca
  estão no vocabulário benigno) e ganha em 100 pilhas (88,1%). **Mas em pilhas
  compartilhadas não bloqueia nenhuma**, onde a regra bloqueia 85,4% a 2,23% de
  colateral, e um z-score sem calibração 89,9% a 3,37%.
- A FPR do filtro de inéditas é de no máximo 0,03% (por isso o resumo diz "a 0,03%").

**Por janela (Tabela V, Apêndice E):** Ω ≥ τ sozinho dispara em 78–86% das
janelas de ataque, 0,6% das limpas e **80–100% dos flash crowds**. Exigir que o
teste aponte uma impressão elimina todo falso alarme e mantém a detecção.

---

## 10. V-C. Dano colateral (linhas 531–568, Fig. 2)

**Fig. 2** agora tem três escopos (frequência, inéditas, enriquecimento) em seis
grupos, incluindo "M = 25, compartilhada".

- **M = 1:** os dois primeiros concordam, 89,8% sem colateral. Um limite global
  desconectaria todo usuário legítimo.
- **A partir de 5 pilhas:** o escopo por frequência **inverte**: 0,0% do ataque,
  39,0% do legítimo (61,1% com α = 2,0).
- **Enriquecimento:** 90,0% e 90,3% em M = 5 e 25, **sem colateral observado**. O
  filtro de inéditas repete isso nas pilhas geradas e perde nas compartilhadas.
  M = 100: 38,6%, sem colateral; um perfil de 30 períodos restaura 89,6%.
- **Dois limites:** o modo adversarial (30,4% a 3,78% de colateral; com ρ mais
  estrito, o escopo se recusa) e o perfil (deriva moderada tolerável; perfil plano
  leva o colateral a 77,6%). **Perfil fresco e amplo é requisito de implantação.**

---

## 11. V-D. Tráfego de produção (linhas 569–710, Tabelas III e IV)

É a seção de produção do corpo. Seis parágrafos em negrito, cada um com uma
afirmação. Desde a rodada 8 as tabelas são por endpoint.

### Tabela III (o escopo em produção, por endpoint, em %)

| Endpoint | Escopo | FA | Col. | Flash | Novas 0,1× | Novas 1× | Comp. 0,1× | Comp. 1× |
|---|---|---|---|---|---|---|---|---|
| E1 | binomial | 0,0 | – | 0,0 | 11,8 | 70,8 | 7,7 | 68,6 |
| E1 | beta-binomial | 0,1 | 0,2 | 0,1 | 11,9 | 70,8 | 10,0 | 67,8 |
| E1 | z-score calibrado | 0,2 | 0,2 | 0,3 | 11,9 | 70,8 | 9,0 | 67,1 |
| E2 | binomial | 0,3 | 31,4 | 5,4 | 0,0 | 5,0 | 0,0 | 0,0 |
| E2 | beta-binomial | 1,3 | 10,7 | 13,5 | 0,7 | 25,9 | 0,2 | 13,2 |
| E2 | z-score calibrado | 1,1 | 11,0 | 14,2 | 0,1 | 18,3 | 0,0 | 2,5 |
| E3 | binomial | 0,1 | 48,5 | 11,0 | 0,0 | 1,9 | 0,0 | 0,5 |
| E3 | beta-binomial | 0,0 | – | 6,6 | 0,3 | 22,7 | 0,3 | 13,9 |
| E3 | z-score calibrado | 0,1 | 48,5 | 2,0 | 0,3 | 20,3 | 0,0 | 4,8 |
| E4 | binomial | 0,0 | – | 2,2 | 0,1 | 2,1 | 0,0 | 1,5 |
| E4 | beta-binomial | 0,1 | 3,5 | 0,9 | 0,1 | 6,0 | 0,1 | 3,9 |
| E4 | z-score calibrado | 0,0 | – | 0,3 | 0,1 | 6,0 | 0,0 | 1,2 |
| Todos | binomial | 0,1 | 32,9 | 4,6 | 3,0 | 19,9 | 1,9 | 17,6 |
| Todos | beta-binomial | 0,4 | 10,5 | 5,3 | 3,3 | 31,4 | 2,7 | 24,7 |
| Todos | z-score calibrado | 0,4 | 10,8 | 4,2 | 3,1 | 28,8 | 2,3 | 18,9 |
| Dia novo | regra básica (Ω ≥ τ) | 0,2 | 41,2 | 1,0 | 0,0 | 17,3 | 0,0 | 16,6 |
| Dia novo | binomial | 0,2 | 41,2 | 1,1 | 0,0 | 20,4 | 0,0 | 17,0 |
| Dia novo | beta-binomial* | 0,0 | – | 4,3 | 0,0 | 32,5 | 0,0 | 26,2 |
| Dia novo | z-score calibrado | 0,2 | 41,2 | 0,4 | 0,0 | 31,4 | 0,0 | 19,7 |

Como ler: **binomial** é a configuração avaliada (teste de enriquecimento unido ao
filtro de inéditas, com as frotas conhecidas isentas); **beta-binomial** é o mesmo
sobre a referência beta-binomial (\* = construída depois de o dia novo ser lido);
**z-score calibrado** tem o limiar no mesmo orçamento; todos sob o gatilho de origens
distintas. A **regra básica** usa o gatilho Ω ≥ τ, a referência do protocolo. **FA**
é a fração das janelas limpas (5.643 nos dias de teste, 1.152 no dia novo) em que o
escopo produz filtro; **Col.** é a fração mediana dos clientes que esses filtros
bloqueiam; **Flash** é FA com um pico legítimo de 100 usuários; as colunas de
bloqueio são a fração média de uma botnet de 25 pilhas do tamanho da janela mediana
do endpoint (1×) ou de um décimo dela (0,1×), em pilhas novas ou compartilhadas. As
impressões únicas limitam o bloqueio a cerca de 90%.

### Tabela IV (piso de calibração e WAF)

| Endpoint | Origens/janela | λ_e bin. | λ_e beta | Piso bin. | + frotas | Piso beta | WAF |
|---|---|---|---|---|---|---|---|
| E1, beacons de RUM | > 10³ | 10⁻⁶⁰ | 10⁻⁴ | 0,16 | 0,07 | 0,03 | – |
| E2, console web | < 10² | 10⁻⁷³ | 10⁻² | 11,6 | 11,6 | 0,90 | 1,5% |
| E3, API | < 10² | 10⁻¹⁴ | 10⁻² | 4,1 | 3,5 | 1,4 | 84% |
| E4, SSO | < 10² | 10⁻⁴ | 10⁻² | 4,2 | 4,2 | 2,8 | 96% |

O piso é a menor botnet de 25 pilhas novas cujas pilhas o nível consegue apontar,
como múltiplo da janela mediana, em mediana sobre os cinco dias de teste. WAF é a
fração dos clientes que o escopo bloquearia e que o WAF também bloqueou.

### Os parágrafos

1. **Protocolo e contagem.** Cada um dos cinco últimos dias é testado com perfil,
   limiares e nível dos dias anteriores. Em conexões, o escopo produz filtro em
   60,1% das janelas limpas; em origens, 26,9% no nível nominal. Calibrar λ_e leva a
   regra a 0,2%, e o gatilho de origens reduz os falsos alarmes à metade (6 contra
   14) sem perder detecção.
2. **As frotas impõem um piso de calibração.** Em E1, λ_e vai a 10⁻⁶⁰, e o teste
   binomial só aponta uma pilha a partir de 15 a 18 origens: a menor botnet de 25
   pilhas é 16% da janela. Com as cinco ou seis frotas conhecidas isentas do escopo e
   da calibração, λ_e sobe para ~10⁻²¹ e o piso cai para 7%; a isenção é uma lista de
   exceções (um bot com a impressão de uma frota não entra no escopo). Nos três
   endpoints pequenos, o piso é 4 a 12 vezes a janela inteira.
3. **Uma referência que modela as frotas rebaixa o piso** (novo na rodada 8). Com a
   beta-binomial, o nível de E1 sobe para 7 × 10⁻⁵ (três origens bastam para apontar
   uma pilha) e o dos demais vai ao teto de 0,01. O piso cai para 3% da janela de E1
   e para 0,9–2,8 janelas nos outros, e nenhuma impressão se qualifica como frota
   conhecida, então a lista de exceções deixa de ser necessária. No console, os
   falsos alarmes dos dias de teste passam do orçamento (1,3%), como os do z-score
   calibrado (1,1%).
4. **Acima do piso, um z-score calibrado iguala o teste.** Em E1, todo escopo
   calibrado bloqueia 67–71% de uma botnet do tamanho da janela típica e 8–12% de uma
   com um décimo (para a qual o gatilho raramente dispara). Nos endpoints pequenos,
   uma botnet do tamanho da janela fica abaixo do piso da binomial, que bloqueia 2–5%
   dela em pilhas novas, enquanto a beta-binomial e o z-score calibrado bloqueiam
   6–26%. No agregado, a binomial dispara em 0,1% (5 de 5.643) e bloqueia 38,4% e
   77,7% de 100 e 1.000 atacantes em pilhas novas, 21,7% e 63,3% em compartilhadas,
   onde o filtro de inéditas sozinho não bloqueia nada. O z-score calibrado e a
   beta-binomial disparam em 0,4% (20 e 22 janelas) e bloqueiam tanto ou mais com
   100 atacantes (54,7% e 59,8% em pilhas novas; 23,7% e 40,5% em compartilhadas),
   com alarmes mais leves (10,8% e 10,5% dos clientes, contra 32,9%). **A binomial
   paga a taxa menor de falsos alarmes com um piso mais alto.** Em janelas de ataque,
   todo escopo calibrado bloqueia mediana de 0% dos legítimos.
5. **No regime furtivo, o gatilho deixa a botnet passar.** Botnet de 0,1× em E1:
   acima do piso com frotas conhecidas, o escopo a aponta em toda janela (pilhas
   novas e compartilhadas), mas o gatilho de origens dispara em só 0,7–42% das
   janelas, conforme o dia, e só 11,8% dos atacantes em pilhas novas são bloqueados.
   Um gatilho só pelo escopo, examinado a posteriori, bloquearia 89,6% (novas) e
   61,1% (compartilhadas) a 1,0% das janelas limpas de E1, e 90,0% e 78,3% a 2,1% com
   a beta-binomial.
6. **O dia novo é compatível com a taxa de falsos alarmes.** 25/09, exportado depois
   de todas as escolhas, com protocolo registrado antes: a configuração binomial dá 2
   falsos alarmes em 1.152 janelas, consistente com os dias de teste (P = 0,27). Os
   dois caem no console web e bloqueiam mediana de 41,2% dos clientes. A
   configuração bloqueia 38,9% e 73,4% em pilhas novas, 21,5% e 60,9% em
   compartilhadas; a 0,1× o gatilho não disparou nenhuma vez. O z-score calibrado e a
   regra básica (a referência do protocolo) dispararam **nas mesmas duas janelas**, e
   o z-score bloqueou mais com 100 atacantes (58,3% e 26,7%); nos dias de teste, ele
   compartilhou 4 dos 5 falsos alarmes do teste. A beta-binomial, construída depois
   da leitura do dia, não deu nenhum. A consulta compilada devolveu as origens e os
   pares /24 iguais aos da exportação nas 1.152 janelas.

A concordância com o WAF e as outras linhas de base (z-score sem calibração e o de
histórico próprio) foram para o Apêndice E na rodada 8.

**Pergunta provável:** "Então para que o teste, se o z-score calibrado faz o
mesmo?" Veja a seção 18.

---

## 12. V-E. Custo e a janela W (linhas 711–718)

Com as relações de igualdade como classes, a admissão fica constante em ~0,37 µs
por sessão, e a camada simbólica linear: 26,4 s para 100 mil sessões, contra 52,8 s
com arestas de par para mil. O valor de Ω cresce com o quadrado do agrupamento;
calculá-lo, não. A AUC de (d) é plana numa faixa de 30× de W, porque a campanha
gerada forma um único agrupamento em qualquer W (1.977 a 1.998 sessões); é uma
propriedade do gerador. A regra rodou com
W = 300 s.

---

## 13. VI. Discussão e limitações (linhas 719–755)

- **O ganho depende do regime:** limiares por IP resolvem origem única; um
  classificador forte por sessão chega a AUC ≥ 0,98 em datasets públicos. Só o
  distribuído **e** furtivo precisa de evidência entre sessões, e **só botnets acima
  do piso de calibração, que o modelo de referência determina, podem ter escopo por
  impressão**. Abaixo dele, o recurso é limite de taxa ou desafio.
- **Cada avaliação estabelece uma coisa:** o gerador mostra o mecanismo; como suas
  pilhas nunca estão no vocabulário benigno, o filtro de inéditas empata ali, e um
  modelo ajustado a um número de pilhas não se transfere para outro. A produção mede
  falsos alarmes reais e detecção de botnet injetada, em nove dias de uma operadora.
  Não há campanha furtiva capturada.
- **Dependência de um discriminador de peso alto:** com o JA4 aleatorizado, a AUC(d)
  cai de 1,00 para ~0,74 e o escopo perde o discriminador, enquanto o gatilho de
  volume sobrevive. Um bot que imita o JA4 de navegador o derrota. O ECH esconde o
  JA4 de quem observa no caminho, mas não de quem termina o TLS (o defensor do
  modelo). A versão anterior do artigo dizia, errado, que o ECH poderia esconder o
  JA4 do defensor.
- **O que o grafo acrescenta:**
  - *Não acrescenta:* a AUC (um modelo linear sobre os atributos chega a 0,799) nem
    o gatilho; o teste do escopo é estatístico.
  - *Acrescenta, medido:* a ontologia é a especificação que o operador implanta (o
    que cada relação de igualdade iguala, seu peso, a unidade de contagem); a
    consulta compilada dela devolve as contagens exportadas em todas as janelas de
    **dois** dias de produção; um sinal novo custa 4 triplas e nenhum código; o STIX
    2.1 passa no validador em modo estrito e atravessa o servidor TAXII de
    referência (exceto a definição de extensão).
  - *Lacuna de padrão:* o importador do MISP descarta os JA4, e os filtros do DOTS
    só atuam sobre campos de rede e de transporte; os dois alargariam o escopo para o
    endpoint ou para prefixos. A mitigação por impressão precisa de uma propriedade
    padrão para JA4.
  - Se a derivação, que torna o veredicto inspecionável, encurta a decisão de um
    analista não foi testado.

---

## 14. VII. Conclusão (linhas 756–771)

Um parágrafo só, desde a rodada 8. O escopo tratado como teste calibrado. Por sessão
no acaso; entre sessões 0,93–0,98, **só dentro de uma estrutura de botnet**. O
escopo por frequência seleciona uma impressão legítima; o teste bloqueia 90% até 25
pilhas sem colateral observado nem rótulo e inclui no escopo as pilhas
compartilhadas, que o filtro de inéditas não consegue. Em produção, as frotas impõem
o piso: 16% da janela de E1 sob a binomial e 3% sob a beta-binomial, no ponto de
operação de um z-score calibrado. O dia novo é compatível com a taxa de falsos
alarmes da configuração binomial, e no regime furtivo o escopo aponta a botnet que o
gatilho, em sua maior parte, deixa passar. **Próximos passos:** gatilhos acionados
pelo escopo, HTTP/2 e uma campanha furtiva capturada (a referência com
sobredispersão, que era trabalho futuro, entrou nesta rodada).

**Agradecimento:** Azion autorizou a medição de impressões digitais e as
estatísticas agregadas, exportadas sem endereços, portas ou URIs.

---

## 15. Apêndices A a F

### A. Construção e instanciação das sub-relações (linhas 781–851)

**Algoritmo 1:** para cada requisição, resolve sessão, identidade e endpoint; liga
no grafo; instancia cada sub-relação contra as sessões ativas; expurga o que sai da
janela. Os procedimentos das seis sub-relações estão num só parágrafo: TLS
(igualdade exata ou variante próxima), endpoint (normalização de caminho), rede
(/24, /48 ou ASN), e, numa frase só, as três especificadas mas não exercitadas:
identidade (cookie, token ou usuário; JWT pelo `sub`), temporal (DTW normalizado ≤
τ_DTW, com FastDTW) e carga útil (cosseno). **Listagem 1:** a regra
SWRL e a agregação SPARQL.

### B. Calibração dos pesos (linhas 852–868)

Em laboratório, a otimização inverte o sinal do TLS (baixa diversidade de JA4). No
cenário realista, grade {0,3…1,0}³ (125 combinações, 60 cenários, 91.500 sessões):
melhor vetor (1,0; 0,3; 0,3); só o TLS discrimina sozinho (AUC 0,93 contra 0,50 e
0,58). Os pesos do artigo (1,0; 0,6; 0,3) dão a mesma AUC ótima 0,943 e são
insensíveis a ±20%. A calibração **corrobora a ordem**; os pesos médio e baixo não
são identificáveis separadamente.

### C. Limitações adicionais (linhas 869–902)

Instrumentação de sessão (CGN subconta, IPv6 com endereços de privacidade
sobreconta); custo de manutenção do grafo (números simbólicos são limite superior;
a produção foi *offline*); cobertura (HTTP/2, outros protocolos; só 3 das 6
sub-relações exercitadas); amplitude de datasets (nenhuma captura independente do
regime furtivo).

- **Laboratório e KLAGE** (a Tabela VI saiu na rodada 8; os números estão no texto):
  no `DDoS Slowloris` do CIC-IoT2023, os agrupamentos de ataque concentram sete
  origens num de 143 prefixos /24; (a) enxuta, 3 atributos: F1 0,179 (AUC 0,551);
  forte, 8 atributos: 0,900 (AUC 0,987); (d): 0,911 (AUC 0,982). O KLAGE publica
  0,841: comparação favorável mas não controlada, porque a nossa linha de base forte
  também o supera e o código deles parte de um grafo de construção não publicada,
  sem pesos.
- **Representação aprendida** (parágrafo novo): (d) é treinada e testada numa
  divisão 70/30 de uma campanha; treinada em 25 pilhas e testada em 100, AUC 0,75,
  contra 0,95–0,995 no mesmo M com outras sementes; sementes disjuntas, porque com a
  mesma semente (a) chegaria a 0,88–0,94 por memorização.
- **Validação da explicação** sem estudo com usuários.

### D. Modelo de custo e sensibilidade à janela (linhas 903–961, Fig. 3)

Com pares, a admissão cresce de 2,3 µs (100 sessões) a 127 µs (10.000); com classes,
fica entre 0,33 e 0,42 µs até 100 mil. Materializar arestas: 0,84 s (100) e 52,8 s
(1.000); agregar por classes: 0,33 s em 1.000 (161× mais rápido) e 26,4 s em 100 mil.
**Listagem 2:** a cadeia de evidência (1.991 origens, Ω = 1.303.422,8, endpoint
91%). **A janela W:** no gerador, W é o intervalo que divide as sessões de um
endpoint em agrupamentos de detecção; de 60 a 1.800 s a AUC de (d) fica em
0,976–0,978, porque o agrupamento da campanha tem 1.977–1.998 sessões em qualquer W.
**Particionamento em escala de CDN** (um parágrafo desde a rodada 8): o endpoint é a
chave natural; uma campanha que espalha um JA4 por muitos endpoints escapa de cada
partição; desenho em dois níveis, não implementado, cuja revocação precisa ser
medida.

### E. A regra por janela (linhas 962–1050, Tabela V e Fig. 4)

**Tabela V (sintético):** ataque K = 1000: 77,8% / 77,8% / cobertura 79,8% /
colateral 0; K = 50: 85,7% / 85,7% / 75,3% / 0; limpas: Ω 0,6%, dispara 0%; flash
crowds 25/50/100: Ω 80/100/100%, dispara 0%. Com o teste, nenhuma janela limpa
(limite superior 0,8%) e nenhum flash crowd. Pesos uniformes: pelo menos tantas
janelas de ataque; sem o termo de endpoint, 33,3% e nenhuma.

**Fig. 4:** pontos de operação em produção com 100 atacantes por janela, em dois
painéis (pilhas novas e compartilhadas): eixo x = falsos alarmes em janelas limpas
(escala log), eixo y = fração bloqueada. Dias de teste preenchidos, dia novo vazado;
uma taxa zero é desenhada em 0,01%. Na rodada 8 entraram dois pontos da
beta-binomial: unida ao filtro de inéditas sob o gatilho de origens, e sozinha como
gatilho.

**Produção, em cinco blocos:** (1) exportações dos quatro endpoints, limpas sem os
clientes bloqueados pelo WAF, escopo julgado só pelo JA4; botnet com /24 disjuntos
dos reais; frotas levam λ_e aos níveis da Tabela IV; o escopo sozinho produz filtro
em 1,5–6,3% das janelas do dia seguinte; por que o gatilho de origens corta os
falsos alarmes (nas oito janelas que só Ω admite, 33% do Ω vem de fora do termo de
endpoint, contra 12%). (2) **Concordância com o WAF** (veio de V-D): E3 84%, E4 96%,
E2 1,5%; o escopo cobre 16,7% dos bloqueios do WAF. (3) **Outras linhas de base**
(veio de V-D): o z-score sem calibração dispara em 2,6% das limpas e 64,5% dos flash
crowds; o de histórico próprio, em metade deles. (4) **Referência sobredispersa**
(novo): a correlação φ de cada impressão do perfil, estimada pelos momentos a partir
de Var[c] = n·b(1 − b)(1 + (n − 1)φ), limitada a [0; 0,99]; impressão ausente do
perfil mantém a binomial; nível calibrado como antes. (5) As frotas conhecidas (5%
das janelas, escolhido em três dias; nos dois reservados, E1 a 0,1× de 0,7% para
6,3%, com 7 falsos alarmes contra 8); o limiar dos z-scores calibrados; o gatilho
só pelo escopo (2,2% das limpas com frotas, 0,5% no dia novo, contra 3,5% e 8,8% sem
elas); sensibilidade a ρ; flash crowds de 1.000 (regra 21,8%, z-score 86,8%).

### F. Reprodutibilidade (linhas 1051 em diante)

Código público, Makefiles, sementes fixas. `make compile-check stix-ingest` confere
a consulta compilada e passa o STIX pelo validador, pelo TAXII e pelo MISP. O
protocolo do dia novo foi registrado com os *hashes* antes de ler o dia
(`fresh_day_protocol.md`), e `make production-tables` recalcula todo número de
produção. As entradas das Tabelas III e IV (agregados da operadora) não vão para o
repositório; vai o resumo anonimizado.

---

## 16. As fórmulas, uma a uma, com exemplos numéricos

### Pares de uma classe: C(n, 2) = n(n − 1)/2

Cinco origens com o mesmo JA4 formam C(5, 2) = 10 pares; mil origens, 499.500. É
por isso que o termo de endpoint domina: todas as origens de uma janela estão no
mesmo endpoint.

### A massa de coordenação: Ω(S) = Σ w_i · |E_i(S)|

Listagem 2 (1.991 origens): endpoint C(1.991, 2) = 1.981.045 pares × 0,6 =
1.188.627,0; TLS 114.710 × 1,0; rede 286 × 0,3 = 85,8. **Ω = 1.303.422,8**, com o
endpoint em 91%.

### O teste de enriquecimento

Uma janela com n = 100 origens; uma impressão com b(f) = 0,001 no perfil; c(f) = 5
origens com ela; |F| = 500.

1. **Enriquecimento:** c/n = 0,05 ≥ ρ · b = 0,003. Passa.
2. **Significância:** P[Bin(100; 0,001) ≥ 5] ≈ 7 × 10⁻⁸; vezes 500 (Bonferroni),
   3,5 × 10⁻⁵ < 0,01. **f entra no escopo.**
3. Com λ = 0,01, bastariam 4 origens para apontar essa pilha; com λ = 10⁻⁶⁰,
   seriam precisas 30.

O prior 1/N em b(f) evita prevalência zero para uma impressão nunca vista.

### O piso de calibração

A menor contagem que o nível aponta é c_min(n) = o menor c com P[Bin(n, b) ≥ c] · |F| <
λ_e (e c/n ≥ ρ·b). Uma botnet de A atacantes em 25 pilhas, com 90% nas pilhas, põe
cerca de 0,9 · A/25 origens em cada pilha, numa janela de n₀ + A origens. **O piso
é o menor A com 0,9 · A/25 ≥ c_min(n₀ + A)**, dividido por n₀ para virar fração da
janela.

Exemplo hipotético (não é um endpoint real): janela de 2.000 origens, perfil com
200.000 pares origem–impressão (b = 1/200.000 para uma pilha nova), |F| = 300.

| Nível λ_e | c_min por pilha | Menor botnet A | Piso (fração da janela) |
|---|---|---|---|
| 10⁻² | 3 | 84 | 4% |
| 10⁻²¹ | 10 | 278 | 14% |
| 10⁻⁶⁰ | 22 | 612 | 31% |

É o mecanismo da Tabela IV: as frotas empurram o nível para baixo, o nível empurra o
piso para cima, e isentar as frotas conhecidas devolve parte do nível.

### A referência beta-binomial

A binomial supõe que cada origem é um sorteio independente do perfil. Uma frota que
se ativa de uma vez põe várias origens na mesma janela, e a variância da contagem
fica maior que n·b(1 − b). A beta-binomial acrescenta uma correlação φ dentro da
janela:

> Var[c] = n·b(1 − b)·(1 + (n − 1)·φ)

Com φ = 0, é a binomial. Para cada impressão f do perfil, φ_f é estimado pelo
método dos momentos nas janelas de calibração com ao menos k_min origens:

> φ = Σ[(c − n·b)² − n·b(1 − b)] / Σ[n(n − 1)·b(1 − b)], limitado a [0; 0,99]

O teste passa a usar P[X ≥ c] com X ~ BetaBin(n; b·(1 − φ)/φ; (1 − b)·(1 − φ)/φ),
que tem a mesma média n·b. Uma impressão ausente do perfil mantém a binomial (não
há de onde estimar φ), e o nível λ_e é calibrado como antes.

Exemplo: n = 100 origens, b = 0,01 (em média, 1 origem na janela). Sob a binomial,
P[X ≥ 5] ≈ 3,4 × 10⁻³ e P[X ≥ 8] ≈ 8,2 × 10⁻⁶. Com φ = 0,05, P[X ≥ 5] ≈ 0,069 e
P[X ≥ 8] ≈ 0,030: uma frota que põe 8 origens na janela deixa de ser improvável. Por
isso a calibração não precisa mais empurrar o nível para 10⁻⁶⁰ para calar as
frotas, e o piso cai.

### O nível calibrado λ_e

Em cada janela sem ataque dos dias anteriores, calcula-se o menor p-valor ajustado
entre as impressões enriquecidas. λ_e é o 1º percentil desses valores, limitado a
0,01: o escopo produziria filtro em no máximo 1% das janelas de calibração.

### τ_cluster e o gatilho de origens

- τ_cluster = percentil 99 de Ω nas janelas sem ataque.
- Gatilho de origens = percentil 99 do número de origens distintas nas mesmas
  janelas.

### Os z-scores (linhas de base)

- **z contra o perfil:** z = (c − n·b) / √(n·b·(1 − b)). Sem calibração, bloqueia
  toda impressão com z > 3. No exemplo acima, z ≈ 15,5.
- **z calibrado:** o limiar passa a ser o percentil 99 do maior z de cada janela de
  calibração, nunca abaixo de 3. É o mesmo orçamento do teste.
- **z contra o próprio histórico:** (c − média de f) / max(desvio de f; 1), com
  média e desvio da contagem de f nas janelas de calibração, e o limiar calibrado da
  mesma forma.

### O filtro de inéditas e a união

- **Inéditas:** impressões ausentes do perfil e vistas em ao menos k_min = 5
  origens da janela.
- **União:** o escopo é enriquecimento ∪ inéditas. A união recupera as pilhas novas
  pequenas demais para o nível, e o enriquecimento cobre as compartilhadas.

### Frotas conhecidas

Impressão que o teste aponta, no nível nominal 0,01, em pelo menos 5% das janelas de
calibração. Sai do escopo e da calibração de λ_e (é uma lista de exceções). Sob a
beta-binomial, nenhuma impressão se qualifica, em nenhum endpoint e em nenhum dia.

### A regra de decisão do dia novo

Nos dias de teste: 5 falsos alarmes em 5.643 janelas, r = 0,000886. Com 1.152
janelas no dia novo, esperam-se 1,02 falsos alarmes. O protocolo dizia: o dia é
**consistente** se P[Bin(1.152; r) ≥ x] ≥ 0,05. Com x = 2, P = 0,27: consistente.
Com essa quantidade de janelas, o dia seria consistente até 3 falsos alarmes, e só
consegue limitar a taxa perto de 0,26% (regra dos três: 3/1.152); não a estabelece.

### Métricas

- **Revocação:** atacantes bloqueados / atacantes. **Precisão:** atacantes
  bloqueados / tudo o que foi bloqueado. **F1:** 2PR/(P + R).
- **FPR (TFP):** legítimos sinalizados / legítimos.
- **AUC:** probabilidade de um ataque aleatório receber escore maior que um
  benigno; mede ordenação, não decisão (por isso a Tabela II força o ponto de
  operação).
- **Colateral:** clientes legítimos bloqueados / clientes legítimos da janela. Na
  Tabela III, a mediana sobre as janelas limpas em que o escopo disparou.
- **Bloqueio da botnet (Tabela III):** fração dos atacantes injetados bloqueada,
  média sobre **todas** as janelas (0 onde a regra não dispara).
- **Regra dos três:** com zero eventos em n, o limite superior de 95% é ≈ 3/n
  (3/360 = 0,8% na Tabela V).
- **Wilcoxon pareado**, **d de Cohen**, **Kolmogorov–Smirnov (D)**: como antes.
  Com n = 30, o menor p bilateral exato do Wilcoxon é 2/2³⁰ ≈ 1,86 × 10⁻⁹; vezes 4
  (Bonferroni), 7,45 × 10⁻⁹: (d) venceu em todas as 30 sementes.

---

## 17. Números para saber de cor

| O quê | Número |
|---|---|
| AUC por sessão (acaso) / entre sessões | ≈ 0,50 (0,488–0,503) / 0,93–0,98, só dentro de um M |
| (d) com outro número de pilhas | 5 → 25 / 100: 0,61 / 0,63; 25 → 5 / 100: 0,48 / 0,75; mesmo M, outras sementes: 0,95–0,995 |
| MLP (a / d) | 0,493 / 0,862 (K = 50); 0,494 / 0,952 (K = 1000) |
| Escopo por frequência, 5+ pilhas | 0% do ataque, 39% do legítimo |
| Enriquecimento, 25 pilhas | 90,3%, sem colateral observado, sem rótulo |
| Inéditas, sintético | 90,3% (25 pilhas), 88,1% (100), 0% (compartilhadas); TFP 0,03% |
| Enriquecimento em pilhas compartilhadas (sintético) | 85,4% a 2,23% de colateral |
| Modelo aprendido + perfil, 25 / 100 pilhas | 87,4% / 86,9% (com rótulos) |
| Termo de endpoint no Ω da Listagem 2 | 91% |
| Produção | 8 dias + 1 dia novo; 4 endpoints; 5 dias de teste; 5.643 janelas limpas; 1.152 no dia novo |
| Regra do artigo (gatilho Ω) | 0,2% das limpas, colateral mediano 49,1% |
| Gatilho de origens: falsos alarmes | 6 contra 14 |
| Piso de calibração, E1 | 16% da janela (binomial); 7% com frotas conhecidas; 3% (beta-binomial); 15–18 origens por pilha (3 na beta-binomial) |
| Piso nos endpoints pequenos | 4 a 12 janelas (binomial); 0,9 a 2,8 (beta-binomial) |
| Níveis λ_e | binomial: E4 10⁻⁴, E3 10⁻¹⁴, E1 10⁻⁶⁰ (10⁻²¹ com frotas), E2 10⁻⁷³; beta-binomial: E1 7 × 10⁻⁵, os demais 0,01 |
| Configuração binomial (união, origens, frotas) | 0,1% (5 de 5.643); 38,4 / 77,7 (novas); 21,7 / 63,3 (compart.); colateral 32,9% |
| Beta-binomial (união, origens) | 0,4% (22 de 5.643); 59,8 / 77,7; 40,5 / 63,2; colateral 10,5%; console 1,3%; dia novo 0 (*post hoc*) |
| z-score calibrado | 0,4% (20 de 5.643); 54,7 / 77,7; 23,7 / 62,3; colateral 10,8%; console 1,1% |
| Acima do piso, E1 | 67–71% de uma botnet de 1× com todo escopo calibrado; 8–12% com 0,1× |
| Endpoints pequenos, 1× em pilhas novas | binomial 2–5%; beta-binomial e z-score 6–26% |
| z-score sem calibração | 2,6% das limpas, 64,5% dos flash crowds |
| z-score, histórico próprio | 0,9% das limpas, 50,6% dos flash crowds |
| Regime furtivo (E1, 0,1×) | gatilho dispara em 0,7–42% das janelas; 11,8% bloqueado; só escopo: 89,6 / 61,1% a 1,0% (binomial), 90,0 / 78,3% a 2,1% (beta-binomial) |
| WAF | E3 84%, E4 96%, E2 1,5%; o escopo cobre 16,7% dos bloqueios do WAF |
| Dia novo | binomial 2 de 1.152 (P = 0,27); 38,9 / 73,4; 21,5 / 60,9; z-score e regra básica nas mesmas 2 janelas |
| Frotas conhecidas, dias reservados | E1 0,1×: 0,7% → 6,3%, 7 contra 8 falsos alarmes |
| Consulta compilada no banco de logs da operadora | 23/09 e 25/09: origens e /24 em 1.152 / 1.152 janelas cada |
| Sinal novo na ontologia | 4 triplas, 0 linhas de código |
| STIX 2.1 | 0 erros, 0 avisos, modo estrito |
| Importador do MISP | mantém curso de ação e endpoint, perde 26 de 26 JA4 |
| Custo | 0,37 µs por admissão; 26,4 s para 100 mil sessões |
| Significância | p = 7,5 × 10⁻⁹; d de Cohen 13,5 e 22,3 |
| Medição JA4 na Azion | 6,33 M requisições, 495 impressões, top-1 38,4%, top-10 93,8% |
| Rapid Reset | 398 M rps; 201 M rps de ~20 mil máquinas |

---

## 18. Perguntas difíceis e como responder

**"Por que não usar só um z-score calibrado?"**
É uma alternativa legítima, e o artigo mostra isso na Tabela III: acima do piso, ele
bloqueia tanto ou mais, com alarmes mais leves. Nos dias de teste, porém, dispara
quatro vezes mais (20 contra 5 janelas limpas), e no dia novo os dois deram os
mesmos 2 falsos alarmes. A binomial paga a taxa menor de falsos alarmes com um piso
mais alto, e dá um nível do qual o **piso se calcula antes do ataque**: o operador
sabe, por endpoint, que botnet consegue apontar e onde precisa de outro recurso. Com
a referência beta-binomial, o teste chega ao ponto de operação do z-score com um
piso várias vezes menor e bloqueia mais em pilhas compartilhadas (40,5% contra 23,7%
com 100 atacantes). O artigo não afirma que o teste binomial bloqueia mais.

**"A beta-binomial não foi feita depois de olhar o dia novo?"**
Foi, e o artigo marca isso (asterisco na Tabela III). Por isso ela entra como
correção, ao lado da binomial, que é a configuração avaliada e registrada no
protocolo. O dia novo confirma a binomial (2 em 1.152, P = 0,27); o zero da
beta-binomial nesse dia não conta como confirmação. Nos dias de teste ela passa do
orçamento no console (1,3%), como o z-score calibrado (1,1%).

**"Se o modelo aprendido chega a 0,98, para que a regra?"**
Porque ele aprende a faixa de compartilhamento que um número de pilhas produz:
treinado com 5 pilhas, cai para 0,61–0,63 com 25 ou 100; treinado com 25, vai a 0,48
com 5. A regra lê um perfil de tráfego normal, não usa rótulos e mantém cerca de 90%
até 25 pilhas. E o teste entre números de pilhas usou sementes disjuntas, porque com
a mesma semente o gerador repete as sessões benignas e até (a) chegaria a 0,88–0,94.

**"O dia novo prova alguma coisa?"**
Prova que a taxa de falsos alarmes da configuração escolhida nos dias de teste não
era sobreajuste: 2 em 1.152, consistente com 5 em 5.643 (P = 0,27). A configuração,
as métricas e a regra de decisão foram registradas antes de ler o dia, com os
*hashes* das exportações. Com 1.152 janelas, o dia só limita a taxa perto de 0,26%;
não a estabelece sozinho.

**"O que o operador faz com o piso?"**
Decide o recurso por endpoint. Em E1, uma botnet acima de ~16% da janela (7% com
frotas conhecidas, 3% com a beta-binomial) pode ser apontada e bloqueada por
impressão. Nos endpoints pequenos, o piso da binomial é maior que a própria janela
(4 a 12 janelas; 0,9 a 2,8 com a beta-binomial): ali o escopo por impressão quase não
se aplica, e o recurso é limite de taxa ou desafio. É uma informação de gerência que
vem antes do ataque.

**"No sintético, o filtro de inéditas empata com vocês."**
Empata, e o artigo diz por quê: as pilhas geradas nunca aparecem no vocabulário
benigno. Por isso criamos o modo compartilhado, com pilhas tiradas do perfil, como
na injeção de produção: ali o filtro de inéditas bloqueia 0% e o teste 85,4%. Em
produção vale o mesmo (0% contra 20–63%).

**"O MLP mudou de resultado?"**
Mudou, e para melhor: o 0,235 era artefato da parada antecipada, que avaliava por
acurácia com 4,8% de ataques e restaurava os pesos da época 7. Sem parada
antecipada, 0,862 e 0,952. A conclusão (por sessão no acaso; entre sessões depende
do modelo) não muda; a frase "o perceptron inverte" saiu.

**"Por que o gatilho deixa passar a botnet no regime furtivo?"**
Porque é volume: uma botnet de um décimo da janela acrescenta poucas origens para
passar do percentil 99, na maior parte dos dias. O escopo, sozinho, a aponta em toda
janela; um gatilho só pelo escopo, examinado a posteriori, bloquearia 89,6% a 1,0%
das janelas limpas de E1. É o próximo passo declarado (gatilhos acionados pelo
escopo), não uma afirmação do artigo.

**"Se atributos resolvem a AUC, para que o grafo?"**
O artigo mede isso: um modelo linear sobre os atributos chega a 0,799, e o OWL não
mexe na AUC nem no gatilho. O grafo entra na operação: a consulta de contagens é
compilada da ontologia e reproduz as exportações de produção em dois dias; um sinal
novo custa 4 triplas; o veredicto sai como STIX 2.1 válido com a derivação junto.

**"O STIX de vocês funciona num SOAR de verdade? E o DOTS?"**
Pelo TAXII 2.1, o servidor de referência devolve intactos o indicador, o curso de
ação e a relação. O MISP descarta os JA4, e o DOTS define o escopo pelo alvo, só
filtra por campos de rede e de transporte (RFC 8783) e só descreve origens por
prefixo na telemetria (RFC 9244): nos dois casos, o escopo se alargaria para o
endpoint ou para prefixos de endereço. É uma lacuna de padrão que o artigo aponta.

**"Então Ω é só volume?"**
Na janela, sim, e o artigo diz isso: o termo de endpoint é 91% de Ω, e uma contagem
de origens serve de gatilho até melhor. O que discrimina ataque de pico é o escopo.

**"O modelo aprendido com perfil ganha em M = 100."**
Ganha, e está na Tabela II, mas treina com os rótulos da campanha que pontua. A
regra chega a 90% sem rótulo até 25 pilhas; em 100, um perfil maior restaura 89,6%.

**"Vocês escolheram a porta de origens e a união olhando os dados de teste."**
Sim, e o artigo diz isso. Depois, um dia novo, analisado com tudo fixado de antemão,
confirmou a taxa de falsos alarmes. As frotas conhecidas foram escolhidas em três
dias e testadas em dois reservados.

**"Uma operadora só, e tráfego sintético."**
Cada fonte responde a uma pergunta. Não existe dataset público do regime furtivo
distribuído (verificamos, inclusive o BCCC-cPacket-Cloud-DDoS-2024). Uma campanha
capturada é trabalho futuro.

**"E se o bot imitar o JA4 de um navegador? E o ECH?"**
Fora do modelo de ameaça; o modo adversarial mede isso (30,4% a 3,78% de colateral;
com ρ mais estrito, o escopo se recusa). O ECH esconde o JA4 só de quem observa no
caminho; uma CDN que termina o TLS continua vendo o ClientHello interno, então não
é uma limitação no nosso modelo de ameaça.

**"Os falsos alarmes bloqueiam um terço dos clientes da janela."**
Porque apontam frotas legítimas. Por isso a taxa é tão baixa (0,1%), e o artigo
reporta o colateral por alarme, que é o que o operador precisa. O z-score calibrado e
a beta-binomial têm alarmes mais leves (10,8% e 10,5%), mas quatro vezes mais
frequentes nos dias de teste.

**"Por que contar origens e não sessões?"**
Um cliente abre muitas conexões; em conexões, o escopo dispararia em 60% das
janelas limpas. Ressalva: CGN subconta e IPv6 com endereços de privacidade
sobreconta.

**"Por que ρ = 3?"**
É um piso de tamanho de efeito; quem faz o trabalho é o nível. Com ρ = 2 ou 5,
nenhuma taxa de disparo muda mais de 0,3 ponto e nenhum bloqueio mais de 4,5.

**"A comparação com o KLAGE é justa?"**
Não é controlada, e dizemos isso: nossa linha de base forte por sessão também supera
o F1 publicado, e o código deles não permite reexecutar.

---

## 19. Glossário de siglas e símbolos

### Siglas

| Sigla | Significado |
|---|---|
| AUC / ROC | Área sob a curva ROC (Receiver Operating Characteristic) |
| API | Application Programming Interface (E3 é o endpoint de API) |
| ASN | Autonomous System Number |
| CDN | Content Delivery Network (como a Azion) |
| CGN | Carrier-Grade NAT (muitos usuários atrás de um endereço) |
| CICIDS2017, CIC-IoT2023 | Datasets de laboratório do Canadian Institute for Cybersecurity |
| CVE | Common Vulnerabilities and Exposures |
| D3FEND | Grafo OWL de contramedidas defensivas do MITRE, mapeado ao ATT&CK |
| DDoS | Distributed Denial of Service |
| DOTS | DDoS Open Threat Signaling (IETF; RFC 8811 arquitetura, RFC 9132 canal de sinalização, RFC 8783 canal de dados, RFC 9244 telemetria) |
| DTW | Dynamic Time Warping |
| ECH | Encrypted Client Hello |
| F1 | Média harmônica de precisão e revocação |
| FA | Falso alarme (coluna da Tabela III) |
| FPR / TFP | Taxa de falsos positivos |
| HGB | Histogram Gradient Boosting |
| IETF / RFC | Internet Engineering Task Force / Request for Comments |
| IM | IFIP/IEEE Symposium on Integrated Network and Service Management |
| JA3 / JA4 | Impressões digitais do ClientHello TLS |
| JSON-LD | JSON para dados ligados |
| JWT | JSON Web Token |
| Kill-Bots / Speak-up | Defesas contra ataques que imitam picos legítimos (desafio computacional / gasto de banda) |
| KLAGE | Trabalho relacionado mais próximo (classifica nós de grafos de conhecimento construídos a partir de logs de rede) |
| KS | Teste de Kolmogorov–Smirnov |
| L7 | Camada 7 (aplicação) |
| MISP | Plataforma aberta de compartilhamento de inteligência de ameaças |
| MLP | Multilayer Perceptron |
| NOMS | Network Operations and Management Symposium |
| OASIS | Consórcio que mantém STIX e TAXII |
| OWL 2 (RL, DL) | Web Ontology Language; RL = perfil com inferência polinomial |
| PCA | Principal Component Analysis |
| RDF | Resource Description Framework |
| RF | Random Forest |
| RUM | Real User Monitoring (E1) |
| SIEM / SOAR | Gestão de eventos / orquestração e resposta de segurança |
| SPARQL | Linguagem de consulta para RDF |
| SSO | Single Sign-On (E4) |
| STIX 2.1 / TAXII 2.1 | Formato de intercâmbio de inteligência / protocolo de transporte |
| SynchroTrap | Detector de contas que agem em sincronia (coordenação no nível de contas) |
| SWRL | Semantic Web Rule Language |
| URCA / Hamsa | Extração de anomalias em fluxos / geração de assinaturas conferidas em tráfego normal |
| WAF | Web Application Firewall |

### Símbolos

| Símbolo | Significado |
|---|---|
| S, S_W | conjunto candidato de sessões; sessões ativas na janela W |
| W | janela deslizante (5 min) |
| Ω(S) | massa de coordenação |
| w_i | peso (`coordinationWeight`) da sub-relação i |
| E_i(S) | pares de origens distintas ligadas pela sub-relação i |
| τ_cluster | limiar de Ω: percentil 99 em tráfego sem ataque |
| k_min | mínimo de origens (5) |
| K, M, A | dispositivos da botnet; pilhas TLS; atacantes injetados por janela |
| 1×, 0,1× | botnet do tamanho da janela típica do endpoint, ou um décimo |
| α | expoente de Zipf das impressões benignas |
| c(f), n, b(f), N | origens com f; total de origens; prevalência de f no perfil (+1/N); pares do perfil |
| ρ | razão mínima de enriquecimento (3) |
| λ_e | nível do teste, calibrado por endpoint e |
| \|F\| | tamanho da família de Bonferroni |
| c_min | menor contagem que o nível aponta (define o piso) |
| φ | correlação dentro da janela de uma impressão do perfil (referência beta-binomial) |
| BetaBin | distribuição beta-binomial, a referência sobredispersa |
| 5% | fração das janelas de calibração em que o teste precisa apontar uma impressão para ela virar frota conhecida (sem símbolo) |
| E1–E4 | endpoints de produção anonimizados (RUM, console, API, SSO) |

---

## 20. Estado do trabalho e onde cada coisa está

**Pronto para apresentar.** O artigo em inglês tem 12 páginas com o corpo em 8
(limites do NOMS) e o resumo em 249 palavras; `make audit` confere 221 números e
frases contra os resultados, com 0 divergências. A versão em português acompanha a
estrutura da rodada 8, com os mesmos números (15 páginas; não é a submetida).

**Pendências:**

- o reenquadramento da tese, decidido depois da revisão de 26/09: escopo calibrado
  por impressão digital como contribuição, e a ontologia como camada de
  especificação e de interoperabilidade;
- antes da submissão: um arquivo LICENSE (o Apêndice F promete licença permissiva)
  e o branch publicado, para a URL do artigo mostrar esta versão;
- trabalho futuro declarado: gatilho acionado pelo escopo, HTTP/2, campanha furtiva
  capturada.

As regras de detecção removidas da ontologia ficam fora: nada depende delas, o SWRL
delas era inválido e uma redefinia `CoordinatedHTTPFlood` por taxa por sessão, o que
contradiz o artigo (revisão do artefato de 26/09). Estão no histórico do Git.

**Onde está cada coisa:**

| O quê | Onde |
|---|---|
| Artigo submetido | `papers/http-session-noms/article.tex` e `.pdf` |
| Artigo em português | `papers/http-session-noms-pt/article.tex` e `.pdf` |
| Conceitos explicados em detalhe | `docs/concepts.md` |
| Resultados do sprint | `experiments/sprint-6-noms/README.md` |
| Protocolo do dia novo | `experiments/sprint-6-noms/results/fresh_day_protocol.md` |
| Tabelas de produção (III e IV) | `scripts/production_tables.py` → `results/production_tables.json` (`make production-tables`) |
| Referência beta-binomial | `rule_detection_production.py --overdispersion` (`make rule-production-od`) |
| Generalização entre números de pilhas | `scripts/cross_m_generalization.py` → `results/cross_m_generalization.json` (`make cross-m`) |
| Adendo do protocolo do dia novo | `experiments/sprint-6-noms/results/fresh_day_protocol_addendum.md` |
| Filtro de inéditas no sintético | `scripts/unseen_synth.py` → `results/unseen_synth_*.csv` (`make unseen-synth`) |
| Auditoria dos números | `make audit` em `experiments/sprint-6-noms` |
| Ontologia | `ontology/ddos_ontology.owl` |
| Compilador e verificação STIX | `scripts/compile_counts.py`, `scripts/stix_check.py` |
| Dados da Azion (fora do repositório) | `/Volumes/Untitled/kg-ddos-data/azion/` |
