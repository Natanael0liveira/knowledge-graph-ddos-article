# Guia de estudo do artigo NOMS

*Scoped Mitigation of Application-Layer DDoS with a Session-Centric Knowledge Graph*

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
6. III. O grafo de conhecimento centrado na sessão (Fig. 1 e 2)
7. IV. Metodologia de avaliação
8. V-A. Ablação (Tabela II)
9. V-B. A regra como detector (Tabela III) e o tráfego de produção
10. V-C. Capturas de laboratório e KLAGE (Tabela IV)
11. V-D. Dano colateral (Fig. 3)
12. V-E e V-F. Custo, janela W e significância estatística
13. VI. Discussão e limitações
14. VII. Conclusão
15. Apêndices A a F (Tabelas V e VI, Listagens 1 e 2)
16. As fórmulas, uma a uma, com exemplos numéricos
17. Números para saber de cor
18. Perguntas difíceis e como responder
19. Glossário de siglas e símbolos
20. Estado do trabalho e onde cada coisa está

---

## 1. O artigo em um minuto

**O problema.** Um DDoS lento e distribuído na camada de aplicação (a família
*Slow HTTP DoS*: Slowloris, HULK, GoldenEye) usa muitas origens, cada uma mandando
pouco tráfego. Nenhuma origem cruza um limiar por origem, e cada sessão, olhada
sozinha, parece legítima.

**A virada do artigo.** Perceber que um endpoint está sob ataque é fácil: quase
basta contar quantas origens distintas chegaram nele na janela. O difícil é
**decidir quem bloquear sem bloquear os próprios usuários do serviço**. O artigo
é sobre essa decisão, o **escopo da mitigação**.

**A proposta.** Um grafo de conhecimento (OWL) em que a sessão HTTP é entidade de
primeira classe, ligada a outras sessões por seis relações tipadas, cada uma com
um peso proporcional ao custo que o atacante teria para quebrá-la. Uma regra
(SPARQL/SWRL) dispara sobre a "massa de coordenação" Ω, e o escopo vem de um
**teste binomial de enriquecimento**: bloqueia as impressões digitais TLS (JA4)
que estão sobre-representadas no agrupamento em relação ao tráfego normal.

**Os quatro achados principais.**

1. Em campanhas furtivas geradas, a detecção por sessão fica no acaso (AUC ≈ 0,50)
   em quatro famílias de classificador; atributos entre sessões chegam a 0,93–0,98.
2. O escopo "natural" (a impressão digital mais comum do agrupamento) é
   **prejudicial**: com a botnet espalhada em várias pilhas TLS, ele bloqueia 0% do
   ataque e 39% do tráfego legítimo. O teste de enriquecimento bloqueia 90% sem
   colateral e sem rótulo algum.
3. Em oito dias de tráfego real da CDN da Azion, o teste nomeia pilhas da botnet
   que clientes reais também usam (o que um filtro de "impressões inéditas" não
   consegue) e raramente dispara em picos legítimos (4% contra 65% de um z-score).
4. O que o grafo acrescenta é operacional e **medido**: a consulta de contagens é
   compilada a partir da ontologia e reproduz exatamente as exportações da Azion;
   a exportação STIX 2.1 passa no validador oficial em modo estrito.

**A honestidade como argumento.** O artigo diz com todas as letras o que o grafo
*não* acrescenta (a AUC e o gatilho), onde o método falha (regime furtivo em
produção) e quais escolhas foram feitas depois de ver dados, com confirmação em
dias reservados.

---

## 2. O que mudou nas últimas rodadas, e por quê

O artigo passou por quatro rodadas de revisão independente (weak reject → weak
accept borderline → weak accept) e por dois blocos de trabalho novo (itens 2 e 3).
Em ordem:

### Rodada 1 e 2: o método de contagem e a produção

- **Contar em origens, não em sessões.** Em produção uma "sessão" é uma conexão, e
  um cliente abre muitas (5,8 por cliente no endpoint de API). Contado em
  conexões, o escopo nomeava filtro em 60,1% das janelas limpas. Agora Ω, o
  mínimo k_min e o teste contam **origens distintas** (endereços de origem).
- **Nível calibrado λ_e.** Frotas legítimas que ligam juntas quebram a
  independência que o teste binomial assume. O nível do teste passou a ser
  calibrado por endpoint nos dias anteriores, como τ.
- **Tráfego de produção da Azion** (8 dias, 4 endpoints, anonimizados como E1–E4),
  com botnet injetada, protocolo *rolling* (cada dia testado com o que os dias
  anteriores ensinaram) e a Tabela VI.
- **Fig. 1 redesenhada** em tons de cinza: espessura da linha segue o peso, e cada
  sub-relação tem seu padrão de traço.

### Rodada 3: o enquadramento

- **Título novo**, centrado na mitigação com escopo.
- **O gatilho é volume.** Um limiar simples no número de origens distintas
  concorda com Ω ≥ τ em 86–99,6% das janelas. O artigo passou a dizer isso.
- **Tabela VI refeita** com três escopos (enriquecimento, z-score, JA4 inéditos),
  pilhas novas e compartilhadas, coluna de *flash crowd*, a união
  (enriquecimento ∪ inéditos) e a porta de origens.
- **Modelo aprendido com o perfil.** Para a comparação ser justa, o modelo
  aprendido também recebeu o perfil de tráfego normal. Ele passa a igualar ou
  superar a regra, mas precisa dos rótulos da própria campanha. A antiga frase
  "recupera mais que o dobro" saiu.
- **Condições (iv) e (v) da regra removidas** (taxa agregada e perfil
  BotBehavior): nunca estavam ativas em nenhum experimento.

### Rodada 4: precisão das afirmações

- "Compila em contagens" virou "se reduz a contagens" até ser medido (e depois,
  no item 3, foi medido de verdade).
- A porta de origens e a união foram **declaradas como escolhidas nos mesmos dias
  de teste**, com os números (6 contra 14 falsos alarmes) e a confirmação de que
  valem em cada um dos cinco dias.
- O resultado negativo do regime furtivo (E1 a 0,1×: 0,6%) entrou no corpo.

### Item 2: um perfil que conhece as frotas

- Impressões digitais que o teste nomeia com frequência nos dias de calibração
  viram **frotas conhecidas**: saem do escopo e da calibração do nível.
- **Protocolo registrado antes de rodar**: escolha da fração φ nos três primeiros
  dias de teste, pelo maior bloqueio sem mais falsos alarmes; os dois últimos
  ficam de reserva.
- Escolhido φ = 5%. Nos dias de reserva, E1 a 0,1× sobe de 0,7% para **6,3%**
  (pilhas compartilhadas: 0,2% → 4,4%), com 7 falsos alarmes contra 8.

### Item 3: o valor do grafo, medido

- Os pesos passaram a ser **lidos da ontologia** em todos os scripts (antes eram
  copiados à mão em cinco lugares).
- A ontologia ganhou `kg:classKey` (o que cada relação de igualdade iguala),
  `kg:countUnit`, `kg:tlsJa4`, `kg:srcPrefix`, e teve `kg:targets` corrigido (a
  declaração antiga faria um raciocinador concluir que toda sessão é um ataque).
- Um **compilador** gera o SQL de contagens a partir da ontologia. Em sessões
  geradas, reproduz Ω com diferença 0,0. **No ClickHouse da Azion, para 23/09,
  devolveu exatamente as origens e os pares /24 exportados nas 1.152 janelas.**
- Uma sub-relação nova custa **4 triplas e 0 linhas de código**.
- O STIX 2.1 exportado passou a ser **válido no validador da OASIS, inclusive em
  modo estrito** (antes falhava com 13 erros por pacote).

---

## 3. Título e resumo (linhas 99–129)

**Título.** *Scoped Mitigation of Application-Layer DDoS with a Session-Centric
Knowledge Graph.* A palavra que manda é **scoped**: a contribuição é o escopo da
mitigação; o grafo é a camada onde a decisão é derivada e exportada.

**O resumo, frase a frase.** Ele segue um arco: problema, virada, método,
resultado negativo, solução, produção (com o custo à vista) e, no fecho, a resposta
a "por que um grafo?".

1. *Um Slow HTTP DoS distribuído mantém cada origem abaixo de qualquer limiar por
   origem.* O problema.
2. *Sinalizar o endpoint atacado exige pouco mais que contar origens; a decisão
   difícil é quem bloquear sem bloquear os próprios usuários, e a resposta natural
   é prejudicial.* A tese e o suspense: a "resposta natural" é o escopo pela
   impressão mais comum, que o artigo mostra ser prejudicial.
3. *Modelamos a sessão HTTP como entidade de primeira classe de um grafo OWL, com
   seis sub-propriedades ponderadas pelo custo de evasão; uma regra SPARQL/SWRL
   deriva veredicto, evidência e escopo.* O método.
4. *Em campanhas furtivas geradas, a detecção por sessão fica no acaso; atributos
   entre sessões chegam a AUC 0,93–0,98.* Resultado 1.
5. *O escopo pela impressão TLS mais comum bloqueia 0% do ataque e 39% do legítimo;
   o teste de enriquecimento bloqueia 90% sem colateral e sem rótulo, igualando um
   modelo aprendido que recebe o perfil e os rótulos da campanha.* O resultado
   negativo e a solução, com a comparação justa.
6. *Em oito dias de CDN, o teste nomeia pilhas que clientes reais também usam (o
   filtro de inéditas não) e dispara em 4% dos flash crowds contra 65% do
   z-score.* Por que o escopo importa em produção.
7. *Unido a esse filtro atrás de um gatilho de origens, detém 38–78% de 100 a 1.000
   atacantes (20–62% em pilhas compartilhadas) e dispara em 0,1% das janelas limpas,
   onde bloqueia uma mediana de 30% dos clientes.* O saldo operacional, com o
   ganho e o custo lado a lado.
8. *O grafo justifica seu lugar: a consulta compilada reproduz janela a janela a
   exportação de um dia de produção, um sinal novo custa 4 triplas e nenhum código,
   e o STIX 2.1 passa no validador da OASIS em modo estrito.* O fecho responde à
   principal objeção dos revisores com três fatos medidos.

O resumo tem 250 palavras, no limite do IEEE.

---

## 4. I. Introdução (linhas 137–177)

**Parágrafo 1: o contexto.** Ataques de camada de aplicação crescem (HTTP/2 Rapid
Reset, CVE-2023-44487: 398 milhões de requisições por segundo de ~20 mil
máquinas; Cloudflare: 6.500 ataques hipervolumétricos no 2º trimestre de 2025).
Defesas volumétricas absorvem o grande; o difícil é o lento e distribuído.

**Parágrafo 2: o que resta de discriminativo.** Uma campanha furtiva deixa cada
sessão parecida com uma legítima. O que sobra está **entre** sessões: a mesma
impressão digital recorrendo em muitas origens, convergindo num endpoint. Por isso
o problema é de **gerência de rede e serviço** (NOMS), não só de detecção: agir
exige decidir quem, com que evidência, com que filtro.

**Parágrafo 3: as três lacunas.** Uma meta-análise de 75 estudos: 47% dos
detectores tiram atributos de sessões, mas as achatam num vetor. KLAGE usa grafo,
mas (1) raciocina sobre nós de rede, não sessões; (2) a coordenação fica implícita
em *embeddings*; (3) para num relatório, sem escopo de mitigação.

**Parágrafo 4: as quatro contribuições.**

- **(i)** Ontologia OWL com a sessão como entidade e seis sub-propriedades
  ponderadas por custo de evasão; proximidade de rede entra só como evidência
  auxiliar.
- **(ii)** Procedimento de decisão: a regra dispara sobre Ω(S), e o veredicto é a
  derivação. Mostramos que na janela Ω age como gatilho de volume, que uma
  contagem de origens distintas cumpre ao menos tão bem, com metade dos falsos
  alarmes em produção.
- **(iii)** Escopo derivado do grafo, exportado em JSON-LD e STIX 2.1. A escolha
  natural (propriedade mais comum) é prejudicial; o teste binomial de
  enriquecimento a substitui.
- **(iv)** Avaliação contra linha de base forte por sessão e contra modelo
  aprendido com o perfil, à medida que a campanha se distribui, mais oito dias de
  produção, medindo o colateral.

**Pergunta provável:** "Por que isso é NOMS e não segurança pura?" Resposta: porque
a contribuição é a decisão operacional (o escopo, o custo em usuários legítimos, a
exportação para SOAR), medida em tráfego de produção.

---

## 5. II. Trabalhos relacionados (linhas 180–206, Tabela I)

**Tabela I** compara sete trabalhos em quatro dimensões: unidade de raciocínio,
relação entre sessões, forma da explicação, e se há escopo de mitigação e
colateral. Só "This Work" tem: sessão de aplicação, relação explícita (tipada e
ponderada), explicação como derivação, escopo derivado, colateral reportado.

- **Grafos de conhecimento em segurança:** a primeira onda era estática (CVE,
  relatórios). Uma revisão diz que ainda não se sabe usar KG em problemas
  industriais reais. KLAGE é o mais próximo (grafo a partir de logs).
- **Detecção de DDoS L7:** perfilamento estatístico (PCA sobre fluxos ou sobre
  matriz por sessão) e aprendizado supervisionado. Nenhum mantém relação entre
  sessões.
- **Modelagem de sessão:** nenhum dos 75 estudos mantém a sessão como objeto com
  identidade e relações. Plataformas industriais (Cloudflare, sinais por JA4)
  existem, mas são proprietárias e não publicam colateral.
- **Fronteira:** nenhum trabalho tem, junto, sessão como unidade, relações
  explícitas e escopo derivado com colateral.

---

## 6. III. O grafo de conhecimento centrado na sessão (linhas 209–410)

### Fig. 1 (a ontologia) e Fig. 2 (o pipeline)

A **Fig. 1** tem três colunas:

- **Session:** a `ApplicationSession` ligada a `Identity` (cookie, token, JA4),
  `Endpoint`, `IPAddress/ASN` e `Behavior`.
- **relatedTo:** sessões S1–S7 ligadas pelas seis sub-relações. A espessura da
  linha segue o peso; cada sub-relação tem um traço (TLS contínua preta grossa,
  identidade tracejada, temporal traço-ponto, endpoint contínua cinza, carga útil
  pontilhada, rede tracejada cinza-clara). S6–S7 ligadas só por rede ficam
  "esparsas: abaixo de τ".
- **Verdict:** `CoordinatedHTTPFlood` (≥ k_min origens, um endpoint, Ω ≥ τ) →
  cadeia de evidência JSON-LD/STIX → `CourseOfAction`. O escopo são as impressões
  digitais enriquecidas contra o tráfego normal.

A **Fig. 2** mostra as duas camadas: admissão por requisição (rápida) e
materialização/regra por janela.

### III-A. Grafos de conhecimento (linha 232)

- **RDF:** fatos como triplas ⟨sujeito, predicado, objeto⟩.
- **OWL 2:** declara classes e propriedades. Usamos o perfil **OWL 2 RL**, cuja
  inferência por encadeamento para frente é polinomial, o que torna viável
  materializar em tempo de execução (OWL 2 DL não é).
- **SWRL:** regras de Horn (se todas as premissas valem, afirma uma tripla).
- **SPARQL:** consulta e agrega.
- **JA4:** hash do *ClientHello* do TLS, que identifica a pilha TLS do cliente.
  Não depende do IP, então sobrevive à rotação de endereço.

### III-B. A ontologia (linha 245)

Classe central `ApplicationSession`, ligada por `hasIdentity`, `originatesFrom`
(endereço de origem), `targets` (endpoint), `exhibitsBehavior`, `mitigatedBy`
(política com atributo `scope`). Hierarquia de ataques:
`ApplicationLayerAttack` → `SlowHTTPDoSFamily` → `ConnectionExhaustionAttack`
(Slowloris, slow body, slow read) e `CoordinatedHTTPFlood` (HULK, GoldenEye).
Alinhada a STIX 2.1 e MITRE ATT&CK.

### III-C. Modelo de ameaça (linha 263)

- O **defensor** opera a aplicação e vê, por requisição, o JA4, a origem, o
  endpoint, o tempo e a identidade. Não vê o canal de controle da botnet, mas pode
  perfilar o tráfego normal fora de ataques.
- O **atacante** controla K dispositivos comprometidos e pode fazer cada sessão
  estatisticamente igual a uma legítima (hipótese furtiva).
- **O dano é capacidade esgotada:** cada sessão segura uma conexão e um *worker*
  como uma legítima; nenhuma taxa por sessão sobe.
- **Por que JA4 é difícil de mudar:** vem da biblioteca TLS de cada dispositivo
  (roteadores, câmeras, DVRs da linhagem Mirai). Apresentar o *ClientHello* de um
  navegador exigiria embarcar uma biblioteca de imitação em cada dispositivo.
- **Fronteira:** bots que imitam navegador (fazendas de *headless browser*) ficam
  fora do modelo e são avaliados como limite (modo adversarial).

### III-D. A família `relatedTo` ponderada (linha 285)

Seis sub-propriedades de `relatedTo` (simétrica), cada uma com
`coordinationWeight` w_i:

| Sub-relação | Peso | Por quê |
|---|---|---|
| TLSFingerprint | 1,0 | trocar a pilha TLS em todo dispositivo é caro |
| ReusedIdentity | 1,0 | espalhar credenciais quebra a economia da campanha |
| TemporalPattern | 0,9 | vem da operação da botnet; ruído quebra parcialmente |
| PayloadSignature | 0,6 | randomizar é barato, mas custa coerência |
| EndpointConvergence | 0,6 | idem |
| NetworkProximity | 0,3 | botnets modernas se espalham por ASNs; CGN torna /24 fraco |

A calibração do Apêndice B **corrobora a ordem**, não os valores absolutos.

### III-E. Construção em tempo de execução (linha 309)

Janela deslizante W = 5 min. JA4 exato, endpoint e prefixo são **relações de
equivalência**: cada uma particiona S em classes. Então o número de pares ligados
sai do tamanho das classes:

> |E_i(S)| = Σ_k C(n_k, 2), com C(n, 2) = n(n−1)/2 e n_k o tamanho da classe k,
> contado em origens.

Consequência prática: admitir uma sessão é inserir sua origem numa classe
(tempo constante), e Ω não precisa de nenhuma aresta de par. Só as relações não
transitivas (JA4 quase igual, temporal, carga útil) comparam pares.

### III-F. A regra de detecção (linhas 326–357)

**A fórmula central:**

> Ω(S) = Σ_i w_i · |E_i(S)|

E_i(S) é o conjunto de **pares de origens distintas** cujas sessões estão ligadas
pela sub-relação i. Cada par conta uma vez, então um cliente com muitas sessões
não se passa por coordenação.

**A regra `CoordinatedHTTPFlood`** vale quando existe S com:

- (i) pelo menos k_min origens (k_min = 5);
- (ii) todas as sessões visam o mesmo endpoint;
- (iii) Ω(S) ≥ τ_cluster.

Ela só **mitiga** quando o teste de enriquecimento nomeia uma impressão digital.
Por janela, S é toda sessão para o endpoint.

**"Na escala da janela, Ω é volume."** Sob a condição (ii), o termo de endpoint é
0,6 · C(n, 2) para n origens, e responde por 91% de Ω na campanha da Listagem 2.
Com pesos uniformes a regra detecta igual. Um limiar sobre origens distintas serve
de porta ao menos tão bem, e um limiar de taxa agregada nada acrescenta (cada
sessão mantém taxa legítima). Os pesos ordenam a cadeia de evidência: um conjunto
ligado **só** por rede precisa de ~3× mais pares (1,0/0,3) para chegar ao mesmo Ω.

### III-G. Formulação simbólica (linha 359)

Dois estágios (Listagem 1): SWRL enuncia cada sub-relação como regra de Horn; a
agregação (soma), que SWRL não expressa, é uma consulta SPARQL que lê os pesos das
anotações `coordinationWeight`.

### III-H. Cadeia de evidência e escopo derivado (linhas 372–410)

Quando a regra dispara: regra satisfeita, instâncias, decomposição de Ω por
sub-relação e escopo. Exportado em JSON-LD e STIX 2.1 (*indicator* +
*course-of-action* ligados por *mitigates*), para SIEM e SOAR.

**Por que o escopo por frequência falha.** A impressão digital mais comum do
agrupamento é a da população legítima (a cabeça da distribuição). Contra uma
botnet em várias pilhas, cada pilha é menor que a cabeça benigna, e o filtro
bloqueia usuários e nenhum atacante.

**O teste de enriquecimento** (explicado com exemplo na seção 16). Admite toda
impressão digital f que seja:

- **enriquecida:** c(f)/n ≥ ρ · b(f), com ρ = 3;
- **improvável sob o fundo:** P[X ≥ c(f)] < λ_e / |F|, com X ~ Bin(n, b(f)).

Onde c(f) = origens do agrupamento com a impressão f; n = Σ c(f); b(f) =
prevalência de f no perfil de tráfego normal, mais 1/N; |F| = número de impressões
do perfil e do agrupamento (divisor de Bonferroni). O resultado é um **conjunto**
de impressões, o que cobre uma botnet fragmentada.

**λ_e calibrado:** o maior valor até 0,01 em que o escopo nomeia filtro em no
máximo 1% das janelas sem ataque. No gerador, λ_e fica em 0,01.

**Sem rótulos:** o perfil é o que o defensor vê em operação normal. Se o
adversário se esconde numa impressão popular, nada fica enriquecido e o sistema
**recusa** o escopo (relata que não há discriminador).

---

## 7. IV. Metodologia de avaliação (linhas 413–517)

**Cinco fontes, cada uma responde a uma pergunta:** gerador calibrado (mecanismo
sob campanhas controladas), capturas de laboratório (ataques convencionais e
KLAGE), oito dias de produção (falsos alarmes reais e detecção de botnet
injetada).

**Cenários por grau de distribuição K** (número de dispositivos):

- A (K = 1): inundação de origem única, resolvida por detectores volumétricos;
- B (10 ≤ K ≤ 100): botnets pequenas, cada origem dentro do seu limite;
- C (K ≥ 1000): espalhada em centenas de ASNs; é onde a contribuição tem de valer.

Reportamos B (K = 50) e C (K = 1000).

**O gerador.** Dois parâmetros decidem o realismo:

- **Popularidade das impressões benignas:** curva de Zipf de expoente α (a
  impressão de posto r tem probabilidade proporcional a r^(−α)). Medimos na Azion:
  6,33 milhões de requisições TLS, 495 impressões distintas, a mais comum com
  38,4% e as dez primeiras com 93,8%. α = 1,5 e 2,0 cercam a curva medida;
  canônico α = 1,5.
- **Composição da botnet:** 90% da campanha distribuída uniformemente em M pilhas
  TLS (M = 25 canônico), o resto em impressões únicas. Modo **adversarial**: a
  botnet adota as impressões benignas mais comuns (limite do modelo de ameaça).

**Realismo das sessões benignas:** calibradas em ~322 mil sessões benignas do
CICIDS2017 e verificadas pelo teste de **Kolmogorov–Smirnov** (D = 0,003 para
duração, 0,002 para número de requisições, p > 0,8). No modo **furtivo**, sessões
de ataque saem das mesmas distribuições.

**Capturas de laboratório:** CICIDS2017 (Slowloris, Slowhttptest, HULK,
GoldenEye) e CIC-IoT2023 (DDoS Slowloris, HTTP Flood), onde KLAGE reporta F1 =
84,1%.

**Linhas de base:** Random Forest forte (8–9 atributos de fluxo), repetida com
gradient boosting, MLP e regressão logística; e três acadêmicas reimplementadas
(PCA sobre fluxos, PCA + k-means sobre matriz de sessão, supervisionado RF/SVM).

**As quatro configurações da ablação:**

- (a) ML sem ontologia;
- (b) ontologia sem nenhuma sub-relação (sessões isoladas);
- (c) só proximidade de rede (detector ingênuo por prefixo/ASN);
- (d) a representação completa entre sessões.

Então (d)−(a) é a contribuição total; (d)−(b), o ganho de representar estrutura
entre sessões; (d)−(c), o ganho dos sinais de peso alto sobre a rede. (d) usa a
evidência como **atributos** (fração do agrupamento com o mesmo JA4 ou /24, e o
tamanho), para todas as configurações terem os mesmos dados e classificador.

**Métricas:** AUC, F1, precisão, revocação e **dano colateral**: a fração de
tráfego legítimo que cai dentro do escopo derivado. É a taxa de falsos positivos
do **filtro que o operador implantaria**, que pode ser muito diferente da do
detector. Cadeias de evidência avaliadas por **completude** e **acionabilidade**.

---

## 8. V-A. Ablação (linhas 525–588, Tabela II)

**Tabela II (AUC por sessão, α = 1,5, M = 25, 30 sementes):**

| Configuração | K = 50 | K = 1000 |
|---|---|---|
| (a) ML por sessão forte | 0,498 | 0,503 |
| (b) ontologia sem relatedBy | 0,500 | 0,502 |
| (c) só NetworkProximity | 0,499 | 0,659 |
| **(d) entre sessões** | **0,927** | **0,982** |

**Leitura:**

- Por sessão, tudo fica no acaso (0,471–0,503 em todas as famílias). O colapso
  está na **representação**, não no classificador.
- (c) só chega a 0,66 porque a botnet é dispersa em prefixos.
- Em (d) o modelo importa: com 25 pilhas a evidência é **não monotônica** (um
  atacante divide a impressão com algumas dezenas de pares; um legítimo da cabeça,
  com centenas). Árvores recortam a faixa do meio (0,92–0,99); regressão logística
  cai para 0,80–0,87; o MLP **inverte** em K = 50 (0,235), porque aprendeu que
  impressão muito compartilhada é benigna.
- A regra não precisa de amostra rotulada, porque lê um perfil explícito.

**As capturas de laboratório** vêm de 1 a 7 origens num único /24: inundações ao
alcance de um limite por prefixo, fora do regime distribuído.

---

## 9. V-B. A regra como detector e o tráfego de produção (linhas 590–663)

### Tabela III: a regra como detector, contra modelos aprendidos

Aqui não há classificador: as sessões que casam com o escopo **são** o conjunto
sinalizado. Como AUC ordena e a regra decide, o classificador é forçado ao ponto
de operação da regra (zero falsos positivos). K = 1000, 15 sementes.

| Cenário | Regra (revocação) | FPR | F1 | Aprendido (d) | Aprendido + perfil |
|---|---|---|---|---|---|
| M = 1 | 89,8% | 0,00% | 0,946 | 91,7% | 85,9% |
| M = 5 | 90,0% | 0,00% | 0,948 | 88,6% | 91,7% |
| M = 25 | 90,3% | 0,00% | 0,949 | 36,4% | 87,4% |
| M = 100 | 38,6% | 0,00% | 0,556 | 17,6% | 86,9% |
| M = 25, adversarial | 30,4% | 3,78% | 0,452 | 7,8% | 6,6% |

**Leitura honesta:**

- Contra botnet monolítica ou pouco fragmentada, o modelo aprendido compete.
- Com 25 pilhas, a regra abre vantagem sobre o modelo sem perfil (90,3% contra
  36,4%), apesar de esse modelo ter AUC 0,979: seus escores se sobrepõem aos
  benignos na cauda.
- **Dado o mesmo perfil** (prevalência da impressão da sessão e seu enriquecimento
  no agrupamento), o modelo iguala a regra em 25 pilhas e a supera em 100.
- **Mas ele treina com os rótulos da campanha que pontua**, que nenhum operador tem
  durante um ataque. A vantagem da regra é não precisar de rótulo.
- Em M = 100, pilhas pequenas demais para um perfil de mil sessões prendem a regra
  em 38,6% (um perfil maior restaura 89,6%, seção V-D).

### Por janela (Tabela V, no Apêndice E)

Com as chegadas benignas espalhadas por uma hora: Ω ≥ τ sozinho dispara em 78–86%
das janelas de ataque, 0,6% das limpas e **80–100% dos flash crowds**. Exigir que o
teste nomeie uma impressão elimina todo falso alarme e mantém a detecção.

### O parágrafo de produção

1. **Duas suposições do gerador quebram:** um cliente abre muitas conexões
   (contado em conexões, escopo em 60,1% das janelas limpas; em origens, 26,9%); e
   frotas ligam juntas (por isso λ_e calibrado, levando a regra a 0,2%).
2. **O gatilho é volume:** um limiar p99 sobre origens distintas concorda em
   86–99,6% e, como porta, **reduz os falsos alarmes à metade** (6 contra 14
   janelas limpas) sem perder detecção.
3. **O escopo separa ataque de pico:** com pilhas compartilhadas, o enriquecimento
   bloqueia 20,2% e 61,6% de 100 e 1.000 atacantes, onde o filtro de inéditas não
   bloqueia nenhum; e dispara em 3,9% dos flash crowds de 100 usuários, onde o
   z-score dispara em 64,5%.
4. **Configuração combinada** (união atrás da porta de origens): 0,1% das janelas
   limpas, bloqueia 38,4% e 77,7% em pilhas novas; seus falsos alarmes bloqueiam
   uma mediana de 29,9% dos clientes.
5. **Declaração:** essas duas melhorias foram escolhidas nos mesmos dias de teste;
   valem em cada um dos cinco; dias novos precisam confirmá-las.

---

## 10. V-C. Laboratório e KLAGE (linhas 665–699, Tabela IV)

**Tabela IV (CIC-IoT2023, DDoS Slowloris):** KLAGE F1 0,841; (a) 3 atributos
0,179; (a′) 8 atributos 0,900; (d) nosso 0,911.

**Leitura:** o Slowloris real de laboratório deixa assinatura de fluxo por sessão,
então uma linha de base forte já basta. A comparação com KLAGE é favorável mas
**não controlada**: nossa linha de base forte também supera 0,841, então a margem
não é da representação; e o código do KLAGE parte de um grafo pré-construído sem
pesos publicados, então não dá para reexecutar. Datasets públicos só têm ataques
com assinatura de fluxo óbvia (Fig. 4).

---

## 11. V-D. Dano colateral (linhas 701–744, Fig. 3)

**Fig. 3:** escopo por frequência contra escopo por enriquecimento, α = 1,5,
15 campanhas por configuração.

- **Botnet monolítica (M = 1):** os dois concordam, 89,8% bloqueado, sem colateral.
  Um limite global no endpoint desconectaria todo usuário legítimo.
- **A partir de 5 pilhas:** a impressão modal vira uma legítima e o escopo por
  frequência **inverte**: 0,0% do ataque, 39,0% do legítimo. Com α = 2,0, 61,1%.
- **Enriquecimento:** 90,0% e 90,3% em M = 5 e 25, **sem colateral observado**. Os
  10% restantes são as impressões únicas (escopo troca completude por precisão).
  Em M = 100: 38,6%, ainda sem colateral; perfil de 30 períodos restaura 89,6%.
- **Dois limites:** (1) modo adversarial: 30,4% do ataque a 3,78% de colateral
  (contra 3,6% e 39,0% da frequência); com ρ mais estrito o escopo se recusa. (2) O
  perfil: deriva moderada é tolerável (perfil α = 2,0 contra episódio 1,5: 90,3%,
  sem colateral); perfil plano ou ausente leva o colateral a 77,6%. **Perfil fresco
  e amplo é requisito de implantação.**

---

## 12. V-E e V-F. Custo, W e significância (linhas 746–762)

**Custo (Apêndice D, Fig. 5):** com as relações de igualdade como classes, a
admissão fica constante em ~0,37 µs por sessão, e a camada simbólica linear: 26,4 s
para 100 mil sessões, contra 52,8 s com arestas de par para apenas mil. O valor de
Ω cresce com o quadrado do agrupamento; calculá-lo, não.

**Janela W:** a AUC de (d) é plana numa faixa de 30× de W (60 a 1.800 s).

**Significância:** testes de **Wilcoxon** pareados nas 30 execuções, com correção
de **Bonferroni** para quatro comparações: (d)−(c) e (d)−(a) significativos em
K = 1000 (p = 7,5 × 10⁻⁹), com **d de Cohen** de 13,5 e 22,4. Ressalva: sementes
são sorteios do mesmo gerador; os testes mostram estabilidade, não preveem o campo.

---

## 13. VI. Discussão e limitações (linhas 765–821)

- **Particionamento:** a condição (ii) faz do endpoint a chave natural de
  particionamento; a regra fica exata por partição. Uma campanha que espalha um JA4
  por muitos endpoints acumula poucos pares em cada um. Apêndice D esboça um
  desenho de dois níveis.
- **O ganho é específico do regime:** limiares por IP resolvem origem única; um
  classificador forte por sessão chega a AUC ≥ 0,98 em datasets públicos. Só o
  distribuído **e** furtivo precisa do método, que complementa as defesas
  volumétricas.
- **Cada avaliação estabelece uma coisa:** o gerador mostra o mecanismo (sob
  imitação imposta por construção); a produção mede falsos alarmes reais e
  detecção de botnet injetada. Onde o tráfego real casa com o modelo de ameaça
  (E1 a 0,1×), o nível calibrado prende o enriquecimento em 0,6%, e o perfil com
  frotas conhecidas, testado em dias reservados, em 6,3%. Não há campanha furtiva
  capturada.
- **Dependência de um discriminador de peso alto:** a varredura de robustez mostra
  a AUC(d) caindo de 1,00 para ~0,74 quando o JA4 é aleatorizado. O gatilho de
  volume sobrevive, mas o escopo fica sem discriminador. Um bot que imita o JA4 de
  navegador o derrota; o ECH poderia esconder o JA4.
- **O que o grafo acrescenta (o parágrafo mais importante para a defesa):**
  - *O que não acrescenta:* a AUC (um modelo linear sobre os mesmos três atributos
    chega a 0,799) nem o gatilho (volume); e um modelo aprendido com perfil e
    rótulos iguala ou supera a regra.
  - *O que acrescenta, medido:* a ontologia marca o que cada relação de igualdade
    iguala, seu peso e a unidade de contagem; a consulta é **compilada** dela e
    reproduz Ω exatamente em sessões geradas; **no armazém de logs da operadora
    devolve as contagens exportadas nas 1.152 janelas de um dia**; um sinal novo
    custa 4 triplas e 0 código; o pacote STIX 2.1 passa no validador da OASIS em
    modo estrito, então o SOAR recebe um *course-of-action* já parametrizado.
  - "Explicável" no sentido de derivação inspecionável; se encurta a decisão de um
    analista não foi testado.

---

## 14. VII. Conclusão (linhas 824–844)

Resumo dos achados, com as ressalvas: detecção por sessão no acaso contra 0,93–0,98;
escopo por frequência prejudicial contra enriquecimento a 90% sem colateral e sem
rótulo; modelo aprendido só iguala com perfil e rótulos; em produção o gatilho é
contagem de origens e o teste nomeia pilhas compartilhadas e ignora a maioria dos
picos, mas no regime furtivo certifica poucas, caso que as frotas conhecidas elevam
de 0,7% para 6,3%. Próximos passos: modelos de frota mais ricos, HTTP/2 e uma
campanha furtiva capturada.

**Agradecimento:** Azion autorizou a medição de impressões digitais e as
estatísticas agregadas, exportadas sem endereços, portas ou URIs.

---

## 15. Apêndices A a F

### A. Construção e instanciação das sub-relações (linhas 855–949)

**Algoritmo 1:** para cada requisição, resolve sessão, identidade e endpoint; liga
no grafo; instancia cada sub-relação contra as sessões ativas; expurga o que sai
da janela. (Enumera pares por clareza; na prática as relações de igualdade são
classes.)

Procedimento de cada sub-relação: TLS (igualdade exata ou variante próxima,
distância ≤ 1), identidade (cookie, token ou usuário compartilhado; JWT pelo
`sub`), temporal (DTW normalizado ≤ τ_DTW, com FastDTW e LSH), carga útil (cosseno
> τ_payload), endpoint (normalização de caminho), rede (mesmo /24, /48 ou ASN).

**Listagem 1:** uma regra SWRL (dois `tlsJa4` iguais → `relatedByTLSFingerprint`)
e a agregação SPARQL: conta origens distintas por classe (`COUNT(DISTINCT ?o)`),
soma w · n(n−1)/2 por endpoint, e compara com o τ do endpoint (`kg:tauCluster`).

### B. Calibração dos pesos (linhas 950–990)

Em laboratório (poucas dezenas de JA4), a otimização até inverte o sinal do TLS:
artefato de baixa diversidade. No cenário realista (conjunto de 2.000 impressões,
maior que as 76–818 que cada endpoint de produção mostra), grade {0,3…1,0}³ (125
combinações, 60 cenários, 91.500 sessões): o melhor vetor é (1,0; 0,3; 0,3), e o
TLS é o único sinal individualmente discriminativo (AUC 0,93, contra 0,50 do
endpoint e 0,58 da rede). Os pesos do artigo (1,0; 0,6; 0,3) dão a mesma AUC ótima
0,943 e são insensíveis a ±20%. Conclusão: a calibração valida a **ordem**.

*Realismo do gerador:* a medição é ponderada por requisição (superestima a
concentração) e vem de um ponto de presença; o CICIDS2017 é mais concentrado
(52,7% na cabeça); a curva medida é cercada por α = 1,5 e 2,0.

### C. Limitações adicionais (linhas 991–1034, Fig. 4)

Instrumentação de sessão; contar origens por endereço erra com CGN (subconta) e
IPv6 com endereços de privacidade (sobreconta; o /64 seria a unidade natural);
custo da manutenção do grafo; HTTP/2 e outros protocolos; só 3 das 6 sub-relações
exercitadas; amplitude de datasets; validação da explicação sem estudo com
usuários. A **Fig. 4** mostra onde a evidência entre sessões é necessária.

### D. Modelo de custo e sensibilidade à janela (linhas 1035–1113, Fig. 5)

Com enumeração de pares, a admissão cresce de 2,3 µs (100 sessões) para 127 µs
(10.000); com contadores de classe, fica entre 0,33 e 0,42 µs de 100 a 100 mil.
Materializar arestas: 0,84 s (100) e 52,8 s (1.000); agregar por classes: 0,33 s em
1.000 (161× mais rápido) e 26,4 s em 100 mil. Os dois modos dão o mesmo Ω até
7 × 10⁻¹².

**Listagem 2:** a cadeia de evidência de uma campanha canônica (M = 25, K = 1000),
contada em origens: 1.991 origens, Ω = 1.303.422,8, das quais TLS 114.710, endpoint
1.188.627 (91%), rede 85,8; o escopo lista 25 impressões.

Particionamento em escala de CDN: trabalhadores por endpoint mais um esboço global
sobre identificadores de peso alto (não implementado).

### E. A regra por janela (linhas 1115–1252, Tabelas V e VI)

**Tabela V (sintético, por janela de 5 min):** ataque K = 1000: Ω ≥ τ 77,8%,
dispara 77,8%, cobertura 79,8%, colateral 0; K = 50: 85,7% / 85,7% / 75,3% / 0;
limpas: Ω 0,6%, dispara 0,0%; flash crowds 25/50/100: Ω 80/100/100%, dispara 0%.
Com o teste: nenhuma janela limpa (limite superior de 95% = 0,8%, pela "regra dos
três": 3/360) e nenhum flash crowd. Pesos uniformes: mesma detecção; sem o termo de
endpoint: 33,3% e 0%. Porta de origens: 82,2% e 85,7%.

**Tabela VI (produção, 8 dias, 5 dias de teste, 5.643 janelas limpas):**

- Por endpoint (regra do artigo): E1 (RUM, > 1.000 origens/janela), E2 (console),
  E3 (API), E4 (SSO), todos < 100 origens/janela exceto E1.
- Por escopo, com porta Ω ≥ τ: enriquecimento, z-score, JA4 inéditos, união.
- Com porta de origens: enriquecimento e união.
- Colunas: dispara em janelas limpas, colateral mediano, dispara em flash crowd de
  100, e botnet bloqueada com A = 100, A = 1.000 e 1× (do tamanho da janela típica),
  pilhas novas / compartilhadas.

**Texto do Apêndice E, em quatro parágrafos:**

1. **Protocolo:** exportações com contagens por impressão e janela, feitas dentro
   do armazém de logs; cada dia testado com perfil, limiares e λ_e dos dias
   anteriores; clientes bloqueados pelo WAF excluídos; botnet canônica injetada;
   escopo julgado só pelo JA4 (as exportações não trazem prefixos).
2. **Frotas e o nível:** λ_e vai a ~10⁻⁴ (E4), 10⁻¹⁴ (E3), 10⁻⁶⁰ (E1), 10⁻⁷³ (E2).
   O escopo sozinho nomeia filtro em 1,5–6,3% das janelas do dia seguinte. Quando a
   regra dispara em janela limpa de E2 ou E3, nomeia uma frota e bloqueia cerca de
   metade dos clientes. **Por que a porta de origens reduz os falsos alarmes à
   metade:** nas 8 janelas limpas que só Ω admite, 33% do Ω vem de fora do termo de
   endpoint (contra 12% nas demais); uma frota se concentra numa impressão e infla
   o termo TLS justamente onde o escopo erra. O gatilho não deve ler a mesma
   evidência que o escopo.
3. **Dois limites da detecção:** em E1 com 1.000 atacantes e E4 a 1×, o escopo
   nomeia as pilhas mas Ω fica abaixo de τ em 57% e 94% das janelas; em E2 e E3 as
   pilhas de uma botnet desse tamanho têm uma ou duas origens, e nenhum nível
   calibrado as certifica. Com 0,1× só E1 tem mais de 100 atacantes: enriquecimento
   0,6%, inéditas 11,2%, z-score 12,5% (disparando em 5,1% das janelas limpas de E1).
4. **Perfil com frotas conhecidas** (φ = 5%, escolhido nos 3 primeiros dias): em E1,
   5 ou 6 frotas (7% do perfil) fixavam o nível, que sobe de ~10⁻⁶⁰ para 10⁻²¹. Nos
   2 dias de reserva, E1 a 0,1× sobe de 0,7% para 6,3% (compartilhadas 0,2% → 4,4%),
   com 7 falsos alarmes contra 8. Frações menores bloqueiam mais, mas disparam o
   dobro, com filtros mais leves e em mais flash crowds; e um atacante que use a
   impressão de uma frota conhecida escapa. Também: perfil por hora não ajudou; ρ = 2
   ou 5 move taxas de disparo em no máximo 0,3 ponto, bloqueios em 4,5 e colateral
   mediano em 7,2; flash crowds de 1.000 disparam a regra em 21,8% e o z-score em
   86,8%; o WAF concorda em 84% (E3) e 96% (E4), 1,5% em E2; E1 não tem WAF.

### F. Reprodutibilidade (linhas 1254 em diante)

Código público, Makefiles, sementes fixas, `make audit` confere cada número do
artigo contra os resultados. As entradas da Tabela VI (agregados da operadora)
não vão para o repositório; vai só o resumo anonimizado. `make compile-check` e
`make stix-check` rodam sem dados.

---

## 16. As fórmulas, uma a uma, com exemplos numéricos

### Pares de uma classe: C(n, 2) = n(n − 1)/2

Cinco origens com o mesmo JA4 formam C(5, 2) = 10 pares. Mil origens formam
499.500. É por isso que o termo de endpoint domina: todas as origens de uma janela
estão no mesmo endpoint.

### A massa de coordenação: Ω(S) = Σ w_i · |E_i(S)|

Exemplo da Listagem 2 (1.991 origens):

- endpoint: C(1.991, 2) = 1.981.045 pares × 0,6 = 1.188.627,0
- TLS: 114.710 pares × 1,0 = 114.710,0
- rede (/24): 286 pares × 0,3 = 85,8
- **Ω = 1.303.422,8**, dos quais o endpoint é 91%. Daí "na janela, Ω é volume".

### O teste de enriquecimento

Exemplo: uma janela com n = 100 origens; uma impressão f com prevalência
b(f) = 0,001 (0,1%) no perfil; c(f) = 5 origens do agrupamento com essa impressão;
|F| = 500 impressões na família.

1. **Enriquecimento:** c/n = 5/100 = 0,05 ≥ ρ · b = 3 × 0,001 = 0,003. Passa.
2. **Significância:** sob o fundo, esperaríamos n · b = 0,1 origem com f.
   P[Bin(100; 0,001) ≥ 5] ≈ 7 × 10⁻⁸. Ajustado por Bonferroni (× 500): 3,5 × 10⁻⁵.
   Com λ = 0,01, passa: **f entra no escopo**.
3. Com λ = 0,01, bastariam **4** origens para certificar essa pilha. Com
   λ = 10⁻⁶⁰ (o nível que as frotas impõem em E1), seriam precisas **30**. É isso
   que "o nível calibrado prende o enriquecimento" quer dizer.

**Bonferroni** (dividir λ por |F|, ou multiplicar p por |F|) controla a chance de
qualquer uma das |F| impressões passar por acaso.

**O prior 1/N** em b(f) evita dividir por zero: uma impressão nunca vista teria
prevalência 0 e enriquecimento infinito.

### O nível calibrado λ_e

Em cada janela sem ataque dos dias anteriores, calcula-se o menor p-valor ajustado
entre as impressões enriquecidas. λ_e é o 1º percentil desses valores, limitado a
0,01. Por construção, o escopo nomearia filtro em no máximo 1% das janelas de
calibração.

### τ_cluster e a porta de origens

- τ_cluster = percentil 99 de Ω nas janelas (ou agrupamentos) sem ataque.
- Porta de origens = percentil 99 do número de origens distintas nas mesmas janelas.

### O z-score (linha de base)

z = (c − n·b) / √(n·b·(1 − b)). Bloqueia toda impressão com z > 3, sem correção
para múltiplos testes e sem calibração. No exemplo acima, z ≈ 15,5: o z-score
também nomearia f. Sua fraqueza aparece nos flash crowds, onde dispara em 64,5%.

### Frotas conhecidas

Uma impressão é frota conhecida se o teste a nomeia, no nível nominal 0,01, em pelo
menos φ das janelas de calibração (φ = 5%). Ela sai do escopo e da calibração de λ_e.

### Métricas

- **Revocação (recall):** atacantes bloqueados / atacantes.
- **Precisão:** atacantes bloqueados / tudo o que foi bloqueado.
- **F1:** 2 · P · R / (P + R).
- **FPR (taxa de falsos positivos):** legítimos sinalizados / legítimos.
- **AUC (área sob a curva ROC):** probabilidade de um ataque aleatório receber
  escore maior que um benigno aleatório. 0,5 é o acaso; 1,0, perfeito. Mede
  **ordenação**, não decisão; por isso a Tabela III força o ponto de operação.
- **Colateral:** clientes legítimos bloqueados pelo escopo / clientes legítimos da
  janela. Na Tabela VI, a mediana sobre as janelas limpas em que o escopo disparou.
- **Bloqueio da botnet (Tabela VI):** fração dos atacantes injetados que o escopo
  detém, média sobre **todas** as janelas (0 onde a regra não dispara).
- **Limite superior de 95% com zero eventos ("regra dos três"):** 3/n; com 360
  janelas limpas e nenhum disparo, 3/360 = 0,8%.
- **Wilcoxon pareado:** teste não paramétrico sobre as diferenças par a par entre
  duas configurações nas mesmas sementes.
- **d de Cohen:** diferença média dividida pelo desvio padrão; acima de 0,8 já é
  "grande"; 13,5 e 22,4 são enormes (o gerador separa muito bem).
- **Kolmogorov–Smirnov (D):** maior distância entre duas distribuições acumuladas;
  D = 0,003 quer dizer distribuições praticamente iguais.

---

## 17. Números para saber de cor

| O quê | Número |
|---|---|
| AUC por sessão (acaso) / entre sessões | ≈ 0,50 / 0,93–0,98 |
| Escopo por frequência, 5+ pilhas | 0% do ataque, 39% do legítimo |
| Enriquecimento, 25 pilhas | 90,3%, sem colateral, sem rótulo |
| Modelo aprendido + perfil, 25 / 100 pilhas | 87,4% / 86,9% (com rótulos) |
| Termo de endpoint no Ω da Listagem 2 | 91% |
| Produção | 8 dias, 4 endpoints (E1–E4), 5 dias de teste, 5.643 janelas limpas |
| Regra do artigo em janelas limpas | 0,2%, colateral mediano 49,1% |
| Porta de origens: falsos alarmes | 6 contra 14 (metade) |
| Flash crowd de 100: enriquecimento / z-score / inéditas | 3,9% / 64,5% / 0,2% |
| Pilhas compartilhadas, 100 / 1.000 atacantes | enriquecimento 20,2% / 61,6%; inéditas 0% |
| Configuração combinada (porta + união) | 0,1% das limpas, 38,4% / 77,7% (novas) |
| Níveis calibrados λ_e | E4 10⁻⁴, E3 10⁻¹⁴, E1 10⁻⁶⁰, E2 10⁻⁷³ |
| E1 a 0,1×: enriquecimento / inéditas / z-score | 0,6% / 11,2% / 12,5% |
| Frotas conhecidas, dias de reserva | E1 0,7% → 6,3% (compart. 0,2% → 4,4%), 7 vs 8 alarmes |
| Consulta compilada no ClickHouse da Azion | 1.152 / 1.152 janelas idênticas |
| Sinal novo na ontologia | 4 triplas, 0 linhas de código |
| STIX 2.1 | 0 erros, 0 avisos, modo estrito |
| Custo | 0,37 µs por admissão; 26,4 s para 100 mil sessões |
| Significância | p = 7,5 × 10⁻⁹; d de Cohen 13,5 e 22,4 |
| Medição JA4 na Azion | 6,33 M requisições, 495 impressões, top-1 38,4%, top-10 93,8% |

---

## 18. Perguntas difíceis e como responder

**"Se atributos resolvem a AUC, para que o grafo?"**
Concordamos, e o artigo mede isso: um modelo linear sobre os mesmos atributos chega
a 0,799, e o OWL não mexe na AUC. O grafo entra na **operação**: a consulta de
contagens é compilada da ontologia e reproduz as exportações de produção nas 1.152
janelas; um sinal novo custa 4 triplas e nenhum código; o veredicto sai como STIX
2.1 válido, pronto para o SOAR, com a derivação junto.

**"Então Ω é só volume?"**
Na janela, sim, e o artigo diz isso. O termo de endpoint é 91% de Ω, e uma contagem
de origens serve de porta até melhor. O que discrimina ataque de pico é o **escopo**
(o teste de enriquecimento). Ω continua útil como decomposição da evidência e é
onde entrariam as relações não transitivas (temporal, carga útil).

**"O modelo aprendido com perfil ganha de vocês em M = 100."**
Ganha, e está na Tabela III. Mas ele treina com os rótulos da campanha que pontua,
que nenhum operador tem durante o ataque. A regra chega a 90% sem rótulo até 25
pilhas; em 100 pilhas, um perfil maior restaura 89,6%.

**"Em produção a detecção é fraca."**
Em parte, sim, e isso está declarado. O método detém bem botnets grandes diante do
tráfego do endpoint. No regime furtivo (E1 a 0,1×), o nível calibrado prende o teste
em 0,6%; o perfil com frotas conhecidas, validado em dias reservados, sobe para
6,3%. O z-score detém mais (12,5%), mas dispara em 5% das janelas limpas de E1 e em
64,5% dos flash crowds. A contribuição de produção é mostrar **o custo de cada
escopo**, não vencer em detecção.

**"Vocês escolheram a porta de origens e a união olhando os dados de teste."**
Sim, e o artigo diz isso, com os números (6 contra 14) e a confirmação de que valem
nos cinco dias. Para as frotas conhecidas, fizemos o certo: regra de escolha
registrada antes, desenho em 3 dias, teste em 2 reservados.

**"Uma operadora só, e tráfego sintético."**
Cada fonte responde a uma pergunta: o gerador isola o mecanismo sob imitação
imposta; a produção mede falsos alarmes em clientes reais. Não existe dataset
público do regime furtivo distribuído (verificamos, inclusive o
BCCC-cPacket-Cloud-DDoS-2024). Uma campanha capturada é trabalho futuro.

**"E se o bot imitar o JA4 de um navegador? E o ECH?"**
Fica fora do modelo de ameaça, e o modo adversarial mede isso: o escopo cai para
30,4% com 3,78% de colateral, e com ρ mais estrito se recusa, que é o relato
correto quando não há discriminador. O ECH pode esconder o JA4; é uma limitação
declarada.

**"Os falsos alarmes bloqueiam metade dos clientes da janela."**
Sim, porque o que eles nomeiam são frotas legítimas. Por isso a taxa é tão baixa
(0,2%, ou 0,1% com a porta de origens), e o artigo reporta o colateral por falso
alarme, que é a métrica que um operador precisa.

**"Por que contar origens e não sessões?"**
Porque um cliente abre muitas conexões (5,8 por cliente na API). Em conexões, o
escopo dispararia em 60% das janelas limpas. Ressalva declarada: CGN subconta e IPv6
com endereços de privacidade sobreconta (o /64 seria a unidade).

**"Por que ρ = 3?"**
É um piso de tamanho de efeito; quem faz o trabalho é o nível. Com ρ = 2 ou 5,
nenhuma taxa de disparo muda mais de 0,3 ponto e nenhum bloqueio mais de 4,5.

**"A comparação com o KLAGE é justa?"**
Não é controlada, e dizemos isso. Nossa linha de base forte por sessão também supera
o F1 publicado do KLAGE, então a margem não é da representação. O código deles não
permite reexecutar.

**"E HTTP/2?"**
Rapid Reset e similares exigem outras sub-relações (cancelamento de stream, abuso de
CONTINUATION). É o próximo passo, declarado.

---

## 19. Glossário de siglas e símbolos

### Siglas

| Sigla | Significado |
|---|---|
| AUC / ROC | Área sob a curva ROC (Receiver Operating Characteristic) |
| API | Application Programming Interface (E3 é o endpoint de API) |
| ASN | Autonomous System Number (identifica uma rede na internet) |
| CDN | Content Delivery Network (rede de entrega, como a Azion) |
| CGN | Carrier-Grade NAT (muitos usuários atrás de um endereço) |
| CI | Confidence Interval (intervalo de confiança) |
| CICIDS2017, CIC-IoT2023 | Datasets de laboratório do Canadian Institute for Cybersecurity |
| CVE | Common Vulnerabilities and Exposures |
| DDoS | Distributed Denial of Service |
| DTW | Dynamic Time Warping (distância entre séries temporais) |
| DVR | Digital Video Recorder (dispositivo típico de botnet Mirai) |
| ECH | Encrypted Client Hello (TLS que cifra o ClientHello) |
| F1 | Média harmônica de precisão e revocação |
| FPR / TFP | False Positive Rate / taxa de falsos positivos |
| HGB | Histogram Gradient Boosting |
| HTTP/2 | Segunda versão do HTTP (multiplexação de streams) |
| IEEE / IFIP | Organizadores da conferência NOMS |
| JA3 / JA4 | Impressões digitais do ClientHello TLS (JA4 ordena extensões antes do hash) |
| JSON-LD | JSON para dados ligados (Linked Data) |
| JWT | JSON Web Token (`sub` = identificador do sujeito) |
| KG | Knowledge Graph (grafo de conhecimento) |
| KLAGE | Trabalho relacionado mais próximo (grafos a partir de logs + Graph-BERT) |
| KS | Teste de Kolmogorov–Smirnov |
| L7 | Camada 7 (aplicação) do modelo OSI |
| LIME / LLM | Explicação local de modelos / modelo de linguagem |
| LR | Logistic Regression |
| LSH | Locality-Sensitive Hashing |
| MITRE ATT&CK | Base de táticas e técnicas de ataque (T1498.001 = inundação direta) |
| ML | Machine Learning |
| MLP | Multilayer Perceptron |
| NAT | Network Address Translation |
| NOMS | Network Operations and Management Symposium |
| OASIS | Consórcio que mantém o padrão STIX |
| OWL 2 (RL, DL) | Web Ontology Language; RL = perfil com inferência polinomial |
| PCA | Principal Component Analysis |
| PoP | Point of Presence (ponto de presença da CDN) |
| RDF | Resource Description Framework (triplas) |
| RF | Random Forest |
| RUM | Real User Monitoring (E1 são beacons de RUM) |
| SIEM | Security Information and Event Management |
| SOAR | Security Orchestration, Automation and Response |
| SPARQL | Linguagem de consulta para RDF |
| SSO | Single Sign-On (E4) |
| STIX 2.1 | Structured Threat Information Expression, formato de intercâmbio de inteligência |
| SVM | Support Vector Machine |
| SWRL | Semantic Web Rule Language (regras de Horn sobre OWL) |
| TDB2 / Fuseki | Armazenamento e servidor SPARQL do Apache Jena |
| TLS | Transport Layer Security |
| UUID | Identificador único universal (STIX exige `tipo--UUID`) |
| WAF | Web Application Firewall |

### Símbolos

| Símbolo | Significado |
|---|---|
| S | conjunto candidato de sessões (por janela: todas as sessões do endpoint) |
| W | janela deslizante (5 min) |
| Ω(S) | massa de coordenação: soma ponderada de pares ligados |
| w_i | peso (`coordinationWeight`) da sub-relação i |
| E_i(S) | pares de origens distintas ligadas pela sub-relação i |
| n_k | tamanho (em origens) da classe k de uma relação de igualdade |
| τ_cluster | limiar de Ω: percentil 99 em tráfego sem ataque |
| k_min | mínimo de origens para a regra (5) |
| K | número de dispositivos da botnet (grau de distribuição) |
| M | número de pilhas TLS da botnet |
| A | atacantes injetados por janela (produção) |
| 1×, 0,1× | botnet do tamanho da janela típica do endpoint, ou um décimo |
| α | expoente de Zipf da popularidade das impressões benignas |
| c(f) | origens do agrupamento com a impressão f |
| n | total de origens do agrupamento (no teste) |
| b(f) | prevalência de f no perfil normal (+ 1/N) |
| N | pares origem–impressão do perfil |
| ρ | razão mínima de enriquecimento (3) |
| λ_e | nível do teste binomial, calibrado por endpoint e |
| \|F\| | tamanho da família de Bonferroni (impressões do perfil e do agrupamento) |
| φ | fração de janelas de calibração para uma impressão virar frota conhecida (5%) |
| E1–E4 | endpoints de produção anonimizados (RUM, console, API, SSO) |

---

## 20. Estado do trabalho e onde cada coisa está

**Pronto para apresentar.** O artigo em inglês tem 12 páginas com o corpo em 8
(limites do NOMS), compila sem avisos de estouro, e `make audit` confere 136
números contra os resultados, com 0 divergências. A versão em português está
sincronizada (14 páginas; não é a submetida).

**Pendências, nenhuma bloqueia a apresentação:**

- dia 25/09 da Azion (E3 e E4, depois das 21h de Brasília), como confirmação
  extra fora da amostra;
- uma rodada do revisor independente sobre os itens 2 e 3;
- os commits (nada foi commitado ainda).

**Onde está cada coisa:**

| O quê | Onde |
|---|---|
| Artigo submetido | `papers/http-session-noms/article.tex` e `.pdf` |
| Artigo em português | `papers/http-session-noms-pt/article.tex` e `.pdf` |
| Conceitos explicados em detalhe | `docs/concepts.md` |
| Resultados do sprint e protocolo das frotas | `experiments/sprint-6-noms/README.md` (seções 9 a 11) |
| Auditoria dos números | `make audit` em `experiments/sprint-6-noms` |
| Ontologia | `ontology/ddos_ontology.owl` |
| Compilador e verificação STIX | `scripts/compile_counts.py`, `scripts/stix_check.py` |
| Dados da Azion (fora do repositório) | `/Volumes/Untitled/kg-ddos-data/azion/` |
