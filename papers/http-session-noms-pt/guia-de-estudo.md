# Guia de estudo: escopo calibrado por fingerprint TLS

*TLS-Fingerprint Scoping of Application-Layer DDoS Mitigation: Calibration Floors and
Collateral on a CDN Operator's Endpoints*

Este guia explica o projeto inteiro, do problema às fórmulas, tal como ele está. Cada
conceito aparece com a intuição, a fórmula, um exemplo com números e o lugar
do artigo onde ele é usado. A versão que vale é o artigo em inglês
(`papers/http-session-noms/article.tex`), a que vai para o NOMS, e as seções, tabelas e
figuras citadas aqui são as dele. Os números vêm do artigo ou dos arquivos de
`experiments/sprint-6-noms/results/`, que `make audit` confere contra o texto. Os
exemplos numéricos marcados como *hipotéticos* servem só para ensinar a conta.

**Como ler.** Se você não é da área, comece pela **Parte 0**, que explica tudo sem fórmulas, com uma analogia, um exemplo com números redondos e um roteiro de leitura de cada tabela e figura. Depois, a Parte I apresenta o problema e a ideia, e a Parte II
ensina o método, fórmula por fórmula. A Parte III explica como ele foi avaliado e com que
métricas, e a Parte IV percorre os resultados, tabela por tabela. A Parte V reúne o que o artigo recomenda, os seus limites, os números principais, o glossário e onde está cada coisa. Com pouco tempo, leia a Parte 0 e a seção 19. A história de por que o artigo deixou
de ser sobre grafos de conhecimento está em `por-que-mudamos.md`, nesta pasta.

**Notação.** Vírgula decimal (0,1%). Potências de dez como 10⁻⁶⁰. ⌈x⌉ é o menor inteiro
maior ou igual a x. C(n, 2) = n(n − 1)/2 é o número de pares distintos entre n elementos.
Bin(n, b) é a distribuição binomial de n sorteios com probabilidade b.

---

## Parte 0. Para entender sem matemática

*Se você não é da área, comece aqui. Esta parte explica o trabalho com uma analogia, um
exemplo pequeno com números redondos e o significado de cada resultado, sem fórmulas. As
Partes I a V aprofundam cada ponto, com as contas.*

### 0.1 O trabalho em cinco frases

1. Um ataque DDoS lento e distribuído usa milhares de máquinas, e cada uma manda tão
   pouco tráfego que nenhuma chama atenção sozinha.
2. Perceber que um serviço está sob ataque é fácil, porque aparecem visitantes demais. O
   difícil é decidir **quem bloquear** sem bloquear os usuários de verdade.
3. Nós bloqueamos pelo "fingerprint" do software de cada visitante, a **fingerprint TLS**
   (JA4). Só entram no bloqueio os fingerprints que aparecem **muito mais que o normal**
   naquele serviço.
4. Um teste estatístico decide o que é "muito mais que o normal". Ele é **calibrado** em
   dias sem ataque, para errar raramente.
5. Medimos isso em tráfego gerado e em oito dias de quatro serviços reais da Azion: quanto
   o método acerta, quanto custa aos usuários e onde deixa de funcionar.

### 0.2 Uma analogia: a portaria de um prédio

Pense na portaria de um prédio comercial muito movimentado. O porteiro não conhece
ninguém, mas repara em duas coisas em cada pessoa que entra: **de onde ela vem** (o
endereço de rede, que o artigo chama de *origem*) e **como ela se apresenta** (o *fingerprint*).

O fingerprint TLS funciona como um sotaque. Quando um navegador ou um programa abre uma conexão
segura (HTTPS), ele se apresenta de um jeito característico: quais versões aceita, que
lista de cifras oferece, em que ordem. A JA4 resume essa apresentação numa sequência
curta de letras e números. O Chrome se apresenta de um jeito, o Safari de outro, e o
firmware de uma câmera IP barata de um terceiro jeito.

**Um dia normal.** Das pessoas que entram, 40% apresentam o fingerprint "Chrome", 25% "Safari",
10% "Firefox", e o resto se divide entre muitos fingerprints raros. Essa distribuição é o
**perfil** do prédio, e o porteiro a anota em dias tranquilos.

**O ataque.** Chegam 300 pessoas extras, cada uma de um endereço diferente e cada uma
educada, sem correr nem gritar. Nenhuma chama atenção sozinha. Mas elas são aparelhos
invadidos, câmeras e roteadores, e usam poucos fingerprints raros, os do software desses
aparelhos.

**Duas formas de reagir:**
- **A óbvia:** barrar o fingerprint mais comum no saguão agora. É o "Chrome", e com isso o
  porteiro barra os próprios clientes e nenhum invasor. Esse é o primeiro resultado do
  artigo: a escolha óbvia é a pior.
- **A nossa:** comparar o saguão de agora com um dia normal e barrar só os fingerprints que
  de repente ficaram muito mais frequentes do que costumam ser.

**As regras do porteiro.** Ele precisa decidir o que é "muito mais frequente". Se for
exigente demais, grupos pequenos de invasores passam: esse é o **piso**. Se for exigente
de menos, ele barra grupos legítimos que chegam juntos, como uma excursão, e isso é um
**falso alarme**. Por isso ajustamos a exigência em dias normais, para que o porteiro dê
falso alarme em no máximo 1% dos períodos de cinco minutos: isso é a **calibração**.

**O alarme da portaria.** O porteiro só confere os fingerprints quando o saguão está
anormalmente cheio. Esse é o **gatilho**, que o artigo chama de *gate*: o porteiro só age quando o gate "abre". Num prédio enorme, 300 pessoas a mais quase não
mudam a lotação, então o alarme não toca e os invasores entram, mesmo que o porteiro
fosse capaz de reconhecê-los. Esse é um dos achados principais do artigo: **o gatilho
decide**.

**Sem alarme (*no gate*).** Se o porteiro conferisse os fingerprints de todo mundo, com o
saguão cheio ou vazio, não haveria gate: a própria lista de fingerprints barrados seria o
alarme. Assim ele pegaria grupos pequenos de invasores que hoje passam, mas também daria mais
falsos alarmes. O artigo examina essa opção depois do dia novo (Tabela VI).

### 0.3 As palavras do artigo, uma por uma

| Termo | O que é | Na analogia |
|---|---|---|
| Sessão | uma conexão de um cliente com o serviço | uma pessoa entrando |
| Origem | o endereço de rede (IP) de onde vem a sessão | de onde a pessoa vem |
| Janela | um intervalo de 5 minutos; um dia tem 288 | um período de observação |
| Endpoint | o serviço atacado (E1 a E4 no artigo) | o prédio |
| Fingerprint TLS, JA4 | o resumo de como o software do cliente abre a conexão segura | o fingerprint |
| Pilha TLS | o software que produz um fingerprint (um navegador, uma biblioteca) | quem ensinou o fingerprint |
| Botnet | os aparelhos invadidos que o atacante controla | os invasores |
| Perfil | a distribuição normal dos fingerprints, medida em dias sem ataque | o dia normal anotado |
| Escopo | o conjunto de fingerprints que o filtro bloqueia | a lista de fingerprints barrados |
| Gatilho (*trigger*) e *gate* | a condição de volume que dispara o alarme. O escopo só age nas janelas em que o gate "abre" | o alarme da portaria |
| *Origin gate* (gate de origens distintas) | o gate do protocolo: abre quando as origens distintas da janela chegam ao percentil 99 dos dias sem ataque | o saguão mais cheio que em 99% dos dias normais |
| *No gate* (sem gate) | não há condição de volume: o escopo roda em toda janela e age sempre que aponta um fingerprint, sendo ele mesmo o gatilho. As figuras chamam isso de *scope alone* e *own trigger* | o porteiro confere todo mundo, com o saguão cheio ou vazio |
| Falso alarme | o escopo bloqueia algo numa janela sem ataque | barrar uma excursão |
| Dano colateral | a parte dos clientes legítimos que o filtro bloqueia | clientes barrados por engano |
| Orçamento (1%) | a meta de falsos alarmes: no máximo 1% das janelas limpas | "errar no máximo 3 vezes por dia" |
| Calibração, nível | ajustar o quão exigente o teste é, olhando dias normais | a regra do porteiro |
| Piso de calibração | o menor ataque que o teste consegue apontar | o menor grupo que o porteiro percebe |
| Limite da razão | fingerprints comuns demais nunca parecem "muito acima do normal" | invasores que falam "Chrome" |
| Frota | clientes legítimos que chegam juntos, como robôs de monitoramento | uma excursão |
| Frotas conhecidas | as frotas que aparecem sempre, postas numa lista de exceções | excursões conhecidas |
| Filtro de fingerprints inéditos | bloqueia fingerprints nunca vistos no perfil | fingerprints que nunca passaram por ali |
| União | o teste junto com o filtro de inéditos | as duas regras juntas |
| z-score | uma regra mais simples que o teste binomial, usada como comparação | outro porteiro, menos cuidadoso |
| Beta-binomial | um modelo estatístico que aceita que as pessoas cheguem em grupos | o porteiro que já espera excursões |
| *Seasonal gate* (gate sazonal) | um gate *post hoc* que compara as origens da janela com a mediana da mesma hora nos dias de calibração | "está cheio para uma segunda às 10h?" |
| Calibração cruzada | calibrar com uns dias e conferir em outros | estudar com uma prova e fazer outra |
| Em amostra | calibrar e medir nos mesmos dias | estudar com a própria prova |
| Dia novo (*held-out*) | um nono dia analisado com tudo fixado antes | a prova final, com questões inéditas |
| *Post hoc* | análise pensada depois de ver o dia novo | ideia que surgiu depois da prova |
| Pico legítimo (*flash crowd*) | muita gente de verdade chegando de uma vez | a liquidação que lota a loja |
| WAF | o firewall de aplicação da Azion, que bloqueia por outras regras | a segurança do prédio vizinho |
| STIX, DOTS, Flowspec, OCSF | padrões para ferramentas trocarem alertas e pedidos de bloqueio | os formulários oficiais |
| Ontologia OWL | um dicionário formal do que é sessão, origem e relação | a planta do sistema |

**Os quatro serviços da Azion** (os *endpoints*):
- **E1**, sinais de monitoramento de usuários reais. São pequenos avisos que os
  navegadores mandam para medir o desempenho das páginas. É o mais movimentado, com cerca
  de 3.000 origens por janela.
- **E2**, o console web, onde os clientes da Azion configuram os serviços (cerca de 62
  origens por janela).
- **E3**, a API (41 origens).
- **E4**, o login único, o SSO (20 origens).

### 0.4 O teste, sem fórmula

O **teste binomial de enriquecimento** faz uma pergunta simples para cada fingerprint: *isto
pode ser sorte?*

Suponha que, num dia normal, 1 em cada 1.000 visitantes tenha o fingerprint X. Numa janela
com 1.300 visitantes, esperamos ver cerca de uma pessoa com X. Se aparecem 101, é como
lançar uma moeda que dá cara uma vez em mil e tirar 101 caras em 1.300 lançamentos: pode
acontecer, mas a chance é tão pequena que ninguém acredita em sorte.

O teste calcula essa **chance de sorte** e aponta X quando duas condições valem juntas:
1. X aparece pelo menos **três vezes mais** do que no perfil;
2. a chance de ver tanto X por sorte é **menor que um limite** (o *nível*).

**Um cuidado extra.** Em cada janela testamos centenas de fingerprints. Se cada um tivesse
chance de 1 em 100 de parecer suspeito por sorte, algum sempre pareceria. Por isso o
limite é dividido pelo número de fingerprints testados (a *correção de Bonferroni*): quanto
mais fingerprints, mais exigente fica cada teste.

**Por que calibrar.** Em dados reais, as frotas chegam juntas: dezenas de robôs de
monitoramento com o mesmo fingerprint, no mesmo minuto. Para o teste, isso parece
improvável, mas é normal. Então ajustamos o limite olhando dias sem ataque: escolhemos o
mais permissivo que ainda erra em no máximo 1% das janelas. Nos serviços com muitas
frotas, esse limite fica extremamente exigente (uma chance de 1 em 10²¹ no E1), e por
isso o piso sobe.

### 0.5 Um exemplo completo, com números redondos (hipotético)

Uma janela normal de um serviço tem **1.000 visitantes legítimos**:
- fingerprint A (um navegador comum): 40%, ou 400 pessoas;
- B: 25%, ou 250;
- C: 10%, ou 100;
- o resto (250 pessoas) se espalha por muitos fingerprints raros, cada um com 1% ou menos;
- entre eles estão X, Y e Z, com 0,1% cada, ou seja, **1 pessoa** cada.

Chega uma botnet de **300 aparelhos**, com 100 em cada um dos fingerprints X, Y e Z. A janela
passa a ter 1.300 visitantes.

**1. A escolha óbvia falha.** O fingerprint mais comum no saguão continua sendo A, com 400
pessoas (X, Y e Z têm 101 cada). Barrar A bloqueia 400 usuários legítimos, ou 40% deles, e
nenhum aparelho da botnet. No artigo, com tráfego gerado, esse número é 39%.

**2. O teste acerta.**
- Para A: esperaríamos 40% de 1.300, ou 520 pessoas, e vemos 400. A está *abaixo* do
  normal, então não entra no escopo.
- Para X: esperaríamos cerca de 1,3 pessoa e vemos 101, quase 80 vezes mais. A chance de
  sorte é praticamente zero, então X entra, e Y e Z também.
- Barrar X, Y e Z bloqueia os 300 aparelhos e 3 usuários legítimos (a 1 pessoa normal de
  cada fingerprint). O dano colateral é de 0,3%, pequeno, mas diferente de zero.

**3. O piso.** Agora a botnet tem só **5 aparelhos** por fingerprint. Em X vemos 6 pessoas em
vez de 1. Isso é seis vezes mais que o normal, mas a chance de sorte ainda é de cerca de
6 em 10.000. Com cem fingerprints testados e o limite dividido entre eles, essa chance não é
pequena o bastante, e X não entra. Ataques pequenos ficam **abaixo do piso**: o teste não
consegue separá-los do acaso.

**4. O limite da razão.** Suponha que os 300 aparelhos usem o fingerprint A, o do
navegador comum. Para A ficar "três vezes mais frequente que o normal", ele teria que ser
120% dos visitantes, o que é impossível. Um bot que imita um navegador comum nunca é
apontado, e isso vale para qualquer tamanho de botnet. No artigo, com 25 fingerprints na
botnet, cada um fica com no máximo 3,6% da janela. Então só os fingerprints com menos de 1,2%
do perfil podem ser apontados, e os 4 a 28 fingerprints mais comuns de cada serviço, que
somam 86% a 94% dos visitantes, estão fora de alcance.

**5. O gatilho.** No E1, uma janela normal tem cerca de 3.000 visitantes. Uma botnet de
300 acrescenta 10%, e o alarme, que só dispara quando a janela está entre as 1% mais
cheias dos dias normais, raramente toca: em só 6% a 13% das janelas para botnets desse
tamanho. Quando o alarme não toca, ninguém confere os fingerprints, e a botnet passa.

### 0.6 O que o trabalho mostrou, em linguagem simples

1. **A escolha óbvia é perigosa.** No tráfego gerado, barrar o fingerprint mais comum
   bloqueia 39% dos usuários e nenhum atacante quando a botnet usa cinco fingerprints ou
   mais. Comparar com o perfil bloqueia 90% da botnet sem dano observado, com até 25
   fingerprints novos.
2. **Em dados reais, a configuração calibrada erra pouco, mas cada erro pesa.** Ela dá
   falso alarme em 0,1% das janelas limpas (5 de 5.643), e cada um bloqueia, em mediana,
   um terço dos clientes daquela janela. Na média, isso dá 0,03% dos clientes por janela.
3. **Há um tamanho mínimo de ataque que se consegue apontar, o piso.**
   - Em fingerprints novos, 139 atacantes por janela.
   - Em fingerprints raros que clientes reais também usam, 254 atacantes no E1 (8% da janela)
     e de 4 a 19 janelas inteiras nos serviços pequenos.
   - Nos fingerprints mais comuns, em expectativa, nunca.

   Abaixo do piso, o recurso do operador é limitar a taxa ou desafiar todos os clientes.
4. **O alarme é o gargalo.** No E1, o teste sozinho bloquearia 90% de uma botnet de um
   décimo da janela, mas o alarme toca em poucas janelas, e a configuração detém só 12%.
5. **Ideias testadas depois recuperam parte disso.** Usar o próprio filtro de fingerprints
   inéditos como alarme detém 90% em fingerprints novos com poucos falsos alarmes. Como foi
   pensado depois de ver o dia novo, isso precisa de um teste novo, marcado antes, para
   valer.
6. **O firewall da Azion não serve de gabarito**, porque bloqueia por outros critérios.
   **E os padrões de troca não sabem dizer "bloqueie este fingerprint":** o STIX só leva a JA4
   numa extensão, o importador do MISP a descarta, e DOTS e Flowspec só filtram campos de
   rede e de transporte.

### 0.7 Como ler cada tabela e figura

Cada item abaixo responde a cinco coisas: a pergunta que a tabela ou figura responde, como
lê-la, um exemplo de leitura com os números do artigo, o que concluir, e o cuidado para não
concluir demais. A ordem é a do artigo.

**Antes de começar: quatro convenções que se repetem**
- **Escala logarítmica.** Nas Figs. 2, 3 e 4, cada marca do eixo vale 10 vezes a anterior
  (10, 100, 1.000). É o que permite ver no mesmo gráfico uma botnet de 25 atacantes e uma de
  3.000. Subir uma marca é multiplicar por 10, e não somar 10.
- **Números como 10⁻²¹.** É 0,000...0001, com a vírgula 21 casas à esquerda: uma chance de
  um em um sextilhão. Na Tabela V, quanto menor esse número, mais exigente o teste e mais
  alto o piso.
- **"254/286".** São duas medidas da mesma coisa separadas por uma barra. A primeira vem da
  calibração em amostra e a segunda da calibração cruzada.
- **Os sinais \* e †.** O \* marca o que é *post hoc*, pensado depois de ver o dia novo, e o
  † marca o que usa calibração cruzada. Um resultado com \* é uma pista para o próximo teste,
  e não uma prova.

---

**Fig. 1, o método numa fileira de caixas**
- **A pergunta:** como o sistema decide quem barrar, a cada cinco minutos?
- **Como ler:** da esquerda para a direita, para cada serviço e cada janela de cinco minutos.
  1. *access log*: cada requisição traz o fingerprint (JA4), a origem e o serviço.
  2. *count query*: uma consulta gerada automaticamente a partir da ontologia (a caixa de
     baixo, com a seta *compiles*) e executada no banco de logs.
  3. *class sizes*: as contagens que a consulta devolve. São quantas origens falam cada
     fingerprint, c(f), o total de origens, n, e os pares de origens na mesma vizinhança de rede
     (/24).
  4. *trigger*: o alarme. Toca quando o número de origens passa do percentil 99 dos dias
     normais, isto é, quando o saguão está mais cheio do que em 99% dos períodos normais.
  5. *scope*: a lista de fingerprints barrados. Entra um fingerprint que está pelo menos 3 vezes
     (ρ = 3) mais frequente do que no perfil e que seria improvável por acaso. Entram também
     os fingerprints inéditos, e saem as frotas conhecidas.
  6. As duas saídas. Se a lista tem fingerprints, o sistema desafia ou bloqueia esses fingerprints
     naquele serviço e exporta a justificativa em STIX 2.1. Se ela sai vazia, o operador cai
     para um limite de taxa ou para um desafio a todos.
  - A caixa larga de baixo, *calibration on attack-free days*, é de onde vêm todos os
    limites: o perfil, os percentis 99, o nível do teste (o maior valor até 0,01 que dispara
    em no máximo 1% das janelas) e as frotas conhecidas. As setas tracejadas mostram que ela
    alimenta o alarme e a lista. Em nenhum ponto entra um rótulo do tipo "isto é ataque".
- **Exemplo de leitura (hipotético):** numa janela com 500 origens, o alarme toca porque 500
  passa do percentil 99. O fingerprint X aparece em 200 delas (40%), mas no perfil tem só 0,1%.
  Ele está 400 vezes acima do normal, muito além das 3 vezes exigidas, e isso seria
  impossível por acaso. X entra na lista, e só quem fala X é barrado.
- **O que concluir:** o método conta e compara com o normal do próprio serviço. Nenhum passo
  precisa saber quem é atacante.
- **Cuidado:** o alarme decide *quando* agir, e a lista decide *quem* barrar. Se o alarme não
  toca, ninguém é barrado, mesmo que a lista estivesse certa. A Fig. 2 mostra o preço disso.

**Tabela I, o que já existe**
- **A pergunta:** o que as outras soluções filtram, o que escolhe o filtro, e quanto ele custa
  aos usuários?
- **Como ler:** cada linha é uma família de soluções. As colunas dizem o que o filtro compara
  (*Filter matches*), o que decide o filtro (*Chosen by*) e quem paga por ele (*Cost to
  legitimate users*).
- **Exemplo de leitura:** o *Blackholing* descarta o tráfego do endereço atacado, e quem paga
  é todo o tráfego desse endereço, inclusive o legítimo. O *Bot management* dos produtos
  comerciais filtra por JA4, mas não publica como escolhe nem quanto custa (*Undisclosed*).
- **O que concluir:** só a última linha filtra pelo fingerprint TLS **e** mede o custo, por
  alarme e por janela.
- **Cuidado:** é uma comparação de desenho, e não de desempenho. Não rodamos essas soluções
  nos nossos dados.

**Tabela II, as quatro configurações de produção**
- **A pergunta:** o que exatamente foi testado nos dados reais?
- **Como ler:** cada linha é uma configuração completa, e cada coluna é uma peça dela.
  - *Gate*: o gatilho de volume, que precisa abrir antes de a lista agir (veja *gate* na seção 0.3). Na regra de referência é Ω ≥ τ, e nas outras é o *origin gate*, o número de origens distintas.
  - *Scope*: a regra que monta a lista.
  - *Background*: o modelo do que é normal, binomial ou beta-binomial.
  - *Exempt*: o que fica fora da lista, ou seja, as frotas conhecidas.
  - *Chosen*: onde as escolhas foram feitas, nos dias de teste ou depois (*post hoc*).
  - *Held-out day*: se o dia novo foi analisado dentro do protocolo fixado antes.
- **Exemplo de leitura:** a linha *Binomial* usa o alarme de origens, a lista do teste mais a
  dos inéditos, o modelo binomial e a isenção das frotas. Ela está *in protocol*, e por isso é
  a configuração recomendada, a única testada no dia novo do jeito fixado antes.
- **O que concluir:** *Binomial* é a configuração principal. *Base rule* e *z-score* servem de
  referência, e *Beta-binomial* é uma alternativa construída depois.
- **Cuidado:** *outside* (nota *a*) quer dizer que o z-score já estava no código antes do dia
  novo, mas não fazia parte do que o protocolo prometia avaliar.

**Tabela III, o tráfego gerado**
- **A pergunta:** quem acerta a botnet quando ela fala 1, 5, 25 ou 100 fingerprints?
- **Como ler:** cada linha é um cenário. M é o número de fingerprints da botnet. *Shared* quer dizer
  fingerprints que clientes reais também usam, e *adversarial* quer dizer que a botnet copia os
  fingerprints mais comuns do serviço. As colunas são:
  - para o teste binomial, *Recall* (quanto da botnet é barrado), FPR (quanto do tráfego
    legítimo é barrado) e F1, uma nota de 0 a 1 que junta as duas coisas;
  - o *Recall* das outras listas: *Modal* (a escolha óbvia), *z-score* e *Unseen* (inéditos);
  - o *Recall* dos modelos que aprendem com rótulos, travados em zero falso positivo.
- **Exemplo de leitura:** na linha M = 25, o teste barra 90,3% da botnet e 0,00% dos
  legítimos, enquanto a escolha óbvia (*Modal*) barra 0,0%, nenhum atacante.
- **Por que nunca passa de uns 90%:** em cada botnet, 10% dos atacantes usam um fingerprint só deles,
  que nenhuma lista pega. É um teto do experimento, e não uma falha do teste.
- **O que concluir:** a partir de cinco fingerprints, a escolha óbvia falha por completo, e as
  listas relativas ao perfil funcionam sem rótulo nenhum.
- **Cuidado:** o tráfego gerado é fácil por construção, porque os fingerprints da botnet nunca
  aparecem no tráfego legítimo. A última linha (*adversarial*, 30,4%) mostra a fronteira: se a
  botnet fala "Chrome", o método pouco pode fazer.

**Tabela IV, a produção com todos os serviços juntos**
- **A pergunta:** nos dados reais, quantos alarmes falsos acontecem, quanto eles custam, e
  quanto da botnet injetada é barrado?
- **Como ler:** há três blocos de linhas: os dias de teste calibrados em amostra, os mesmos dias
  com calibração cruzada (\*), e o dia novo. As colunas se dividem em dois grupos.
  - **Clean windows**, as janelas sem botnet:
    - FA: em quantas das janelas limpas a configuração barrou alguém;
    - *No gate*: o mesmo número sem gate, isto é, se a lista agisse em toda janela sem esperar o gatilho. Serve de diagnóstico;
    - *Coll.*: quando um falso alarme acontece, a fração dos clientes da janela que é barrada
      (a mediana);
    - *Fl. 1k*: em quantas janelas um pico de 1.000 usuários reais dispara o filtro.
  - **New stacks** e **Shared**, com fingerprints novos ou compartilhados: quanto de uma botnet
    injetada é barrado, quando ela tem um décimo da janela típica (0,1×) ou uma janela inteira
    (1×).
- **Exemplo de leitura:** na linha *binomial* dos dias de teste, FA é 0,1, cerca de um falso
  alarme a cada mil janelas (5 em 5.643). Mas cada um barra, na mediana, 32,9% dos clientes
  da janela, um terço. Um pico de 1.000 usuários dispara o filtro em 22,2% das janelas. E de
  uma botnet de um décimo da janela, com fingerprints novos, só 3,0% é barrado.
- **O que concluir:** os falsos alarmes são raros, mas caros quando acontecem. E botnets
  pequenas passam, como a Fig. 2 explica.
- **Cuidado:** com poucos eventos, a incerteza é grande. O intervalo de 95% dos 5 falsos
  alarmes vai de 0,03% a 0,21%. O dia novo teve 2 falsos alarmes em 1.152 janelas: é
  consistente com os dias de teste, mas traz pouca evidência nova.

**Tabela V, o piso por serviço**
- **A pergunta:** a partir de que tamanho a botnet é apontada?
- **Como ler:** há uma linha por serviço.
  - n₀ é o tamanho da janela típica, em origens.
  - λₑ é o nível calibrado. Quanto menor, mais exigente o teste: 10⁻²¹ é muito mais exigente
    que 10⁻².
  - As colunas de piso dão quantos atacantes por janela a botnet precisa ter para o teste
    apontar um fingerprint típico dela. Cada uma vem como "em amostra / cruzado", para fingerprints
    novos (*new*) e compartilhados (*shared*), com o binomial e com o beta-binomial (\*,
    *post hoc*).
- **Exemplo de leitura:** o E1 tem uma janela típica de 2.983 origens, e com fingerprints
  compartilhados o piso é de 254 atacantes, uns 8% da janela. O E2 tem janela de 62 origens e
  precisa de 1.090 atacantes, mais de 17 vezes o seu tráfego normal.
- **Por que o 139 aparece tanto:** é o piso dos fingerprints novos, fixado pelo filtro de inéditos,
  e ele não depende do nível. O filtro exige 5 origens por fingerprint. Com 25 fingerprints e 90% da
  botnet neles, isso dá 5 × 25 ÷ 0,9 ≈ 139 atacantes.
- **O que concluir:** nos serviços pequenos, uma botnet em fingerprints compartilhados só é
  apontada quando é muito maior que o tráfego normal. Abaixo do piso, o operador precisa de
  um limite de taxa ou de um desafio.
- **Cuidado:** o piso não é um degrau. Abaixo dele, o teste ainda pega os fingerprints que o acaso
  deixou maiores, e por isso as curvas da Fig. 2 sobem aos poucos.

**Fig. 2, o que a configuração barra conforme o tamanho da botnet**
- **A pergunta:** a lista reconhece uma botnet pequena, então por que ela não é barrada?
- **Como ler:** há um painel por serviço, do E1 ao E4. O eixo horizontal traz os atacantes por
  janela, em escala logarítmica (10, 100, 1.000), e o vertical, a porcentagem da botnet que é
  barrada. Cada painel tem só duas linhas e a área entre elas.
  - Tracejada (*the scope alone would block*): quanto a lista de fingerprints barraria se
    pudesse agir em toda janela.
  - Cheia, com bolinhas (*the configuration stops*): quanto o sistema barra de verdade, porque
    ele só age quando o gate abre.
  - Área cinza entre as duas (*lost to the gate*): o que se perde porque o gate não abriu.
  - Triângulo vazado no eixo: um décimo da janela típica, a botnet "de um décimo" do texto.
- **Exemplo de leitura (E1):** no triângulo vazado, com cerca de 300 atacantes, a tracejada
  está em 90% e a cheia em 12%. A lista reconheceria 90% da botnet, mas só 12% é barrado. O
  motivo é que 300 pessoas a mais num saguão de 3.000 quase não mudam a lotação, e o gate só
  abre em 6% a 13% das janelas.
- **Exemplo de leitura (E2 a E4):** no E2 e no E3 as duas linhas andam quase juntas. Nesses
  serviços, 100 atacantes já valem várias janelas típicas: o saguão enche e o gate abre. O
  limite é outro, o tamanho mínimo que a lista reconhece, que é o piso (Tabela V). No E4, com
  só 20 origens por janela, sobra uma área menor, para botnets de até umas 30 origens que ainda
  não enchem o saguão.
- **O que concluir:** reconhecer a botnet não basta. No serviço grande, quem limita o que é
  barrado é o gate, e nos pequenos é o piso.
- **Cuidado:** é uma botnet injetada, de uma forma só (25 fingerprints novos, divididos por
  igual). A taxa do gate e as pilhas compartilhadas ficaram fora da figura. Elas estão no texto,
  na Tabela V e na seção 16.4 deste guia.

**Tabela VI, os alarmes alternativos**
- **A pergunta:** trocar o alarme recupera a botnet pequena sem encher o dia de falsos alarmes?
- **Como ler:** os blocos de linhas são três alarmes.
  - *Origin gate*: o gate de origens distintas, o do protocolo.
  - *Seasonal gate*: o gate sazonal, que compara o saguão com a mesma hora dos dias anteriores (\*).
  - *No gate*: sem gate. A lista roda em toda janela e é o próprio gatilho (\*).

  Dentro de cada bloco há três listas: o binomial, o beta-binomial cruzado (†) e os inéditos.
  As colunas trazem:
  - os falsos alarmes no E1 e o maior valor entre os serviços pequenos (E2 a E4), nos dias de
    teste (*test*) e no dia novo (*held*);
  - *New* e *Shared*: quanto se barra da botnet de um décimo da janela do E1;
  - *Fl. 1k* e *Coll.*, como na Tabela IV.
- **Exemplo de leitura:** na linha *No gate / unseen*, os falsos alarmes ficam em 0,28% no E1
  e em no máximo 0,42% nos serviços pequenos, dentro do orçamento de 1%. Ela barra 89,6% da
  botnet de um décimo com fingerprints novos, e 0,0% com fingerprints compartilhados.
- **O que concluir:** para fingerprints novos, o melhor candidato é usar os inéditos como alarme
  próprio. Para os compartilhados, o beta-binomial cruzado atrás do alarme sazonal chega a
  15,1%. É essa comparação que o bloco de 14 dias, fixado antes, vai testar.
- **Cuidado:** tudo o que tem \* foi examinado depois do dia novo. É uma hipótese para o
  próximo teste, e não um resultado confirmado.

**Fig. 3, o equilíbrio de cada configuração**
- **A pergunta:** qual configuração faz o melhor acordo entre falsos alarmes e detecção?
- **Como ler:** há dois painéis, um para fingerprints novos e outro para compartilhados. O eixo
  horizontal traz os falsos alarmes (% das janelas limpas), em escala logarítmica de 0,01 a
  10, e o vertical, a porcentagem barrada de uma botnet de 100 atacantes.
  - O melhor lugar é **em cima e à esquerda**: muita detecção e poucos falsos alarmes.
  - Cada forma é uma configuração, conforme a legenda. Nela, *scope alone* e *own trigger* querem dizer sem gate: a lista, ou o filtro de inéditos, é o próprio gatilho.
  - Preto são os dias de teste, e cinza é a calibração cruzada, com uma seta saindo do ponto em
    amostra.
  - A linha tracejada vertical é o orçamento de 1%: o que fica à direita dela passa do orçamento.
  - O dia novo ficou fora da figura. Com o gate quase sem abrir, as taxas zero dele cairiam no
    canto "ideal" sem querer dizer nada. Os números dele estão nas Tabelas IV e VI.
- **Exemplo de leitura:** o losango (binomial, a do protocolo) fica perto de 0,1% de falsos
  alarmes e de 38% da botnet em fingerprints novos. O X (a lista sozinha, com beta-binomial) chega
  a uns 86%, mas com cerca de 4,5% de falsos alarmes, bem à direita do orçamento. Com a
  calibração cruzada (a seta), ele cai para cerca de 1,1% e 66%, ainda um pouco além do
  orçamento.
- **O que concluir:** nenhum ponto chega ao canto ideal, porque ganhar detecção custa falsos
  alarmes. As setas mostram quanto do resultado em amostra era otimismo.
- **Cuidado:** os 100 atacantes estão somados sobre os quatro serviços, e o total é puxado
  pelos pequenos, onde 100 atacantes já valem várias janelas típicas.

**Fig. 4 (Apêndice D), o custo de processamento**
- **A pergunta:** o método aguenta rodar em tempo real numa CDN?
- **Como ler:** o eixo horizontal traz as sessões ativas na janela, de 100 a 100.000, e o
  vertical, o tempo em segundos, de um milionésimo de segundo até 100 segundos. Os dois eixos
  estão em escala logarítmica.
  - Há quatro linhas: a admissão, feita a cada requisição, e a agregação, feita uma vez por
    janela.
  - Cada uma é medida de dois jeitos: guardando as ligações entre pares de sessões (cinza) ou
    só contando classes (preto).
  - As pontilhadas são inclinações de referência. *Slope 2* quer dizer que o tempo quadruplica
    quando as sessões dobram, *slope 1* que ele dobra, e *constant* que ele não muda.
- **Exemplo de leitura:** a agregação que guarda pares leva cerca de 53 s com 1.000 sessões,
  o que é inviável. Contando classes, ela leva 0,33 s. A admissão por contagem fica em cerca
  de 0,4 milionésimo de segundo, sem crescer, até 100.000 sessões.
- **O que concluir:** contar classes deixa o custo proporcional ao tráfego, e guardar pares o
  deixa quadrático. Por isso o método conta.
- **Cuidado:** a medição usa uma biblioteca em Python (rdflib), então os tempos são um teto.
  Um motor como o Jena seria mais rápido.

**Listagem 1 (Apêndice D), a cadeia de evidência**
- **A pergunta:** o que o sistema entrega ao operador quando dispara?
- **Como ler:** é um registro em JSON-LD com as seguintes partes:
  - a regra que disparou (*CoordinatedHTTPFlood*);
  - o tamanho do grupo (1.991 origens) e a massa Ω (1.303.422,8);
  - a divisão da massa por tipo de ligação: pares com o mesmo fingerprint (peso 1,0), o mesmo
    serviço (0,6) e a mesma vizinhança /24 (0,3);
  - por fim, a lista barrada, com o serviço e os 25 fingerprints.
- **Exemplo de leitura:** os 1.981.045 pares ligados pelo mesmo serviço, vezes 0,6, dão 91%
  de Ω. É por isso que o artigo diz que Ω mede sobretudo volume.
- **O que concluir:** o operador vê o que foi barrado e por quê, numa forma que outras
  ferramentas conseguem ler.

### 0.8 O que recomendamos, e por quê

- **Agora:** usar a configuração binomial em todos os serviços, porque é a única,
  atrás do gatilho de origens, que foi testada num dia inédito com tudo fixado antes.
  Abaixo do piso, o recurso é limitar a taxa ou desafiar os clientes. No console, onde
  caíram os dois falsos alarmes do dia novo, um desafio pode ser a primeira resposta mais
  segura.
- **Depois:** um teste novo, planejado antes, em semanas de dados, comparando o filtro de
  inéditos como alarme próprio (a base) com as duas alternativas promissoras. Só esse
  teste pode transformar as ideias *post hoc* em recomendação.

### 0.9 Os limites, ditos com honestidade

- A botnet injetada tem um só formato: 25 fingerprints, divididos por igual.
- São nove dias de um único operador, poucos para ver um ciclo semanal.
- Cinco escolhas do método foram feitas nos mesmos dias em que ele foi medido. Só o dia
  novo as testa, e ele é um teste fraco.
- Não existe captura pública de um ataque furtivo real para testar.
- Um bot que imita o fingerprint de um navegador comum escapa. É a fronteira declarada do
  método.
- A avaliação é offline, sobre contagens exportadas. Uma implantação ao vivo ainda
  precisa ser construída.
- Não medimos se um ataque no tamanho do piso derrubaria o serviço, nem um atacante que
  tente enganar o perfil.

### 0.10 Por que o artigo não fala mais em "knowledge graph"

O artigo prometia que um grafo de conhecimento detecta ataques melhor e explica o porquê.
Os testes não confirmaram isso, por três motivos:
1. **O grafo não detectava melhor do que uma planilha.** A vantagem vinha de contar
   quantas conexões têm o mesmo fingerprint TLS, e uma tabela simples faz a mesma conta.
   Em ataques reais de laboratório, olhar cada conexão sozinha já bastava.
2. **Detectar era a parte fácil.** Contar visitantes distintos percebe o ataque. O difícil,
   e que ninguém media, é decidir quem bloquear sem bloquear os usuários.
3. **Um artigo só pode prometer o que os dados mostram.** Com a promessa antiga, as
   revisões simuladas ficavam em "rejeição fraca". Com a nova, chegaram a "aceitação
   fraca".

O grafo ficou como a especificação: dele sai a consulta que roda nos logs e o formato do
bloqueio exportado. A explicação completa, com analogias e os números, está em
**`por-que-mudamos.md`**, nesta mesma pasta.

---

## Sumário

**Parte 0. Para entender sem matemática**
0.1 O trabalho em cinco frases · 0.2 Uma analogia · 0.3 As palavras do artigo · 0.4 O
teste, sem fórmula · 0.5 Um exemplo completo · 0.6 O que o trabalho mostrou · 0.7 Como
ler cada tabela e figura · 0.8 O que recomendamos · 0.9 Os limites · 0.10 Por que não "knowledge graph"

**Parte I. A ideia**
1. O artigo em um minuto
2. O problema
3. Vocabulário
4. O modelo de ameaça

**Parte II. O método**
5. O método em uma figura (Fig. 1)
6. O gatilho
7. O escopo
8. A calibração
9. O piso de calibração
10. Os dois remédios para o piso
11. A ontologia como especificação

**Parte III. A avaliação**
12. As fontes de tráfego
13. As configurações avaliadas em produção (Tabela II)
14. As métricas

**Parte IV. Os resultados**
15. Tráfego gerado (Tabela III)
16. Tráfego de produção (Tabelas IV, V e VI, Figs. 2 e 3)
17. Especificação, troca e custo (Fig. 4)

**Parte V. Recomendações, limites e consulta**
18. Qual configuração recomendar, e os limites
19. Os números do artigo, num só lugar
20. Glossário
21. Onde está cada coisa

**Elementos flutuantes do artigo.** Tabela I: trabalhos relacionados. Tabela II: as
configurações avaliadas em produção. Tabela III: o escopo no tráfego gerado, com a
coluna do fingerprint modal. Tabela IV: as configurações em produção, todos os endpoints.
Tabela V: o piso de calibração das configurações. Tabela VI: os escopos atrás de cada
gatilho, com o filtro de inéditos sozinho (Seção V-C). A tabela por endpoint saiu na rodada
29 (os valores estão na seção 16.9), e a da regra por janela virou uma frase do Apêndice E
na rodada 23. Fig. 1: o pipeline de escopo calibrado. Fig. 2: o
que a configuração binomial detém, por tamanho da botnet e por endpoint (Seção V-C). Fig.
3: os pontos de operação em produção (Seção V-C). Fig. 4: o custo (Apêndice D). Listagem
1: a cadeia de evidência de uma campanha canônica (Apêndice D). A antiga listagem com a
regra SWRL e a agregação SPARQL saiu do artigo na rodada 18 (seção 11.4).

---

# Parte I. A ideia

## 1. O artigo em um minuto

Um ataque DDoS lento e distribuído na camada de aplicação mantém cada origem abaixo de
qualquer limite por origem. Perceber que o endpoint está sob ataque é a parte fácil: o
número de origens distintas cresce. A decisão difícil é o **escopo** da mitigação:
quais clientes desafiar ou bloquear, com um filtro estreito o bastante para poupar os
usuários legítimos do serviço atacado.

O artigo escolhe o escopo pela **fingerprint TLS** (JA4) dos clientes. Um **teste
binomial de enriquecimento** aponta os fingerprints super-representados entre as origens
do alarme em relação a um **perfil** do tráfego normal do endpoint. O nível do teste é
um **quantil empírico** de janelas sem ataque: o maior nível, até 0,01, com que o escopo
produziria filtro em no máximo 1% delas.

O que se mediu, em seis pontos:

1. **No tráfego gerado**, a escolha natural, o fingerprint mais comum do alarme, bloqueia
   0% dos atacantes e 39% do tráfego legítimo quando a botnet se espalha por cinco
   pilhas TLS. Os escopos relativos ao perfil bloqueiam 90% de uma botnet de até 25
   pilhas ausentes do tráfego legítimo, sem dano colateral observado e sem rótulos.
2. **Em oito dias de quatro endpoints dos serviços da própria CDN**, a configuração
   binomial (o teste com as frotas conhecidas isentas, unido a um filtro de fingerprints inéditos, atrás de um gatilho de origens distintas), a que foi fixada para o dia novo,
   dá falso alarme em
   0,1% das janelas limpas dos dias em que foi escolhida, e seus falsos alarmes bloqueiam uma mediana de um terço dos
   clientes da janela. O escopo sozinho dispara em 2,2% contra a meta de 1%.
   Na configuração binomial, gatilho e escopo erram juntos dentro do acaso; na
   beta-binomial e no z-score, bem mais do que se fossem independentes.
3. **Frotas legítimas**, clientes que se ativam juntos, elevam um **piso de
   calibração** (no SSO a maior parte dele vem do tamanho da janela: 56 atacantes no
   nível nominal, 84 calibrado). Uma botnet de 25 pilhas em fingerprints raros que clientes reais também
   usam só é apontada acima de 8% da janela do endpoint mais movimentado e de 4 a 19
   janelas inteiras nos demais. Nas posições 11 a 35 do perfil, ela nunca é apontada no E1
   nem no E2. Nos fingerprints que carregam a maior parte das origens, em
   expectativa, ela não é apontada nunca: a fatia esperada de uma pilha fica abaixo de 0,9/M da janela, e uma
   botnet de 25 pilhas não deve enriquecer nenhum fingerprint acima de 0,9/(ρM) = 1,2%.
   O piso cresce com o número de pilhas: no E1, 50, 254 e 1.026 atacantes para 5, 25 e
   100 pilhas.
4. **Apontar não é deter (Fig. 2).** Onde o escopo aponta uma botnet pequena, o gatilho de
   origens raramente dispara: só 12% de uma botnet de um décimo da janela do endpoint
   mais movimentado é detida. Examinado *post hoc*, o filtro de fingerprints inéditos
   como gatilho próprio detém ali 90% dela em pilhas novas, porque cada pilha dela tem ao
   menos k_min origens, e os seus falsos alarmes ficam dentro do orçamento em todo
   endpoint. A alternativa, a beta-binomial cruzada atrás de um gatilho sazonal, detém
   15% dela em pilhas compartilhadas, mas só 20% em pilhas novas no E1.
5. **Os pontos *post hoc* e os limites.** Uma referência **beta-binomial**, construída
   depois de o dia novo ter sido lido, quase cumpre a meta na calibração cruzada e baixa o
   piso para 6% e no máximo 4,4 janelas. Os veredictos do WAF deste operador não servem de
   rótulo. O dia novo, analisado com a configuração fixada de antemão, não contradiz a
   taxa de falso alarme, mas é um teste fraco e passou sobretudo porque o gatilho quase
   não abriu.
6. **Nenhum padrão examinado expressa o escopo**, um filtro sobre fingerprints JA4, no seu
   vocabulário central. O STIX 2.1 só leva a JA4 numa extensão, que o importador do MISP
   descarta. O OCSF registra JA4 em eventos de rede desde a versão 1.3.0 (2024) e nas
   evidências de achados desde a 1.4.0 (2025), mas não define filtro nem remediação sobre
   elas. Os filtros do
   DOTS e do Flowspec casam só campos de rede e transporte. A **ontologia OWL** especifica as
   contagens que a decisão lê e o escopo exportado, e a consulta compilada a partir dela
   reproduz as contagens de origens e de pares /24 do operador.

As três contribuições declaradas na Seção I são:
1. **Escopo relativo ao perfil.** No tráfego gerado, os escopos relativos ao perfil barram o
   ataque sem rótulos, enquanto o fingerprint mais comum do alarme barra usuários e nenhum
   atacante assim que a botnet usa várias pilhas.
2. **Um método de calibração do escopo.** O teste é calibrado por serviço para um orçamento
   de falsos alarmes de 1% das janelas sem ataque. Essa calibração define o **piso de
   calibração**, o tamanho de botnet a partir do qual o teste aponta uma pilha típica. Os
   dois são avaliados em oito dias de quatro serviços da CDN e num dia novo.
3. **A ontologia de sessão como especificação.** Uma ontologia OWL especifica as contagens
   que a decisão lê e o escopo que ela exporta. A consulta do banco de logs é compilada a
   partir dela, e por isso um sinal novo de igualdade entra sem mudar o código. Nenhum
   padrão de troca examinado expressa o filtro JA4 resultante no seu vocabulário central.

Os demais resultados apoiam essas três contribuições, e o artigo os detalha ao longo do texto:
o limite da razão, os gatilhos *post hoc*, a fronteira do método, a rotatividade de
fingerprints e os veredictos do WAF.

## 2. O problema

### 2.1 O ataque

O DDoS de aplicação tem dois extremos. Num deles está o volume: o HTTP/2 Rapid Reset
(CVE-2023-44487) levou picos de mitigação a 398 milhões de requisições por segundo, um
volume que capacidade e *scrubbing* absorvem. No outro estão as inundações distribuídas
de baixa taxa, alvo do artigo: o *Slow HTTP DoS* distribuído e variantes por taxa que
ainda seguram conexões abertas, como HULK e GoldenEye. Cada origem manda pouco. O dano
é a soma: cada sessão ocupa uma conexão e um *worker* como uma sessão legítima.

### 2.2 Por que limites por origem falham

Se o atacante controla K = 1.000 dispositivos e cada um se comporta como um usuário,
nenhum limite por IP dispara sem bloquear usuários. Uma campanha furtiva também molda
cada sessão para parecer legítima nos sinais por sessão que os detectores usam, como
duração da conexão e entropia de rotas. O que sobra de discriminante está **entre** as
sessões: o mesmo fingerprint de cliente repetida em muitas origens que convergem num
endpoint.

### 2.3 A decisão é o escopo

O operador precisa decidir quais clientes bloquear, com que evidência e com que custo
para os usuários legítimos. Precisa também saber, antes do ataque, onde nenhum filtro
desse tipo pode ser construído, para então recorrer a um limite de taxa ou a um desafio
a todos os clientes. O custo de um escopo é o **dano colateral**: a fração do tráfego
legítimo que cai dentro do filtro.

### 2.4 O que já existe (Seção II, Tabela I)

A Tabela I compara as abordagens por três perguntas: o que o filtro casa, quem o
escolhe e quanto custa aos usuários legítimos.

| Abordagem | O filtro casa | Escolhido por | Custo aos legítimos |
|---|---|---|---|
| Controle de taxa por agregado (Pushback, ACC-Turbo) | Agregado definido por cabeçalhos | Congestionamento ou escore do agregado | Limitado em taxa junto com o agregado |
| *Blackholing* e *blackholing* avançado (Stellar) | Prefixo de destino, ou campos de cabeçalho | A rede atacada | Todo o seu tráfego, ou menos com filtros finos |
| Filtragem por origem | Prefixos de origem | Otimização com orçamento de filtros | Tráfego dos prefixos filtrados |
| Extração de anomalias (URCA, regras de associação) | Valores de atributos de fluxo | Super-representação no tráfego anômalo | Nenhum (só diagnóstico) |
| Geração de assinaturas (Hamsa) | *Tokens* de *payload* | Cobertura contra um conjunto normal | Falsos positivos no tráfego normal |
| Quebra-cabeças (Kill-Bots) | Todo cliente sob ataque | O custo que o cliente paga | Um desafio para cada um |
| DOTS, Flowspec | Campos de rede e transporte | Quem pede a mitigação | O do filtro transportado |
| Detectores L7 (PCA, ML supervisionado, KLAGE) | Nada (só veredicto) | Perfil ou modelo aprendido | Só a FPR de detecção |
| Gestão de bots (sinais JA4) | JA4 | Não divulgado | Não divulgado |
| **Este trabalho** | Fingerprints TLS (JA4) | Enriquecimento calibrado contra o perfil | Medido por alarme e por janela |

As distribuições de atributos (a entropia de endereços e portas, de Lakhina, Crovella e
Diot) detectam e classificam anomalias, e a extração de anomalias faz a pergunta mais
próxima da do teste (que valores estão super-representados no tráfego anômalo), mas sobre
atributos de fluxo. O DDoS-Shield agenda cada sessão pela sua suspeita, o desvio em
relação a perfis legítimos de carga, pesando o atraso imposto aos usuários legítimos.
Picos legítimos se distinguem de inundações pela forma como os pedidos se espalham pelos
documentos do site (Xie e Yu). Todos esses trabalhos operam sobre atributos de rede,
fluxo, sessão ou *payload*. O canal de dados do DOTS
instala filtros em campos de rede e transporte, como o Flowspec: nenhum dos dois expressa
um fingerprint de cliente como a JA4. A
fronteira que o artigo traça é esta: nenhuma abordagem publicada deriva um escopo sobre
fingerprints de clientes de aplicação por um teste calibrado contra o tráfego do próprio
serviço, com o dano colateral e os limites medidos.

## 3. Vocabulário

- **TLS e ClientHello.** O ClientHello é a primeira mensagem do *handshake* TLS,
  enviada pelo cliente. Ela lista versões, conjuntos de cifras, extensões e protocolos
  de aplicação (ALPN). Seu conteúdo depende da biblioteca TLS do cliente, não do usuário.
- **JA4.** Um fingerprint do ClientHello. A primeira parte resume transporte,
  versão, presença de SNI, número de cifras, número de extensões e o primeiro ALPN,
  abreviado; as duas outras partes são *hashes* truncados das cifras ordenadas e das
  extensões ordenadas (com os algoritmos de assinatura). O
  formato é `t13d1516h2_…_…`; o gerador usa valores sintéticos como
  `t13d1516h2_synth_0001_00`.
- **Fingerprint.** O valor JA4 de um cliente. O guia usa o termo em inglês, como o artigo.
- **Pilha TLS** (*stack*). A biblioteca TLS com sua configuração, que produz um
  fingerprint. Muitas aplicações construídas sobre a mesma biblioteca compartilham um
  fingerprint, e é isso que faz de uma pilha um escopo e também o que o limita. Uma botnet
  de roteadores, câmeras e DVRs se espalha por várias pilhas; M é o número de pilhas.
- **Origem.** Um endereço de origem distinto. É a unidade de contagem de tudo: o gatilho,
  as classes e o teste contam origens, não conexões nem requisições.
- **Sessão.** Uma sessão de aplicação, a classe central da ontologia. No gerador cada
  origem carrega uma sessão, então origens e sessões coincidem.
- **Endpoint.** O serviço atacado. A decisão é tomada por endpoint.
- **Janela.** Cinco minutos: 288 janelas por dia. **Janela limpa** é uma janela sem
  ataque injetado.
- **Frota legítima** (*fleet*). Clientes legítimos que se ativam juntos, como uma frota
  de sondas de cerca de vinte clientes ativa só em horário comercial ou uma tarefa
  periódica em minutos fixos de cada hora.
- **Pico legítimo de acesso** (*flash crowd*). Muitos usuários reais chegando de uma vez.
- **WAF.** O *web application firewall* do operador, que bloqueia clientes por regras
  próprias.
- **CDN.** Rede de distribuição de conteúdo. Os dados de produção vêm dos serviços da
  própria Azion.
- **Perfil.** A contagem de origens por fingerprint no tráfego normal do endpoint, fora de
  episódios de ataque.
- **Referência** (*background*). A distribuição que o teste supõe para as contagens sob
  tráfego normal: binomial ou beta-binomial.
- **Escopo.** O conjunto de fingerprints a que a mitigação se aplica. "Produzir um filtro"
  é o escopo não ser vazio; "apontar" uma pilha é incluí-la no escopo.
- **Desafio.** Uma prova pedida ao cliente antes de um bloqueio. O artigo recomenda
  aplicar o escopo como desafio, porque um falso alarme atinge uma frota.

- **Gatilho e *gate*.** O gatilho é o que dispara o alarme numa janela. O artigo chama de *gate*
  o gatilho de volume que precisa "abrir" antes de o escopo poder barrar alguém. Com o gate
  fechado, nada é barrado, mesmo que o escopo tenha apontado a botnet. Há três gates:
  - o *origin gate*, ou gate de origens distintas, que abre quando n chega ao percentil 99 das
    janelas de calibração (seção 6.1). É o da configuração recomendada;
  - o gate de Ω, Ω ≥ τ_cluster, que é o da regra de referência (seção 6.2);
  - o *seasonal gate*, ou gate sazonal, *post hoc*, que compara n com a mediana da mesma hora
    nos dias de calibração (seção 6.1).
- ***No gate*** (sem gate). Não há gatilho de volume: o escopo roda em toda janela e, sempre
  que aponta um fingerprint, o filtro age. O escopo vira o próprio gatilho, e as legendas das
  Figs. 2 e 3 chamam isso de *scope alone* e *own trigger*.
  - Na Tabela IV, a coluna *No gate* é um diagnóstico: mostra em quantas janelas limpas o
    escopo apontaria algo se não esperasse o gate.
  - Na Tabela VI e na Fig. 3, *No gate* é uma configuração *post hoc*. Ela pega muito mais das
    botnets pequenas, mas também dispara mais vezes.

## 4. O modelo de ameaça (Seção III-A)

**O defensor** opera a aplicação atacada. Por requisição, ele vê o ClientHello (logo, a
JA4), o endereço e o prefixo ou ASN de origem, o endpoint, o instante de chegada e o
material de identidade que a aplicação expõe. Ele não vê o canal de controle da botnet
nem quais origens estão coordenadas, mas pode traçar o perfil do próprio tráfego fora
dos episódios de ataque.

**O atacante** controla K dispositivos comprometidos e pode moldar cada sessão para ser
estatisticamente indistinguível de uma legítima (a hipótese furtiva da avaliação).
Tempos, identidades e *payloads* podem ser variados, trocados ou aleatorizados. O dano é
capacidade esgotada: nenhuma taxa por sessão sobe, e o agregado só cresce na medida da
fatia da campanha no tráfego do endpoint.

**Por que a pilha TLS é difícil de trocar.** Um bot fala TLS pela biblioteca que seu
dispositivo ou sua ferramenta traz, e botnets de dispositivos comprometidos abrangem
muitos modelos de roteador, câmera e DVR (como a Mirai). Apresentar o ClientHello de um
navegador exige uma biblioteca de imitação mantida em dia com as versões dos
navegadores.

**A fronteira.** Bots que apresentam fingerprints comuns, como fazendas de navegadores
*headless* ou bots sobre bibliotecas de imitação de TLS, ficam fora do modelo. O artigo
os avalia como a fronteira do método (o modo adversarial), no gerador e em produção.

A consequência que atravessa o artigo: o poder do método vem de as pilhas da botnet serem
raras no tráfego legítimo do endpoint.

---

# Parte II. O método

## 5. O método em uma figura (Fig. 1)

A Fig. 1 mostra o pipeline:

```
log de acesso (por requisição: JA4, origem, endpoint)
   ──► consulta de contagem compilada da ontologia
   ──► por endpoint e janela: origens por JA4 c(f), origens n, pares no mesmo /24
   ──► gatilho: origens distintas ≥ p99, ou Ω(S) ≥ τ
   ──► escopo: toda f com c(f)/n ≥ ρ·b(f) e P[X ≥ c(f)] < λ_e/|F|, ∪ inéditos, − frotas conhecidas
   ──► desafio ou bloqueio de f no endpoint, com a cadeia em STIX 2.1
       (nada apontado ──► limite de taxa ou desafio a todos)

ontologia da sessão (por sub-relação: a propriedade que iguala, o peso, a unidade) ──► compila a consulta
dias sem ataque, sem rótulos ──► calibração: o perfil b(f) (e φ(f) na beta-binomial), os
   limiares no p99, o maior λ_e ≤ 0,01 com filtro em no máximo 1% das janelas, as frotas conhecidas
```

Tudo o que a decisão lê é uma contagem de origens distintas por classe, algo que um
armazenamento de logs calcula com uma agregação simples. Todo limiar e todo nível vêm de
dias sem ataque.

## 6. O gatilho (Seção III-B)

### 6.1 O gatilho de origens distintas

Seja S o conjunto das sessões a um endpoint e numa janela, e n o número de origens
distintas delas.

> **O gatilho dispara quando n ≥ k_min = 5 e n alcança o seu percentil 99 nas janelas sem ataque.**

É o gatilho da avaliação em produção. Por construção, ele dispara em cerca de 1% das
janelas de calibração. Nos dias seguintes dispara em 3,0% das janelas limpas (5,4% no
endpoint mais movimentado).

**O gatilho sazonal**, examinado depois do dia novo, compara n com a mediana das janelas
da mesma hora do dia nos dias de calibração:

> **r = n / mediana(n na mesma hora, nos dias de calibração); dispara quando r ≥ r\*,
> com r\* o percentil 99 de r nas janelas de calibração, nunca abaixo de 1.**

É o mesmo orçamento de 1%. Exemplo hipotético: se às 14h a mediana do endpoint é de 3.000
origens e r\* = 1,15, o gatilho abre a partir de 3.450 origens; às 4h, com mediana de
1.200, abre a partir de 1.380. Um limiar único, calibrado no pico do dia, deixa passar a
botnet que chega de madrugada. Nos dias de teste, o sazonal sozinho também dispara em 3,0%
das janelas limpas, como o de origens.

**O escopo como gatilho próprio** dispensa o gatilho: a configuração dispara sempre que o
escopo aponta um filtro. O nível λ_e já é calibrado para que o escopo sozinho dispare em
1% das janelas de calibração, então esse gatilho tem o seu próprio orçamento.

### 6.2 A massa de coordenação Ω

A regra básica, o termo de comparação do protocolo, dispara pela massa de coordenação da
regra `CoordinatedHTTPFlood` da ontologia. A Seção III-B a define em palavras; a equação
e os pesos estão no Apêndice A:

> **Ω(S) = Σᵢ wᵢ · |Eᵢ(S)|**

- Eᵢ(S) é o conjunto de pares de origens distintas {o(s_a), o(s_b)} cujas sessões a
  sub-relação i liga (mesma JA4, mesmo endpoint, mesmo /24);
- wᵢ é o peso da sub-relação (seção 11);
- o limiar τ_cluster é o percentil 99 de Ω nas janelas sem ataque.

Cada par de **origens** conta uma vez, então as muitas conexões de um cliente não se
passam por coordenação.

As três sub-relações exercitadas são igualdades, e uma igualdade divide as origens em
classes. Dentro de uma classe de tamanho n_k, todos os pares estão ligados:

> **|Eᵢ(S)| = Σₖ C(n_k, 2) = Σₖ n_k(n_k − 1)/2**

Exemplo: cinco origens com a mesma JA4 formam C(5, 2) = 10 pares; mil origens formam
499.500.

### 6.3 Exemplo: a Listagem 1

A Listagem 1 (Apêndice D) é a cadeia de evidência de uma campanha canônica (M = 25, K = 1.000), com
um *cluster* de 1.991 origens:

| Sub-relação | Peso | Pares | Contribuição |
|---|---|---|---|
| Mesmo endpoint | 0,6 | C(1.991, 2) = 1.981.045 | 1.188.627,0 |
| Mesma JA4 | 1,0 | 114.710 | 114.710,0 |
| Mesmo /24 | 0,3 | 286 | 85,8 |
| **Ω** | | | **1.303.422,8** |

O termo de endpoint é 91% de Ω.

### 6.4 Por que Ω é volume

Todas as origens de uma janela estão no mesmo endpoint, então o termo de endpoint é
0,6 · C(n, 2), uma função só de n. Na escala da janela, Ω mede volume. Três medidas
confirmam:

- com pesos uniformes, Ω pega pelo menos tantas janelas de ataque quanto com os pesos da
  ontologia (78,9% e 85,7%), e sem o termo de endpoint pega só 33,3% e nenhuma, embora
  ainda sinalize 53–100% dos picos legítimos (Apêndice E);
- com os pesos da ontologia, Ω sozinho dispara em 80–100% dos picos legítimos gerados
  (Apêndice E; a antiga Tabela VIII virou uma frase na rodada 23);
- em produção, das 181 janelas limpas em que um dos dois dispara, o gatilho de origens e Ω
  disparam juntos em 136.

Por isso o gatilho implantado é a contagem de origens, e **o discriminador vem do
escopo**. O termo TLS de Ω ainda engana de um jeito específico: uma frota se concentra
num fingerprint e infla esse termo. As 13 janelas limpas de produção que só Ω admite
têm uma mediana de 33% de Ω fora do termo de endpoint, contra 12% nas outras.

## 7. O escopo (Seção III-C)

### 7.1 Por que o fingerprint mais comum falha

A escolha natural é filtrar o fingerprint modal do alarme, o mais comum. Ela seleciona o
que é comum, e num serviço sob ataque o que é comum é a população legítima.

Uma botnet de A atacantes espalhada uniformemente por M pilhas põe cerca de 0,9 · A/M
atacantes em cada pilha (os outros 10% ficam em fingerprints avulsos). O fingerprint legítimo mais comum tem uma fração p₁ das n_b origens legítimas.

> **A moda é uma pilha de ataque só enquanto 0,9 · A/M > p₁ · n_b.**

Com o p₁ = 38,4% medido (uma fração de requisições, usada como aproximação da fração de origens) e uma campanha do tamanho do tráfego legítimo (A = n_b):

> 0,9/M > 0,384  ⟹  M < 2,34

A partir de três pilhas a moda é um fingerprint legítimo, e o filtro bloqueia usuários e
nenhum atacante. Exemplo: A = n_b = 1.000 e M = 5 dão 180 atacantes por pilha contra
384 usuários no fingerprint legítimo mais comum.

### 7.2 O perfil

O perfil é a contagem de origens por fingerprint no tráfego normal do endpoint, mantida
pelo operador fora dos episódios de ataque. Seja N o total de pares origem–fingerprint do
perfil. A prevalência de um fingerprint f é

> **b(f) = (contagem de f no perfil)/N + 1/N**

O 1/N evita prevalência zero: um fingerprint nunca visto recebe 1/N, e uma única
observação não vira enriquecimento infinito.

Três propriedades do perfil importam:

- ele é o que um defensor observa em operação normal, então **nenhum rótulo de ataque
  entra**;
- em produção ele exclui os clientes que o WAF do operador bloqueou, porque o escopo
  roda atrás do WAF;
- ele precisa vir de fora do episódio de ataque, porque a campanha ocupa a janela
  inteira e, se o perfil fosse a própria janela, todo candidato teria enriquecimento 1.

### 7.3 O teste binomial de enriquecimento

Seja c(f) o número de origens do alarme que apresentam f e n = Σ_f c(f). Se as n origens
sorteassem fingerprints como o tráfego normal, o número delas com f seguiria uma binomial:

> X ~ Bin(n, b(f)),  P[X ≥ c] = Σ_{k=c}^{n} C(n, k) · b^k · (1 − b)^{n−k}

O teste admite todo fingerprint f que passa em duas condições:

> **Efeito:** c(f)/n ≥ ρ · b(f), com ρ = 3
>
> **Significância:** P[X ≥ c(f)] < λ_e / |F|

- O **efeito** exige que f seja pelo menos três vezes mais comum no alarme que no perfil.
- A **significância** exige que uma contagem tão alta seja improvável se o alarme
  sorteasse fingerprints como o tráfego normal.
- **|F|** é o número de fingerprints do perfil e do alarme juntos: a correção de Bonferroni
  sobre todos os fingerprints que poderiam ser testadas. Contar só as presentes no alarme
  subestimaria a família, porque quais aparecem também é aleatório.
- **λ_e** é o nível do endpoint e, calibrado (seção 8), nunca passa de 0,01.

O resultado é um **conjunto** de fingerprints, e é isso que cobre uma botnet fragmentada
em várias pilhas.

**Exemplo.** Alarme com n = 100 origens; um fingerprint com b = 0,001 no perfil;
c = 5 origens com ele; |F| = 500; λ = 0,01.

1. Efeito: c/n = 0,05 ≥ 3 × 0,001 = 0,003. Passa.
2. Significância: P[Bin(100; 0,001) ≥ 5] = 6,96 × 10⁻⁸. Vezes |F| = 500, dá
   3,48 × 10⁻⁵ < 0,01. Passa: **f entra no escopo.**

**A menor contagem apontada** (c_min) no mesmo exemplo depende do nível:

| λ | c_min |
|---|---|
| 10⁻² | 4 |
| 10⁻⁶ | 6 |
| 10⁻²¹ | 14 |
| 10⁻⁶⁰ | 30 |

Quanto menor o nível, mais origens uma pilha precisa ter para ser apontada. É daí que
sai o piso de calibração (seção 9).

**O papel de ρ.** ρ é um piso de tamanho de efeito e quase não importa: com ρ = 2 ou
ρ = 5, nenhuma taxa agregada de disparo em produção se move mais de 0,3 ponto, nenhuma
fração bloqueada mais de 4,5 e nenhuma mediana de dano colateral mais de 7,2. Quem
decide é o nível.

### 7.4 O z-score

Um escopo relativo ao perfil mais simples:

> **z(f) = (c(f) − n · b(f)) / √(n · b(f) · (1 − b(f)))**

No exemplo acima, z = (5 − 0,1)/√(0,1 × 0,999) = 15,5.

- **Sem calibração**, o limiar é z > 3, pela aproximação normal e sem correção para
  múltiplos testes. A aproximação exagera contagens pequenas: com n · b = 0,1, uma
  contagem de 2 já dá z = 6,0. Em produção, atrás do gatilho de Ω, o z-score sem
  calibração dispara em 2,6% das janelas limpas e em 64,5% dos picos legítimos de 100
  usuários.
- **Calibrado**, o limiar é o percentil 99 do maior z de cada janela de calibração,
  nunca abaixo de 3, o mesmo orçamento do teste.

### 7.5 O filtro de fingerprints inéditos e a união

O **filtro de fingerprints inéditos** (*unseen*) aponta todo fingerprint ausente do perfil
que aparece em pelo menos k_min = 5 origens. Ele não precisa de estatística do perfil.

A **união** junta o teste e o filtro: escopo = teste ∪ inéditos. O motivo é que as
frotas que empurram o nível para baixo apresentam fingerprints do perfil, e nenhuma frota
apresenta um fingerprint ausente dele. A união recupera pilhas novas pequenas demais para
o nível estrito, quase sem custo em falsos alarmes. Em produção, o filtro sozinho detém
29,4% de 100 atacantes em pilhas novas e nenhum em pilhas compartilhadas; a união detém
38,4%. No tráfego gerado, a FPR média do filtro é 0,03%.

### 7.6 O que o escopo recusa

Um adversário escondido num fingerprint legítimo popular não é enriquecido, e o escopo é
recusado. É o relato correto quando não existe discriminador: em vez de um filtro que só
atinge usuários, o operador recebe "nenhum escopo" e recorre ao limite de taxa ou ao
desafio a todos.

## 8. A calibração

### 8.1 Por que calibrar

A binomial trata cada origem como um sorteio independente do perfil. O tráfego gerado
satisfaz isso. O de produção não, porque as frotas se ativam juntas. No nível nominal de
0,01, o escopo produz filtro em 26,9% das janelas limpas de produção contando origens e
em 60,1% contando conexões (um cliente abre muitas conexões, que não são sorteios
independentes). Por isso tudo conta origens, e o nível é calibrado.

### 8.2 O nível λ_e como quantil empírico

Para cada janela de calibração sem ataque (com n ≥ k_min), calcula-se

> m = o menor p-valor ajustado, P[X ≥ c(f)] · |F|, entre os fingerprints da janela que passam no efeito
> (as frotas conhecidas, se isentas, ficam de fora)

e então

> **λ_e = min(0,01; percentil 1 dos valores m)**

O escopo produziria filtro em no máximo 1% das janelas de calibração: cerca de 2,9 das
288 de um dia. Em palavras do artigo: o maior valor até 0,01 com que o escopo produz
filtro em no máximo 1% das janelas de calibração do endpoint.

**Por que "quantil empírico" e não "nível de significância".** A níveis como 10⁻⁶⁰, a
cauda binomial deixou de ser a probabilidade dos dados sob o modelo, porque o modelo
está errado para as frotas. Ela é um **escore**, e o quantil fixa o seu limiar.

Níveis calibrados (medianas dos cinco dias de teste, em amostra): com as frotas
conhecidas isentas, 10⁻²¹ no E1, 10⁻⁷³ no E2, 10⁻¹¹ no E3 e 10⁻⁴ no E4 (Tabela V). Sem
isenção, o E1 fica em 10⁻⁶⁰.

### 8.3 O limiar do z-score calibrado

Para cada janela de calibração, o maior z entre os seus fingerprints; o limiar é o
percentil 99 desses máximos, nunca abaixo de 3. É o mesmo orçamento de 1%.

### 8.4 O limiar do gatilho

O gatilho de origens usa o percentil 99 de n nas janelas de calibração; τ_cluster, o
percentil 99 de Ω. Também são orçamentos de 1%.

### 8.5 Dentro e fora da amostra: divisão móvel e calibração cruzada

**Divisão móvel** (*rolling*). Cada um dos cinco dias de teste usa o perfil, os
limiares, o nível e as frotas conhecidas de todos os dias anteriores a ele. As janelas
de calibração são julgadas contra um perfil que as inclui: o nível pode estar ajustado
aos próprios dias.

**Calibração cruzada** (*cross-fit*, deixando um dia de fora). Ao ajustar λ_e, o limiar
do z e as frotas conhecidas, cada dia de calibração é julgado contra um perfil (e um φ,
na beta-binomial) construído com os **outros** dias de calibração, assim como o dia de
teste é julgado contra dias de que não faz parte. O perfil do dia de teste, τ e o
gatilho não mudam. A pergunta que ela responde: o nível foi favorecido pelo ajuste em
amostra?

### 8.6 P-valores em logaritmo

Na calibração cruzada, uma frota ausente do perfil dos outros dias recebe p-valores
menores que o menor número de ponto flutuante positivo (cerca de 5 × 10⁻³²⁴). A cauda
"arredonda" para 0, e um nível calculado de p-valores 0 é 0, que não aponta nada. Por isso
a cauda é calculada em logaritmo:

> log P[X ≥ c] = log( Σ_{k=c}^{n} exp(log pmf(k)) )

pela soma *log-sum-exp* dos logaritmos da função de probabilidade, onde a cauda
"arredonda" (função `log_tail`). Os níveis são guardados como logaritmos
(`scope_log10_level`).

### 8.7 O que o 1% garante, e o que não garante

Nas janelas de calibração, o orçamento vale por construção. Nos dias seguintes, não:

| Componente | Dias de teste, em amostra | Calibração cruzada |
|---|---|---|
| Escopo da configuração binomial, sozinho | 2,2% (console 4,4%) | 1,9% |
| Escopo da beta-binomial, sozinho | 4,4% (console 10,8%) | 1,1% (console 1,5%; dia novo 1,2%) |
| z-score calibrado, sozinho | 6,1% (console 11,5%) | 2,5% (console 5,8%) |
| Gatilho de origens, sozinho | 3,0% | não muda |

Todo componente calibrado passa da meta de 1% nos dias seguintes, e só a beta-binomial
cruzada chega perto. As configurações completas ficam em 0,1–0,4% das janelas limpas
porque exigem as duas coisas ao mesmo tempo, e gatilho e escopo raramente erram juntos.
O 1% é uma meta de calibração, não uma garantia fora da amostra.

## 9. O piso de calibração (Seção III-D)

### 9.1 A fórmula

Um nível calibrado tem um preço, e ele pode ser calculado antes de qualquer ataque.
Entre n origens, o teste aponta uma pilha de c origens só se c/n ≥ ρ · b e
P[X ≥ c] · |F| < λ_e. Seja c_min(n) a menor contagem que passa. Uma botnet de A
atacantes em M pilhas põe cerca de 0,9 · A/M origens em cada pilha, numa janela de
n₀ + A origens (n₀ é a mediana das janelas do endpoint).

> **Piso = o menor A com 0,9 · A/M ≥ c_min(n₀ + A)**

O piso é dado em atacantes por janela ou como fração da janela típica, A/n₀. A fração
pode passar de 1: um piso de "4 janelas" pede uma botnet quatro vezes maior que todo o
tráfego de uma janela.

### 9.2 Exemplo hipotético

Um endpoint com n₀ = 2.000 origens por janela, perfil de N = 200.000 pares (uma pilha
nova tem b = 1/200.000), |F| = 300 e M = 25:

| Nível λ_e | c_min por pilha | Menor botnet A | Piso (fração da janela) |
|---|---|---|---|
| 10⁻² | 3 | 84 | 4% |
| 10⁻²¹ | 10 | 278 | 14% |
| 10⁻⁶⁰ | 22 | 612 | 31% |

A conta da primeira linha: 3 origens por pilha pedem 0,9 · A/25 ≥ 3, isto é,
A ≥ ⌈3 × 25/0,9⌉ = ⌈83,3⌉ = 84. As frotas empurram o nível para baixo, e o nível
empurra o piso para cima.

### 9.3 Pilhas novas sob a união

O filtro de inéditos aponta uma pilha ausente do perfil assim que ela tem k_min = 5
origens, qualquer que seja o nível:

> **Piso de uma pilha nova = ⌈k_min · M/0,9⌉** = ⌈5 × 25/0,9⌉ = ⌈138,9⌉ = **139** atacantes (M = 25)

Com 5 pilhas, 28; com 100, 556. O teste pode apontar antes do filtro: no E4, onde o nível
é 10⁻⁴ e três origens bastam, o piso é ⌈3 × 25/0,9⌉ = 84.

### 9.4 Pilhas compartilhadas: o nível decide

Numa pilha que clientes reais também usam, o filtro de inéditos não aponta nada e o nível
decide. Na conta do piso, b é a prevalência mediana dos fingerprints do perfil além dos dez mais comuns, mais 1/N (e, na beta-binomial, a correlação mediana deles). É aí que o piso
morde: na configuração binomial, 254 atacantes no E1 (8% da janela) e de 4 a 19 janelas
inteiras nos endpoints pequenos (seção 16.3).

### 9.5 O piso não é um degrau

O piso é onde a pilha **média**, 0,9 · A/M, alcança c_min, e o tamanho das pilhas varia.
Um atacante está numa pilha com probabilidade 0,9, e a pilha dele tem ele mesmo e mais
Bin(A − 1; 0,9/M) outros. A fração de uma botnet em pilhas novas que o escopo sozinho
aponta é, então,

> **0,9 · P[Bin(A − 1; 0,9/M) ≥ c_min − 1]**, com c_min o menor entre k_min e a contagem do teste no nível

Exemplo: no E1, com M = 25 e c_min = 5 (o filtro de inéditos), o modelo dá 9%, 43% e 88%
a 50, 100 e 250 atacantes, e as botnets injetadas dão o mesmo. No próprio piso (139), a
fração é cerca de dois terços. O piso é o tamanho em que uma pilha típica é apontada;
abaixo dele o escopo ainda aponta as pilhas que o acaso deixou maiores.

### 9.6 O limite da razão

Por maior que seja a botnet, a fatia esperada de uma pilha fica abaixo de 0,9/M da
janela. A condição de efeito c/n ≥ ρ · b falha, portanto, em média, para todo fingerprint
com

> **b > 0,9/(ρ · M)** = 0,9/(3 × 25) = **1,2%** (M = 25; com M = 5, 6%)

Nos quatro endpoints de produção, os fingerprints acima desse limite são as 4 a 28 mais
comuns de cada um, e carregam de 86% a 94% das origens. Um bot escondido atrás de uma
delas não é apontado por um teste com 25 pilhas, salvo quando o acaso deixa uma pilha bem
maior que a média: é a aritmética da fronteira adversarial.

### 9.7 Como ler o piso

Para o operador, o piso é uma quantidade de planejamento. Acima dele, o escopo pode ser
um filtro de fingerprints. Abaixo, o recurso é o limite de taxa ou o desafio a todos. Se
uma campanha no piso esgota o serviço depende da folga de capacidade dele, que o artigo
não mediu.

## 10. Os dois remédios para o piso

### 10.1 Frotas conhecidas

As **frotas conhecidas** são os fingerprints que o teste aponta no nível nominal (0,01) em
pelo menos 5% das janelas de calibração. Elas saem do escopo e da calibração do nível.
No E1 são cinco ou seis, e isentá-las eleva o nível de 10⁻⁶⁰ para cerca de 10⁻²¹.

É uma **lista de exceções**: um bot que apresente o fingerprint de uma frota não entra no
escopo. A fração de 5% foi escolhida nos três primeiros dias de teste, como a única cujos
falsos alarmes não passaram os da regra básica (5 contra 6; as outras frações deram de 12
a 16).

O critério do protocolo foi a contagem de falsos alarmes. Pela métrica do próprio artigo,
a taxa vezes o dano mediano por janela limpa, a fração de 0,5% era cerca de 25 vezes mais
leve nos três primeiros dias:

> **16/3.454 × 0,60% = 0,0028%** contra **5/3.454 × 48,6% = 0,070%** (fração de 5%)

e detinha mais de 100 atacantes em pilhas novas (44,6% contra 30,9%). Trocar a escolha
agora seria *post hoc*; o artigo mantém os 5% e declara isso na nota da Tabela II.

### 10.2 A referência beta-binomial

**A intuição.** Uma frota põe várias origens na mesma janela de uma vez. A contagem de
um fingerprint varia de janela para janela mais do que a binomial permite: ela é
**sobredispersa**, com variância maior que n · b · (1 − b).

**O modelo.** Em cada janela, a probabilidade de uma origem apresentar f é ela mesma
sorteada de uma distribuição beta com média b, e, dada essa probabilidade, a contagem é
binomial. O resultado é a beta-binomial:

> **E[X] = n · b**
>
> **Var[X] = n · b · (1 − b) · (1 + (n − 1) · φ)**

φ é a correlação dentro da janela: com φ = 0, volta-se à binomial. Os parâmetros da beta
são

> a = b · (1 − φ)/φ,  β = (1 − b) · (1 − φ)/φ,  e então φ = 1/(a + β + 1)

**A estimativa de φ.** Para cada fingerprint f do perfil, pelo método dos momentos, nas
janelas de calibração w com pelo menos k_min origens:

> **φ = Σ_w [(c_w − n_w · b)² − n_w · b · (1 − b)] / Σ_w [n_w · (n_w − 1) · b · (1 − b)]**, limitado a [0; 0,99]

Aqui b é a fração do fingerprint no perfil, sem o 1/N, e n_w é o total de origens TLS da
janela. O numerador é o excesso do desvio quadrático observado sobre a variância
binomial; o denominador é quanto esse excesso valeria por unidade de φ.

*Exemplo hipotético de φ.* Três janelas com n = 100 e um fingerprint com b = 0,01
(esperada: 1 origem por janela), com contagens 0, 0 e 5 (a frota ligou na terceira).
Numerador: (0 − 1)² − 0,99 = 0,01, duas vezes, mais (5 − 1)² − 0,99 = 15,01, total 15,03.
Denominador: 3 × 100 × 99 × 0,01 × 0,99 = 294,03. φ = 0,051.

*Exemplo hipotético das caudas.* n = 100, b = 0,01, φ = 0,05 (a = 0,19, β = 18,81). A
variância vai de 0,99 para 5,89.

| Contagem | P[X ≥ c], binomial | P[X ≥ c], beta-binomial |
|---|---|---|
| 5 | 3,4 × 10⁻³ | 0,069 |
| 8 | 8,2 × 10⁻⁶ | 0,030 |

Sob a beta-binomial, uma frota que põe 8 origens numa janela não é improvável. A calibração não
precisa mais empurrar o nível para 10⁻⁶⁰ para calar as frotas.

**As regras do teste.** Cada contagem é testada contra uma beta-binomial com a mesma
média. Um fingerprint ausente do perfil mantém a binomial, porque não há de onde estimar
φ. O nível λ_e é calibrado como na seção 8.2.

**O efeito em produção.**

- O nível sobe: cerca de 10⁻⁴ (7 × 10⁻⁵) no E1, onde três origens apontam uma pilha, e o
  teto de 0,01 nos demais, onde duas bastam.
- Nenhum fingerprint se qualifica como frota conhecida em amostra, então a lista de
  exceções não é necessária ali (na calibração cruzada, uma aparece no E1 em três dos
  cinco dias).
- O piso de pilhas novas cai para ⌈2 × 25/0,9⌉ = 56 atacantes onde o nível está no teto.
- O piso de pilhas compartilhadas cai para 86 atacantes no E1 (3% da janela) e para
  1,4–4,2 janelas nos demais.

**A correlação da própria pilha entra no piso.** O piso das pilhas compartilhadas usa a
correlação mediana dos fingerprints da cauda. Em três endpoints ela é 0, e o piso é o mesmo
da cauda binomial. No E4 ela é cerca de 3 × 10⁻⁴, e mesmo isso eleva o piso de 56 para
84 atacantes: a correlação soma b · (1 − b) · φ à variância da probabilidade por janela,
o que rivaliza com b² quando b é pequeno.

**O estatuto.** A beta-binomial foi construída depois de o dia novo ter sido lido: seus
resultados são *post hoc*.

## 11. A ontologia como especificação (Seção III-E)

### 11.1 As classes

A classe central é `ApplicationSession`. Ela se liga:

- por `hasIdentity` a uma `Identity` composta (cookie, token JWT, nome de usuário,
  fingerprint TLS);
- por `originatesFrom` ao seu `IPAddress` de origem;
- por `targets` a um `Endpoint`;
- por `mitigatedBy` a uma `Mitigation` (`RateLimitPolicy`, `ChallengeResponse`,
  `WAFRule`), cujo escopo a cadeia de evidência carrega.

### 11.2 As seis sub-relações e os pesos

Seis sub-propriedades de uma `relatedTo` simétrica tipam a evidência que liga duas
sessões. Cada uma tem um `coordinationWeight`, ordenado pelo custo, para o atacante, de
quebrar o sinal:

| Sub-relação | Peso | Exercitada? |
|---|---|---|
| `relatedByTLSFingerprint` (mesma JA4) | 1,0 | sim |
| `relatedByReusedIdentity` (cookie, token ou usuário reutilizado) | 1,0 | especificada |
| `relatedByTemporalPattern` (sequências de chegada parecidas, DTW) | 0,9 | especificada |
| `relatedByPayloadSignature` (resumos de *payload* parecidos, cosseno) | 0,6 | especificada |
| `relatedByEndpointConvergence` (mesmo endpoint) | 0,6 | sim |
| `relatedByNetworkProximity` (mesmo /24 ou ASN) | 0,3 | sim |

A proximidade de rede pesa pouco porque um NAT de operadora (CGNAT) faz de um /24
compartilhado um mau discriminador. A calibração dos pesos sustenta só o topo da ordem
(seção 17.6). No artigo, a lista das seis e os pesos estão no Apêndice A; a Seção III-E
diz só que sub-propriedades de `relatedTo` tipam a evidência e que as três exercitadas
são igualdades.

### 11.3 Das anotações à consulta

As três sub-relações exercitadas são igualdades: JA4 exata, endpoint e prefixo /24
dividem as sessões em classes. A ontologia anota cada uma com a propriedade da sessão
que ela iguala (`kg:classKey`: `kg:tlsJa4`, `kg:targets`, `kg:srcPrefix`) e anota
`relatedTo` com a unidade em que as classes são contadas (`kg:countUnit`:
`kg:originatesFrom`, isto é, origens).

O `compile_counts.py` lê essas anotações e, com um mapeamento de propriedades para
colunas da tabela de logs (o único insumo escrito à mão), gera a consulta SQL que o
armazenamento de logs executa por janela e endpoint. Em forma esquemática, com nomes
genéricos:

```sql
-- s: uma linha por requisição, já com a janela, o endpoint, a origem e as chaves de classe
SELECT janela, endpoint, COUNT(DISTINCT origem) AS origens            -- o gatilho
FROM s GROUP BY janela, endpoint;

SELECT janela, endpoint, ja4, COUNT(DISTINCT origem) AS n_k           -- as classes por JA4
FROM s GROUP BY janela, endpoint, ja4;                                -- (idem por /24)

-- pares por sub-relação: SUM(n_k * (n_k - 1) / 2); Ω = Σ peso × pares
```

- Um novo sinal de igualdade chega à consulta compilada como **quatro triplas** na
  ontologia, sem mudar código.
- **Nenhum raciocinador roda na avaliação**: a ontologia é a especificação, não o motor.
- As sub-relações sem chave de classe (JA4 quase igual, padrão temporal, *payload*,
  identidade) não são equivalências e precisariam de avaliação par a par. A JA4 quase
  igual (uma variante a um símbolo de distância, Apêndice A) está especificada, mas não é
  exercitada: o artigo e a consulta contam só classes de JA4 exata.

### 11.4 A regra como derivação (fora do artigo)

A listagem que escrevia a regra saiu do artigo na rodada 18, por espaço; a regra está na
ontologia e no código, e o Apêndice D descreve a agregação em palavras. Ela tem duas
partes. Uma regra de Horn em SWRL instancia uma
sub-relação:

```
ApplicationSession(?a) ^ ApplicationSession(?b) ^ differentFrom(?a,?b) ^
  tlsJa4(?a,?j) ^ tlsJa4(?b,?j)  ->  relatedByTLSFingerprint(?a,?b)
```

E uma agregação SPARQL calcula Ω a partir das classes: para cada endpoint e classe,
conta as origens distintas n, soma w · n(n − 1)/2 e mantém o endpoint se a soma alcança
τ. É a mesma conta da seção 6.2, escrita sobre o grafo.

### 11.5 A cadeia de evidência e o STIX 2.1

Quando a regra dispara, a cadeia de evidência (a regra, as instâncias, a decomposição de
Ω por sub-relação e o escopo) é exportada como JSON-LD (Listagem 1) e como STIX 2.1: um
*indicator* e um *course-of-action* ligados por *mitigates*.

---

# Parte III. A avaliação

## 12. As fontes de tráfego (Seção IV-A)

### 12.1 Três fontes, três perguntas

| Fonte | Pergunta que responde |
|---|---|
| Gerador calibrado | O mecanismo, em campanhas controladas com verdade conhecida (avaliação principal) |
| Capturas de laboratório | Ataques convencionais e o sistema publicado mais próximo (KLAGE) |
| Produção (Azion) | Falsos alarmes em clientes reais e, com uma botnet injetada, a detecção |

### 12.2 O gerador

O gerador produz campanhas distribuídas de *Slow HTTP DoS* contra um endpoint, com a
verdade de coordenação conhecida. Os parâmetros:

- **K**, o grau de distribuição: 50 (uma botnet pequena cujas origens ficam cada uma
  dentro do seu limite de taxa) e 1.000 (espalhada por centenas de ASNs e prefixos,
  com sinal por sessão desprezível);
- **M**, o número de pilhas: 1, 5, 25 e 100, com 25 canônico. 90% da campanha se espalha
  uniformemente pelas M pilhas (a escolha conservadora para um dado M) e o resto por
  fingerprints avulsos;
- **α**, o expoente da curva de Zipf dos fingerprints legítimos: 1,5 canônico e 2,0;
- **modo furtivo**: os atributos de cada sessão atacante são sorteados das mesmas
  distribuições das legítimas, então a campanha só se revela pela estrutura entre sessões;
- **modo adversarial**: a botnet adota os fingerprints legítimos mais comuns, como faria um
  bot que imita navegadores;
- **modo compartilhado**: as pilhas são sorteadas da cauda do perfil.

As contagens de requisições e as durações legítimas são amostradas das sessões benignas
do CICIDS2017 (todas as 322.658 para as contagens e as 40.351 com duas ou mais
requisições para as durações). As distâncias de Kolmogorov–Smirnov de 0,002 e 0,003
entre sessões geradas e reais só conferem o amostrador. Os atacantes começam nos
primeiros 30 s, então a campanha é uma fração grande do tráfego que ela sobrepõe: uma
mediana de 34–45% das origens de uma janela e 50% do *cluster* do alarme. No gerador cada
origem carrega uma sessão, e o nível fica em 0,01 em todo cenário. O conjunto de
fingerprints legítimos tem 2.000 valores.

### 12.3 A curva de Zipf

A popularidade do k-ésimo fingerprint legítimo mais comum, num vocabulário de V fingerprints:

> **p_k = k^(−α) / Σ_{j=1}^{V} j^(−α)**

Com V = 2.000:

| α | Fingerprint mais comum | Dez mais comuns |
|---|---|---|
| 1,5 | 38,9% | 77,7% |
| 2,0 | 60,8% | 94,2% |

A curva foi calibrada contra 6,33 milhões de requisições TLS de um ponto de presença da
Azion (medidas em 22 de agosto de 2026, só fingerprints e frequências): 495 fingerprints, o mais comum com 38,4% das requisições e os dez mais comuns com 93,8%. A cabeça bate com
α = 1,5 e as dez primeiras com α = 2,0; α = 1,5 é o canônico. Os endpoints de produção
mostram de 76 a 818 fingerprints distintos.

### 12.4 As capturas de laboratório (Apêndice C)

CICIDS2017 (captura de quarta-feira: Slowloris, Slowhttptest, HULK, GoldenEye) e
CIC-IoT2023 (*DDoS Slowloris* e *HTTP Flood*), a base em que o KLAGE reporta F₁ = 84,1%
para *DDoS Slowloris*, passam pelo mesmo pipeline de extração (PCAP → JA4 + fluxos →
sessões).

### 12.5 Produção

**Os endpoints.** Quatro endpoints dos serviços da própria Azion, todos os que, entre os
12 exportados, têm TLS, pelo menos 50 janelas de calibração com k_min origens e janela
mediana de pelo menos k_min origens:

| Endpoint | Serviço | Origens por janela (mediana) |
|---|---|---|
| E1 | *Beacons* de monitoramento de usuário real (RUM) | 2.983 |
| E2 | Console web | 62 |
| E3 | API | 41 |
| E4 | *Single sign-on* (SSO) | 20 |

**Os dados.** As exportações contam origens distintas e conexões por fingerprint e janela de
cinco minutos, e pares no mesmo /24 por janela, sem endereços, portas ou URIs. Os dias de
calibração são supostos sem ataque: um ataque entre eles baixaria o nível e subiria o
gatilho, e o escopo ficaria mais conservador. Elas ficam no disco
de dados externo, fora do repositório; no repositório entram só resumos anonimizados
(E1–E4, taxas e contagens).

**Os dias.** Oito dias (17 a 24 de setembro de 2026). Cada um dos cinco últimos (dias de
teste, 20 a 24) é testado com o perfil, os limiares e o nível dos dias anteriores (seção
8.5). São 5.643 janelas limpas nos dias de teste. Um nono dia, o **dia novo** (25 de
setembro), foi exportado depois das escolhas que fixaram a configuração e analisado com
ela e com as métricas fixadas de antemão: 1.152 janelas (4 × 288). A beta-binomial e a
calibração cruzada vieram depois de o dia ser lido.

**A botnet injetada.** Em cada janela injeta-se uma botnet construída como o gerador
constrói: de 25 a 1.000 atacantes em 1 a 100 pilhas, ou um décimo (0,1×), metade ou a
totalidade (1×) da janela mediana do endpoint em 25 pilhas. Ela põe 90% dos atacantes em 25 pilhas, uniformemente, e o resto em
fingerprints avulsos, vindos de 2.000 /24 disjuntos dos reais. As pilhas são:

- **novas**: ausentes do tráfego;
- **compartilhadas**: sorteadas do perfil depois das suas dez fingerprints mais comuns;
- **adversariais**: as 25 fingerprints mais comuns do endpoint.

**Os picos legítimos.** Um pico acrescenta 100 ou 1.000 usuários, sorteados dos clientes
do próprio dia, a uma janela.

## 13. As configurações avaliadas em produção (Tabela II)

| Configuração | Gatilho | Escopo | Referência | Isenção | Escolhida | Dia novo |
|---|---|---|---|---|---|---|
| Regra básica | Ω ≥ τ | teste | binomial | nenhuma | nos dias de teste | no protocolo |
| **Binomial** | origens | teste ∪ inéditos | binomial | frotas conhecidas | nos dias de teste | no protocolo |
| z-score | origens | z > seu p99 | binomial | nenhuma | nos dias de teste | fora dele (ver nota) |
| Beta-binomial | origens | teste ∪ inéditos | beta-binomial | nenhuma | *post hoc* | *post hoc* (ver nota) |

- **Gatilho**: Ω ≥ τ_cluster, ou origens distintas no seu percentil 99 ou acima.
- Limiares, níveis e frotas conhecidas são ajustados em dias sem ataque, em amostra ou
  por calibração cruzada.
- **Cinco escolhas foram feitas nos dias de teste**: contar origens, calibrar λ_e, o
  gatilho de origens, a união com o filtro de inéditos e a fração de 5% das frotas. Só o
  dia novo as põe à prova. Das quatro frações, só a de 5% não teve mais falsos alarmes
  que a regra base nos três primeiros dias de teste, embora a de 0,5% bloqueasse cerca de
  25 vezes menos clientes legítimos e detivesse mais de uma botnet de 100 atacantes
  (44,6% contra 30,9%, seção 10.1).
- **Beta-binomial no dia novo**: o dia foi lido antes de ela ser construída, então o
  resultado dela ali também é *post hoc*.
- ***Post hoc***: depois de o dia novo ter sido lido. A beta-binomial e a calibração
  cruzada são *post hoc*.
- **Nota do z-score**: ele estava no código antes de o dia novo ser lido, mas fora do
  protocolo.

No tráfego gerado, os escopos são comparados no *cluster* do alarme: o fingerprint modal,
o filtro de inéditos, o z-score (z > 3) e o teste binomial. A linha de base aprendida é um
*Random Forest* treinado com os rótulos da campanha sobre a evidência entre sessões das
três sub-relações (a configuração (d)), forçado ao ponto de operação do teste.

## 14. As métricas

### 14.1 Métricas de classificação

Com VP, FP, VN e FN os verdadeiros e falsos positivos e negativos:

> **Revocação** (*recall*) = VP/(VP + FN): quanto do ataque foi pego.
>
> **FPR** = FP/(FP + VN): quantos inocentes foram atingidos.
>
> **Precisão** = VP/(VP + FP)
>
> **F₁** = 2 · Precisão · Revocação/(Precisão + Revocação)
>
> **AUC ROC** = a probabilidade de uma sessão atacante sorteada receber escore maior que
> uma legítima sorteada (0,5 é o acaso).

Revocação e FPR não dependem do equilíbrio entre as classes: cada uma tem no
denominador uma classe só (atacantes ou legítimos). Por isso vêm sempre juntas. A
**revocação com FPR = 0** é o
número operacional: quanto se pega sem atingir ninguém. O escopo não tem escore, então
não tem AUC; ele entrega um par (revocação, FPR) sem ajuste.

### 14.2 Dano colateral

> **Dano colateral** = a fração do tráfego legítimo dentro do escopo, isto é, a FPR do
> filtro que o operador implantaria.

"Ataque bloqueado" é revocação; "legítimos atingidos" é FPR.

### 14.3 Taxa de falso alarme e o intervalo de Clopper–Pearson

Um **falso alarme** é uma janela limpa em que o gatilho dispara **e** o escopo produz um
filtro. A taxa é x/n sobre as janelas limpas, com o intervalo exato de Clopper–Pearson
de 95%, cujos limites são quantis de distribuições beta:

> **inferior = Beta⁻¹(0,025; x; n − x + 1)**,  **superior = Beta⁻¹(0,975; x + 1; n − x)**

Exemplo: a configuração binomial dispara em 5 de 5.643 janelas limpas: 0,089%, com
intervalo de 0,029% a 0,207%. O z-score calibrado dispara em 20 (0,354%, até 0,547%) e a
beta-binomial em 22 (0,390%, até 0,590%). O orçamento de 1% de 288 janelas é 2,9 alarmes
por endpoint e dia; a binomial dá 5/20 = 0,25 por endpoint e dia, as outras duas cerca de
um.

**As janelas não são independentes.** Os falsos alarmes se concentram: 13 dos 22 da
beta-binomial e 13 dos 20 do z-score caem num só dia do console. O intervalo exato trata
as 5.643 janelas como sorteios independentes, então subestima a incerteza das taxas
concentradas, e o artigo diz isso. Um ***bootstrap*** **por endpoint-dia** (os dias de cada
endpoint reamostrados com reposição) não resolve: com só cinco dias por endpoint, ele não
enxerga a variação entre dias que não sorteou. Para a binomial ele dá 0,02–0,16%, mais
estreito que o exato (0,03–0,21%), e para a beta-binomial cruzada um limite inferior de 0%
com seis alarmes observados. Por isso o artigo reporta só o exato. O remédio certo seria um
modelo de contagem sobredisperso por endpoint-dia, ou mais dias.

**Gatilho e escopo erram juntos?** Se fossem independentes, os falsos alarmes conjuntos
esperados seriam

> **esperado = Σ_e (taxa do gatilho_e × taxa do escopo sozinho_e × janelas limpas_e)**

que dá 3,5, 7,5 e 11,9 para a binomial, a beta-binomial e o z-score, contra 5, 22 e 20
observados. Uma frota pode causar o excesso, porque sobe a contagem de origens e enriquece
o próprio fingerprint na mesma janela. Para saber se o excesso é real, faz-se um teste de
contagem. Sob independência, os alarmes conjuntos são a soma de muitos eventos raros de
janela, uma contagem quase de **Poisson** com aquela média, e P[X ≥ observado] mede a
surpresa:

| Configuração | Em amostra | P | Cruzada | P |
|---|---|---|---|---|
| Binomial | 5 contra 3,5 | 0,27 | 6 contra 3,2 | 0,10 |
| Beta-binomial | 22 contra 7,5 | 1,4 × 10⁻⁵ | 6 contra 1,8 | 0,011 |
| z-score calibrado | 20 contra 11,9 | 0,020 | 13 contra 4,6 | 0,001 |

Exemplo: com média 3,5,

> **P[X ≥ 5] = 1 − e^(−3,5) · (1 + 3,5 + 3,5²/2 + 3,5³/6 + 3,5⁴/24) ≈ 1 − 0,73 = 0,27**

Cinco alarmes conjuntos contra 3,5 esperados acontecem por acaso uma vez em quatro. A
dependência é clara na beta-binomial e no z-score. Na binomial o excesso cabe no acaso, e
o artigo só afirma a dependência onde ela é significativa.

### 14.4 O custo de um falso alarme e o dano esperado

O **dano colateral de um alarme** é a fração dos clientes da janela que o filtro
bloquearia, reportada como mediana e média sobre os alarmes. Combinado com a taxa:

> **dano esperado por janela limpa = taxa de falso alarme × dano colateral médio por alarme**

| Configuração | Taxa de falso alarme | Dano médio por alarme | Dano esperado |
|---|---|---|---|
| Binomial | 0,089% | 30,6% | 0,027% |
| z-score calibrado | 0,354% | 11,44% | 0,041% |
| Beta-binomial | 0,390% | 7,7% | 0,030% |

Uma configuração que erra pouco mas largo e outra que erra muito mas estreito custam aos
usuários mais ou menos o mesmo.

### 14.5 Picos legítimos

A taxa em picos legítimos é a fração das janelas em que a configuração dispara depois de
se acrescentarem N usuários legítimos (N = 100 ou 1.000) a uma janela limpa. Ela mede com
que frequência um surto de usuários reais seria desafiado.

### 14.6 A fração bloqueada e sua decomposição

A fração bloqueada da botnet é a média, sobre **todas** as janelas de ataque (inclusive
aquelas em que o gatilho não dispara), de

> **bloqueado = 1{o gatilho dispara} × 1{o escopo produz filtro} × cobertura**

em que a cobertura é a fração dos atacantes da janela que o filtro casa. Os três fatores
são reportados separados, e é isso que mostra **qual** parte falha. Com 100 atacantes em
pilhas novas, a configuração binomial produz filtro em toda janela, o gatilho dispara em
68,4% delas, e 38,4% dos atacantes são detidos. Os 10% em fingerprints avulsos limitam
qualquer escopo a cerca de 90%.

### 14.7 O dia novo como teste da taxa

Com a configuração fixada de antemão, os falsos alarmes do dia novo testam a taxa dos
dias de teste, r = 5/5.643. Sob essa taxa, a contagem X nas 1.152 janelas é
Bin(1.152; r), com média 1,02:

| Alarmes x | P[X ≥ x] |
|---|---|
| 2 (observado) | 0,27 |
| 3 | 0,084 |
| 4 | 0,020 |

Até 3 alarmes passariam no nível de 5%, e 4 rejeitariam a taxa. O poder contra uma taxa
três vezes maior, P[Bin(1.152; 3r) ≥ 4], é só 0,37: um único dia refuta um erro
grosseiro, não confirma a taxa.

**O teste condicionado ao gatilho.** O gatilho abriu em só 3 janelas limpas do dia novo,
contra 168 nos dias de teste (3,0%), e o escopo errou em 2 delas. Dada a abertura do
gatilho, a taxa dos dias de teste é 5/168, e

> **P[Bin(3; 5/168) ≥ 2] = 0,003**

A contagem incondicional é compatível porque o gatilho ficou quieto, não porque o escopo
errou menos.

### 14.8 Métricas contra os veredictos do WAF

Os clientes que o WAF bloqueou são tomados como rótulos. Por configuração:

- **produz filtro**: a fração das janelas com filtro;
- **revocação**: a fração dos clientes bloqueados que os filtros casam;
- **precisão**: a fração dos clientes casados que foram bloqueados;
- ***lift*** = precisão / fração bloqueada da janela (uma escolha aleatória de clientes
  tem *lift* 1);
- **dano colateral**: a fração dos clientes não bloqueados casados.

**O piso de precisão embutido.** Se o perfil exclui os clientes bloqueados e o WAF
bloqueia uma fração S da janela, um fingerprint cujos clientes não bloqueados mantêm a
prevalência b do perfil só é enriquecido no tráfego completo quando uma fração s dos
seus próprios clientes foi bloqueada, com

> **s ≥ 1 − (1 − S)/ρ**

De onde vem: se c_limpo = b · (1 − S) · n e s = c_bloq/c, então c/n = b(1 − S)/(1 − s),
e o efeito c/n ≥ ρb pede (1 − S)/(1 − s) ≥ ρ. Com S = 63% (API), s ≥ 0,88; com S = 39%
(SSO), s ≥ 0,80. A precisão alta sai da construção.

**Surtos e acaso.** Um **surto** é uma sequência de janelas consecutivas com pelo menos
k_min clientes bloqueados e pelo menos o percentil 99 da contagem de bloqueados nos dias
anteriores. Ele é **detectado** quando um filtro casa um cliente bloqueado numa das suas
janelas. A comparação é com o acaso:

> **esperado por acaso = Σ_surtos [1 − (1 − p₀)^L]**

com L a duração do surto em janelas e p₀ a taxa com que o escopo casa um cliente
bloqueado fora dos surtos. Exemplo: 28 surtos de duração média 1,75 e p₀ = 0,0072 dão
cerca de 0,35 detecções esperadas.

### 14.9 Testes estatísticos do tráfego gerado

- **Wilcoxon pareado**: compara duas configurações nas mesmas sementes, pelos postos das
  diferenças.
- **Bonferroni**: multiplica cada p-valor pelo número de testes.

---

# Parte IV. Os resultados

## 15. Tráfego gerado (Seção V-A; Apêndices C e E)

### 15.1 A Tabela III, linha a linha

A Tabela III trata o escopo de enriquecimento do *cluster* de maior Ω como detector
(K = 1.000, n = 15 sementes). As sessões que casam o escopo **são** o conjunto
sinalizado, sem treino nem rótulo.

| Cenário | Teste: revocação | FPR | F₁ | Moda | z-score | Inéditas | (d), FPR = 0 | (d) + perfil |
|---|---|---|---|---|---|---|---|---|
| M = 1 (monolítica) | 89,8% | 0,00% | 0,946 | 89,8% | 89,8% | 89,8% | 91,7% | 85,9% |
| M = 5 | 90,0% | 0,00% | 0,948 | 0,0% | 90,0% | 90,0% | 88,6% | 91,7% |
| M = 25 | 90,3% | 0,00% | 0,949 | 0,0% | 90,3% | 90,3% | 36,4% | 87,4% |
| M = 100 | 38,6% | 0,00% | 0,556 | 0,0% | 80,4% | 88,1% | 17,6% | 86,9% |
| M = 25, compartilhada | 85,4% | 2,23% | 0,910 | 0,0% | 89,9% | 0,0% | – | – |
| M = 25, adversarial | 30,4% | 3,78% | 0,452 | 3,6% | 57,3% | 0,0% | 7,8% | 6,6% |

Notas: a coluna Moda é o fingerprint mais comum do alarme, com FPR de 0% a M = 1 e de 39,0%
nas outras linhas (61,1% com α = 2,0); a FPR do z-score é 0% exceto 3,37% (compartilhada)
e 11,3% (adversarial); a FPR
média do filtro de inéditos é 0,03% (no máximo 0,5% numa semente). Com as pilhas
compartilhadas sorteadas do vocabulário do gerador (na maior parte ausente do perfil
amostrado), o filtro de inéditos bloqueia 84,4% e o teste 89,8%.

**Como ler.**

- **A escolha natural falha.** Contra uma botnet monolítica, a moda e o teste concordam
  (89,8%, sem dano colateral). A partir de cinco pilhas, como a condição da seção 7.1
  prevê, a moda é um fingerprint legítimo: a regra por frequência bloqueia 0,0% do ataque
  e 39,0% do tráfego legítimo, e 61,1% com uma população mais concentrada (α = 2,0).
- **Os escopos relativos ao perfil funcionam.** O teste bloqueia 90,0% a cinco pilhas e
  90,3% a 25, sem dano colateral observado, e o z-score também. Os 10% restantes são a
  cauda de fingerprints avulsos: o escopo troca completude por precisão.
- **A 100 pilhas**, uma pilha de cerca de dez sessões entre duas mil não se distingue da
  cauda de um perfil de 1.000 sessões, e o teste cai para 38,6%, abaixo do z-score (80,4%) e do
  filtro de inéditos (88,1%). Um perfil acumulado em 30 períodos sem ataque devolve o teste a 89,6%. O tamanho do
  perfil governa a menor pilha que o teste aponta.
- **O filtro de inéditos** empata até 25 pilhas e vai melhor a 100 (88,1%), porque as
  pilhas geradas nunca aparecem no vocabulário legítimo, mas não bloqueia nenhuma das
  pilhas sorteadas da cauda do perfil. Ali o teste bloqueia 85,4% com 2,23% de dano e o
  z-score 89,9% com 3,37%.

### 15.2 A coluna da moda

A coluna Moda resume o que a moda faz: bloqueia 89,8% do ataque quando a botnet é
monolítica e nenhum atacante a partir de cinco pilhas, sempre atingindo 39,0% do tráfego
legítimo (a fração do fingerprint legítimo mais comum). É a leitura da seção 7.1 em números.

### 15.3 Os modelos aprendidos

O modelo aprendido precisa de rótulos que nenhum operador tem durante um ataque.

- Contra uma botnet monolítica ou pouco fragmentada, ele compete com FPR = 0 (91,7% e
  88,6% contra 89,8% e 90,0%).
- A 25 pilhas o teste passa à frente, 90,3% contra 36,4% com FPR = 0. Com 1% de FPR
  permitido, de que o teste não precisa, o modelo chega a 66,8% (AUC 0,979), e a 94,6%
  com o perfil.
- Com o perfil dado como dois atributos por sessão (a prevalência do fingerprint e o seu
  enriquecimento no *cluster*), ele recupera 87,4% a 25 pilhas e 86,9% a 100, treinado
  com os rótulos da mesma campanha que avalia.
- Na botnet adversarial, onde o teste opera com 3,78% de dano, o modelo aprendido é
  mostrado com FPR = 0; com 1% de FPR ele chega a 23,4%, contra 30,4% do teste.
- Treinado num número de pilhas, (d) não se transfere para outro: sua AUC cai de
  0,95–0,995 no número de pilhas em que foi treinado para 0,48–0,75 (seção 15.6).

### 15.4 As duas condições que limitam o resultado

- **A fronteira do modelo de ameaça.** Quando a botnet adota fingerprints legítimos comuns,
  pouco é enriquecido: o teste bloqueia 30,4% do ataque com 3,78% de dano, o z-score 57,3%
  com 11,3%, e a regra por frequência 3,6% com 39,0%. Com um ρ mais estrito, o escopo se
  recusa a apontar.
- **O perfil.** Uma deriva moderada é tolerável: um perfil com α = 2,0 contra um episódio
  com α = 1,5 dá 90,3% de cobertura sem dano. Um perfil plano ou ausente faz todo fingerprint parecer raro, e o dano salta para 77,6%.

### 15.5 A regra por janela (Apêndice E)

Aqui a regra roda como implantada: por janela de 300 s e endpoint, sem que nenhum limiar
veja ataque ou rótulo. τ_cluster é o percentil 99 de Ω em 30 execuções sem ataque, que
também formam o perfil. Os falsos alarmes são contados em outras 30, a detecção nas
campanhas canônicas (α = 1,5, M = 25) nas janelas com pelo menos 5 atacantes, e um pico
legítimo reagrupa 25, 50 ou 100 sessões legítimas de uma terceira execução numa janela.

Cobertura: mediana da fração dos atacantes da janela que o escopo bloqueia. Dano: a maior
fração das sessões legítimas bloqueada.

| Janelas | n_W | Ω ≥ τ | Ω e teste: dispara | Cobertura | Dano |
|---|---|---|---|---|---|
| Ataque, K = 1.000 | 90 | 77,8% | 77,8% | 79,8% | 0,0% |
| Ataque, K = 50 | 35 | 85,7% | 85,7% | 75,3% | 0,0% |
| Limpas | 360 | 0,6% | 0,0% | – | – |
| Pico, 25 | 30 | 80,0% | 0,0% | – | – |
| Pico, 50 | 30 | 100% | 0,0% | – | – |
| Pico, 100 | 30 | 100% | 0,0% | – | – |

Ω sozinho dispara nos picos legítimos. Exigir que o teste aponte um fingerprint remove
esses falsos alarmes, porque esses picos sorteiam usuários do mesmo *mix* que o perfil
descreve (um surto de um só tipo de cliente seria enriquecido, como as frotas de produção
mostram). Com o teste, a regra não dispara em nenhuma janela limpa (limite superior
unilateral de 95%: 0,8%) nem em nenhum pico, e bloqueia uma mediana de 75–80% dos
atacantes em toda janela de ataque que Ω sinaliza, sem atingir nenhuma sessão legítima.
O gatilho de origens pega 82,2% e 85,7% das janelas de ataque e, com o teste, não
sinaliza nenhuma janela limpa nem pico. Nos picos reais de produção isso não vale: a
configuração ainda dispara em 22,2% dos picos de 1.000 usuários (seção 16.2).

### 15.6 Detecção por sessão e modelos aprendidos (Apêndice C)

**As configurações.** Cada uma roda em n = 30 sementes, com cada campanha dividida 70/30
em sessões de treino e teste.

- (a) só atributos de fluxo por sessão, num *Random Forest* deliberadamente forte,
  repetido com *gradient boosting*, perceptron e regressão logística;
- (b) acrescenta atributos ontológicos por sessão;
- (c) só a proximidade de rede;
- (d) a evidência entre sessões das três sub-relações: a fração do *cluster* que
  compartilha uma JA4 ou um /24, mais o tamanho dele.

Também foram reimplementados três trabalhos: perfil por PCA, PCA com *k-means* sobre uma
matriz comportamental e RF/SVM supervisionado sobre atributos de sessão.

**Os números.** A K = 50 e K = 1.000, (a) chega a AUC por sessão de 0,498 e 0,503, (b) a
0,500 e 0,502 e os três trabalhos a 0,495–0,518. (a) fica em 0,488–0,503 com todas as
famílias de classificador: é o acaso que o modo furtivo impõe. (d) chega a 0,927 e 0,982,
e (c) a 0,499 e 0,659. Nos testes de Wilcoxon pareados com Bonferroni,
p_Bonf = 7,5 × 10⁻⁹ para (d)−(c) e (d)−(a) a K = 1.000.

**A separabilidade não se transfere.** Fragmentar a botnet em M pilhas torna a evidência
entre sessões não monotônica no rótulo: a K = 1.000, um atacante compartilha o fingerprint
com algumas dezenas de pares, e um cliente legítimo na cabeça da curva com centenas.
Treinado com cinco pilhas e
testado com 25 ou 100, (d) cai para 0,61 e 0,63; treinado com 25, cai para 0,48 com cinco e
0,75 com 100, contra 0,95–0,995 no mesmo M com outras sementes. Os testes entre valores de
M usam sementes disjuntas, porque o gerador sorteia toda sessão legítima antes de qualquer
coisa que dependa de M: uma divisão na mesma semente daria a (a) 0,88–0,94 por memorização.

**Capturas de laboratório e KLAGE.** No *DDoS Slowloris* do CIC-IoT2023, cujos
*clusters* de ataque têm sete origens num de 143 prefixos /24, uma linha de base por sessão
enxuta (três atributos) cai para F₁ = 0,179 (AUC 0,551). Uma forte (oito atributos de
fluxo) chega a 0,900 (AUC 0,987) e a representação entre sessões a 0,911 (AUC 0,982),
porque o Slowloris real, ao contrário das campanhas furtivas, deixa uma assinatura de
fluxo por sessão. A comparação com o KLAGE **não é controlada**: a linha de base forte também
supera o 0,841 publicado, e o código liberado parte de um grafo de construção não
publicada e não traz pesos.

**Validação das explicações.** As cadeias de evidência dos sete *clusters* de laboratório
passam nas verificações de completude (toda sessão correlacionada e toda sub-relação
ativada enumerada) e de acionabilidade (um escopo coerente com o discriminador do
*cluster*), 7/7, quando contadas em sessões. Contadas em origens, as cinco do CICIDS2017
têm de uma a três origens, abaixo de k_min, e as duas do CIC-IoT2023 têm sete. Nenhum
estudo com usuários as testou.

## 16. Tráfego de produção (Seções V-B a V-D; Apêndice E)

A Seção V dá três achados de produção: V-B, falsos alarmes e o piso; V-C, o que é detido,
onde o gatilho decide (Fig. 2, Tabela VI, Fig. 3); V-D, o que a evidência sustenta (o dia
novo, as análises *post hoc*, a fronteira e os veredictos do WAF). O texto da Seção V dá
os números centrais; os demais estão nas Tabelas IV a VII e no parágrafo *Details of
Section V* do Apêndice E. Este guia reúne os dois.

### 16.1 O ponto de partida

No nível nominal, o escopo produz filtro em 60,1% das janelas limpas contando conexões e
em 26,9% contando origens. Calibrar λ_e nos dias anteriores leva a regra básica a 0,2%, e
o gatilho de origens, que dispara nas mesmas janelas que Ω em 86–99,6% dos casos, reduz
seus falsos alarmes à metade sem perda de detecção (6 contra 14 janelas).

### 16.2 Falsos alarmes (Tabela IV)

A Tabela IV reúne as configurações em todos os endpoints, em %:

| | Escopo | FA | Sem gatilho | Dano | Pico 1k | Novas 0,1× | Novas 1× | Compart. 0,1× | Compart. 1× |
|---|---|---|---|---|---|---|---|---|---|
| **Dias de teste, em amostra** | binomial | 0,1 | 2,2 | 32,9 | 22,2 | 3,0 | 19,9 | 1,9 | 17,6 |
| | beta-binomial* | 0,4 | 4,4 | 10,5 | 28,4 | 3,3 | 31,4 | 2,7 | 24,7 |
| | z-score | 0,4 | 6,1 | 10,8 | 13,1 | 3,1 | 28,8 | 2,3 | 18,9 |
| **Dias de teste, cruzada** | binomial | 0,1 | 1,9 | 31,4 | 20,7 | 3,0 | 19,8 | 1,5 | 17,4 |
| | beta-binomial* | 0,1 | 1,1 | 2,0 | 10,9 | 3,0 | 23,3 | 2,1 | 17,5 |
| | z-score | 0,2 | 2,5 | 11,0 | 5,5 | 3,0 | 20,1 | 2,0 | 16,0 |
| **Dia novo, calibrado nos oito dias anteriores** | regra | 0,2 | 8,7 | 41,2 | 24,4 | 0,0 | 17,3 | 0,0 | 16,6 |
| | binomial | 0,2 | 0,5 | 41,2 | 24,5 | 0,0 | 20,4 | 0,0 | 17,0 |
| | beta-binomial* | 0,0 | 1,6 | – | 26,6 | 0,0 | 32,5 | 0,0 | 26,2 |
| | z-score | 0,2 | 2,8 | 41,2 | 0,3 | 0,0 | 31,4 | 0,0 | 19,7 |

- **FA**: fração das janelas sem ataque (5.643 nos dias de teste, 1.152 no dia novo) em
  que a configuração produz filtro. **Sem gatilho** (*No gate* no artigo): o mesmo para o
  escopo sem o gatilho.
  **Dano**: mediana da fração dos clientes que o filtro dos falsos alarmes bloqueia.
  **Pico 1k**: a taxa de disparo com um pico legítimo de 1.000 usuários.
- **Bloqueado** (as quatro últimas colunas): fração média de uma botnet de 25 pilhas do
  tamanho da janela mediana do endpoint (1×) ou de um décimo dela (0,1×), em pilhas novas
  ou compartilhadas; os fingerprints avulsos limitam o valor a cerca de 90%.
- \* construída depois de o dia novo ter sido lido (*post hoc*).

**Como ler (Seção V-B).**

- **Os componentes passam da meta**, somando os endpoints. O escopo da binomial sozinho
  produz filtro em 2,2% das janelas limpas (4,4% no console), o z-score calibrado em 6,1%,
  e o gatilho de origens sozinho dispara em 3,0% (5,4% no E1; seção 8.7).
- **Erram juntos?** Na binomial, 5 alarmes conjuntos contra 3,5 esperados sob
  independência cabem no acaso (P = 0,27); na beta-binomial e no z-score o excesso é claro
  (seção 14.3). A conjunção continua rara.
- **A binomial** dispara em 0,1% das janelas limpas (5 de 5.643; intervalo exato de 0,03%
  a 0,21%), 4 deles no console. **O z-score calibrado** dispara em 0,4% (20); 13
  desses alarmes caem num só dia do console, e por isso o intervalo exato, que supõe
  janelas independentes, subestima a incerteza dele.
- **O custo.** Os filtros da binomial bloqueiam uma mediana de 32,9% dos clientes da
  janela (média de 30,6%, que dá o dano esperado) e os do z-score uma média de 11,4%, então
  os dois bloqueiam cerca de 0,03–0,04% dos clientes legítimos por janela limpa.
- **Os picos legítimos.** Um pico de 1.000 usuários, sorteados dos clientes do dia (nos
  endpoints pequenos, de 16 a 50 janelas típicas), dispara o z-score calibrado em 13,1%
  das janelas e a binomial em 22,2%. Os filtros desses disparos são mais leves:
  bloqueiam uma mediana de 4,3% dos clientes da janela, contando o pico (percentil 90 de
  20,6%; 7,1%, 18,6% e 2,7% do E2 ao E4), contra 32,9% nos falsos alarmes de janelas
  limpas.

### 16.3 O que o escopo aponta: o piso (Tabela V)

| Endpoint | Origens | λ_e binomial | λ_e beta* | Binomial: novas | Binomial: compart. | Beta*: novas | Beta*: compart. |
|---|---|---|---|---|---|---|---|
| E1, RUM | 2.983 | 10⁻²¹ | 10⁻⁴ | 139/139 | 254/286 | 85/139 | 86/167 |
| E2, console | 62 | 10⁻⁷³ | 10⁻² | 139/139 | 1.090/1.041 | 56/114 | 84/168 |
| E3, API | 41 | 10⁻¹¹ | 10⁻² | 139/139 | 168/227 | 56/114 | 56/140 |
| E4, SSO | 20 | 10⁻⁴ | 10⁻² | 84/84 | 84/114 | 56/56 | 84/84 |

- **Origens**: mediana por janela. **λ_e**: nível calibrado em amostra, com as frotas
  conhecidas isentas na binomial.
- **Piso**: a menor botnet de 25 pilhas, em atacantes por janela, cujas pilhas a
  configuração aponta, **em amostra / cruzada**, medianas dos cinco dias de teste.
- Em pilhas novas o filtro de inéditos limita o piso a 139. Uma pilha compartilhada toma
  a prevalência mediana do perfil além dos dez fingerprints mais comuns e, na beta-binomial, a correlação mediana deles. \* *post hoc*.

**Como ler.**

- No E1 as frotas empurram λ_e para 10⁻⁶⁰, onde o teste só aponta uma pilha a partir de
  15 a 18 origens; isentar as cinco ou seis frotas conhecidas eleva λ_e para cerca de
  10⁻²¹.
- Unida ao filtro de inéditos, a binomial aponta pilhas novas a partir de 139 atacantes
  do E1 ao E3 (o limite que k_min impõe) e a partir de 84 no E4, onde o próprio teste as
  aponta primeiro.
- Em pilhas compartilhadas o nível decide: 254 atacantes no E1, 8% da janela, e de 4 a
  19 vezes a janela mediana nos pequenos (no E2, os 1.090 atacantes do piso mediano dão
  cerca de 18 janelas de 62 origens; o 19 é a mediana, dobra a dobra, do piso dividido
  pela janela mediana dos dias de calibração daquela dobra).
- **O piso cresce com o número de pilhas** (no corpo, só os 2% e 34% do E1; o resto está
  no Apêndice E). Em pilhas compartilhadas, 50, 254 e 1.026
  atacantes no E1 para 5, 25 e 100 pilhas (2%, 8% e 34% da janela), e 0,7–2,8, 4–19 e
  24–106 janelas nos pequenos. No E2 e no E3 ele cresce mais rápido que M, por isso o
  artigo diz só que o piso cresce com as pilhas.
- **O piso não é um degrau** (seção 9.5): no E1 o escopo sozinho detém 43% de 100
  atacantes em pilhas novas, abaixo do piso de 139, como o modelo de tamanho das pilhas
  prevê.
- **As pilhas compartilhadas são, na maior parte, raras**: são sorteadas além das dez
  fingerprints mais comuns, e a prevalência mediana ali é de 2 × 10⁻⁶ no E1. Nas posições
  36 a 100 do perfil, o piso da binomial no E1 sobe para 743 atacantes (um quarto da
  janela), e nas posições 11 a 35 nenhuma botnet de 25 pilhas é apontada no E1 nem no E2.
  Acima do limite da razão (seção 9.6), nos 4 a 28 fingerprints mais comuns de
  cada endpoint, que carregam 86–94% das origens, nenhuma botnet de 25 pilhas é apontada.

As posições do perfil, na binomial / na beta-binomial (a correlação de cada faixa):

| Endpoint | Posições 11–35 | 36–100 | Além de 100 | Além de 10 (Tabela V) |
|---|---|---|---|---|
| E1 | nenhuma / nenhuma | 743 / 480 | 252 / 85 | 254 / 86 |
| E2 | nenhuma / nenhuma | 1.898 / 140 | 846 / 56 | 1.090 / 84 |
| E3 | 808 / 612 | 227 / 84 | 168 / 56 | 168 / 56 |
| E4 | 114 / 84 | 84 / 84 | (poucos fingerprints) | 84 / 84 |

"Nenhuma": nenhuma botnet de 25 pilhas, de qualquer tamanho.

### 16.4 O que a configuração detém: o gatilho decide (Seção V-C)

Uma botnet apontada só é detida nas janelas em que o gatilho de origens também dispara.
A **Fig. 2** desenha isso por endpoint. No eixo horizontal está o tamanho da botnet de 25
pilhas, em atacantes por janela (escala logarítmica, juntando os tamanhos absolutos, de 25
a 1.000, e os relativos, de um décimo à janela mediana inteira); no vertical, a fração da
botnet. A tracejada é o que o escopo sozinho bloquearia em pilhas novas, e a cheia é o que a
configuração detém. A área cinza entre elas é o que o gate deixa passar, e o triângulo
vazado marca um décimo da janela mediana. A taxa do gate e as pilhas compartilhadas ficaram
fora da figura para ela mostrar uma coisa só. A taxa do gate está na última coluna da
tabela abaixo, e as pilhas compartilhadas na Tabela V. As mesmas curvas em números
(binomial, M = 25, pilhas novas; escopo sozinho / modelo / configuração com o gatilho, em
%, e a taxa do gatilho nas janelas de ataque):

| Endpoint | 25 | 50 | 100 | 250 | 1.000 | Gatilho, de 25 a 1.000 |
|---|---|---|---|---|---|---|
| E1 | 1 / 1 / 0 | 9 / 9 / 1 | 43 / 43 / 3 | 88 / 88 / 11 | 90 / 90 / 41 | 6, 6, 8, 12, 45 |
| E2 | 1 / 1 / 0 | 9 / 9 / 3 | 43 / 43 / 28 | 88 / 88 / 88 | 90 / 90 / 90 | 15, 28, 66, 100, 100 |
| E3 | 2 / 1 / 0 | 9 / 9 / 4 | 43 / 43 / 43 | 88 / 88 / 88 | 90 / 90 / 90 | 12, 49, 100, 100, 100 |
| E4 | 34 / 39 / 5 | 51 / 48 / 42 | 79 / 79 / 79 | 90 / 90 / 90 | 90 / 90 / 90 | 23, 88, 100, 100, 100 |

- **No E1 decide o gatilho.** Ele abre em 6–13% das janelas de uma botnet de 25
  atacantes a um décimo da janela (0,7–42% conforme o dia, a um décimo), em 45% a um terço
  e em 79% a uma janela inteira. A binomial detém, então, 3,4% de 100 atacantes em pilhas
  novas e 11,8% de um décimo da janela, onde o escopo sozinho bloquearia 43,2% e 89,6%, e
  70,8% de uma janela inteira. Dia a dia, os 11,8% vão de 0,6% a 37,2%.
- **Nos endpoints pequenos decide o piso.** Uma botnet de 100 atacantes, de 1,6 a 5
  janelas ali, abre o gatilho em 66–100% das janelas, e a configuração detém 28–79% dela
  em pilhas novas e 0–69% em compartilhadas. Uma botnet do tamanho da janela abre o
  gatilho em 14–33% das janelas e fica abaixo dos pisos (2–5% detidos em pilhas novas).
- **Outros gatilhos** (*post hoc*, Tabela VI). O **gatilho sazonal** (seção 6.1) e o
  **escopo como gatilho próprio**, cada um com a binomial (em amostra), com a
  beta-binomial cruzada e com o **filtro de inéditos sozinho**, em %:

| Gatilho | Escopo | FA E1 teste | FA E1 novo | FA E2–E4 teste (maior) | FA E2–E4 novo (maior) | Novas teste | Novas novo | Compart. teste | Pico 1k | Dano |
|---|---|---|---|---|---|---|---|---|---|---|
| Origens | binomial | 0,00 | 0,00 | 0,28 | 0,69 | 11,8 | 0,0 | 7,7 | 22,2 | 32,9 |
| | beta cruzada* | 0,14 | 0,00 | 0,28 | 0,00 | 11,9 | 0,0 | 8,3 | 10,9 | 2,0 |
| | inéditos | 0,00 | 0,00 | 0,07 | 0,00 | 11,8 | 0,0 | 0,0 | 3,4 | 3,3 |
| Sazonal* | binomial | 0,00 | 0,00 | 2,64 | 0,69 | 20,4 | 15,3 | 14,4 | 22,3 | 35,2 |
| | beta cruzada | 0,07 | 0,00 | 0,21 | 0,00 | 20,4 | 15,3 | 15,1 | 10,9 | 16,9 |
| | inéditos | 0,00 | 0,00 | 0,00 | 0,00 | 20,4 | 15,3 | 0,0 | 3,4 | – |
| Sem gatilho* | binomial | 0,97 | 0,00 | 4,38 | 1,04 | 89,6 | 89,7 | 61,1 | 22,4 | 32,6 |
| | beta cruzada | 0,90 | 1,74 | 1,46 | 1,39 | 89,7 | 90,1 | 65,7 | 11,0 | 6,6 |
| | inéditos | 0,28 | 0,00 | 0,42 | 0,35 | 89,6 | 89,7 | 0,0 | 3,4 | 5,7 |

  Novas e Compart.: fração detida da botnet de um décimo da janela do E1. Pico 1k:
  disparos com 1.000 usuários, todos os endpoints. Dano: mediana sobre os falsos alarmes
  dos dias de teste. \* *post hoc*.

  - **Em pilhas novas com ao menos k_min origens, o filtro de inéditos sozinho faz o
    mesmo** que qualquer escopo, sob todo gatilho, com menos falsos alarmes e menos
    disparos em picos. É o caso da botnet de um décimo do E1 (cerca de 11 atacantes por
    pilha). Como gatilho próprio, erra em 0,28% das janelas limpas do E1 e em no máximo
    0,42% nos demais, dentro do orçamento em todo endpoint nos dois conjuntos de dias, mas
    os erros se concentram: os 4 do E1 e os 2 do console caem num só dia, e 5 dos 6 da API
    em outro.
  - **O que o teste acrescenta são as pilhas compartilhadas**, que o filtro de inéditos
    nunca aponta (14,4–15,1% atrás do sazonal e 61,1–65,7% como gatilho próprio), **e as
    pilhas novas menores que k_min**, a beta-binomial cruzada nos endpoints pequenos e a
    binomial só no SSO (no E1, E2 e E3 ela empata exatamente com o filtro de inéditos, sob
    qualquer gatilho): com 100 atacantes (3,6 por
    pilha), a beta-binomial cruzada atrás do sazonal detém 53–84% ali, contra 43% do filtro
    de inéditos, mas só 3,9% no E1, onde o sazonal abre em 7,4% dessas janelas. No E1 ela
    troca a maior parte da detecção em pilhas novas (20,4% contra 89,6% da botnet de um
    décimo) por 15,1% em compartilhadas. Como gatilho próprio ela detém 57–84% em todo
    endpoint, mas passa do orçamento.
  - O sazonal detém mais da botnet pequena no E1 (e 90,0% de uma do tamanho da janela,
    contra 70,8%). No console, passa do orçamento em três das quatro calibrações (2,64%,
    2,57% e 2,01%); só a beta-binomial cruzada fica dentro (0,21%).
  - O escopo sozinho, na binomial com frotas, fica **no limite** do orçamento no E1: 0,97%
    (intervalo de 0,53% a 1,63%, 14 de 1.440), subindo dia a dia (0, 0, 1, 5, 8 em 288
    janelas), com disparos de mediana 1,0% dos clientes. Sem a isenção de frotas, dispara em
    92 das 1.440 janelas de teste do E1 e em 95 das 288 do dia novo.
- **A leitura**: o gatilho decide o que é detido; em pilhas novas basta o filtro de
  inéditos, e o teste calibrado serve para as compartilhadas (seção 18.1).
- **Os números agregados**, que os endpoints pequenos dominam: a binomial detém 38,4% e
  77,7% de 100 e 1.000 atacantes em pilhas novas, e 21,7% e 63,3% em compartilhadas. De
  100 em pilhas novas, o filtro de inéditos sozinho detém 29,4%, e o z-score calibrado
  54,7% (23,7% em compartilhadas).
- **Dano nas janelas de ataque**: os escopos calibrados bloqueiam uma mediana de 0% dos
  clientes legítimos, no máximo 3% em nove janelas de cada dez e até 71% na pior janela
  de um endpoint pequeno.

### 16.5 O dia novo (Seção V-D)

Exportado depois das escolhas que fixaram a configuração, e analisado com ela e com as
métricas fixadas de antemão (o protocolo `fresh_day_protocol.md`, com os *hashes* das
exportações, escrito antes de o dia ser lido):

- a binomial dá 2 falsos alarmes em 1.152 janelas limpas (P = 0,27; até 3 também
  passariam);
- o teste é fraco: cerca de um falso alarme é esperado, e uma taxa triplicada seria
  sinalizada em 37% das vezes;
- o gatilho abriu em só 3 janelas limpas (0,26%, contra 3,0% nos dias de teste): o dia
  passou sobretudo porque o gatilho ficou quieto, e o artigo diz isso no texto e no
  resumo. Esse diagnóstico, o poder de 37% e os picos de 1.000 vão além das métricas do
  protocolo, e o artigo os marca assim. O escopo errou em duas delas (contra 5 de 168, P = 0,003; seção 14.7), ambas no console,
  bloqueando uma mediana de 41,2% dos clientes da janela;
- a regra básica, o termo de comparação do protocolo, disparou nas mesmas duas janelas,
  assim como o z-score calibrado (no código antes de o dia ser lido, mas fora do
  protocolo), que nos dias de teste compartilhou 4 dos 5 falsos alarmes da binomial;
- os picos de 100 usuários, a métrica 3 do protocolo, disparam a configuração em 1,1% das
  janelas;
- no SSO (E4), os picos de 1.000 usuários disparam a configuração em 97,2% das janelas,
  contra 34,1% nos dias de teste. Dos 280 disparos, 98% apontam o mesmo fingerprint: como
  o pico é sorteado do tráfego do próprio dia, esse fingerprint estava bem mais comum entre
  os clientes daquele dia do que no perfil. É uma deriva do *mix* de clientes que só um
  pico grande torna visível (o filtro de inéditos não disparou), e os filtros são leves,
  com mediana de 1,1% dos clientes da janela. A beta-binomial cruzada atrás do sazonal
  dispara em 97,6% desses picos;
- a binomial detém 38,9% e 73,4% de 100 e 1.000 atacantes em pilhas novas, e 21,5% e 60,9%
  em compartilhadas; a um décimo da janela do E1 o gatilho nunca disparou.

O protocolo foi versionado 17 horas depois do horário que ele declara; nenhum carimbo de
tempo externo atesta a ordem, e o artigo diz isso (Apêndice F).

### 16.6 As análises *post hoc* (Seção V-D)

A beta-binomial e a calibração cruzada foram construídas depois de o dia novo ter sido
lido: seus resultados são *post hoc*.

**A referência beta-binomial.**

- O nível do E1 sobe para cerca de 10⁻⁴, onde três origens apontam uma pilha, e o dos
  demais para o teto de 0,01, onde duas bastam.
- Nenhum fingerprint se qualifica como frota conhecida em amostra, então a lista de
  exceções não é necessária ali.
- O piso em pilhas compartilhadas cai para 86 atacantes no E1 (3%) e para 1,4 a 4,2
  janelas nos demais, e nas posições 36 a 100 do E1 para 480.
- Em amostra ela dispara em 0,4% das janelas limpas (22, 13 delas num só dia do console),
  com filtros que bloqueiam em média 7,7% dos
  clientes da janela, e detém 59,8% e 40,5% de 100 atacantes em pilhas novas e
  compartilhadas. No console, porém, dispara em 1,3% das janelas limpas e em 74,4% dos
  picos de 1.000 usuários (seção 16.9), o que a calibração cruzada baixa para 16,1%. No dia
  novo não deu nenhum falso alarme.

**A calibração cruzada.**

- **A binomial quase não se move**: o escopo sozinho produz filtro em 1,9% das janelas
  limpas, a configuração dispara em 6 contra 5 janelas, e detém 36,9% contra 38,4% de
  100 atacantes em pilhas novas. Sua calibração não estava favorecida.
- **O z-score perde a vantagem**: o limiar sobe por um fator mediano de 1,8, o escopo
  sozinho dispara em 2,5% (5,8% no console), e ele detém 33,6% de 100 atacantes contra
  54,7%. A vantagem vinha do limiar em amostra.
- **Só a beta-binomial quase cumpre a meta**: o escopo sozinho dispara em 1,1% das janelas
  limpas (1,5% no console) e em 1,2% no dia novo, com níveis entre 10⁻¹⁷ e 10⁻². Ela dá os
  mesmos 6 falsos alarmes da binomial, com filtros que bloqueiam uma mediana de 2,0% dos
  clientes da janela, e detém 48,0% de 100 atacantes em pilhas novas e 27,2% em
  compartilhadas, cujo piso fica em 6% da janela do E1 e no máximo 4,4 janelas nos
  demais, abaixo do piso cruzado da binomial em todo endpoint. Esse piso mais baixo vale
  para a cauda rara da Tabela V: nas posições 36 a 100 do E1, a beta-binomial cruzada
  precisa de 949 atacantes, acima dos 743 da binomial. Na calibração cruzada, uma frota conhecida aparece no E1 em três dos cinco dias.
- **O desenho**: um primeiro desenho, que calibrava só no último dia de calibração, foi
  descartado depois de ver os resultados: um dia só perde os eventos raros de frota que
  fixam o nível.

**A Fig. 3** (Seção V-C) tem dois painéis (pilhas novas e compartilhadas, 100 atacantes
por janela): no eixo horizontal, a fração de janelas limpas com falso alarme (escala
logarítmica, com as taxas zero desenhadas em 0,01%); no vertical, a fração da botnet
bloqueada. São sete configurações: a regra básica, a binomial do protocolo, o z-score
calibrado, a beta-binomial, o filtro de inéditos e o escopo sozinho, da binomial e da
beta-binomial. Marcadores cheios são os dias de teste; vazados, o dia novo; cinza, a
calibração cruzada. As setas ligam os pontos em amostra da binomial, da beta-binomial e
do z-score aos cruzados; a beta-binomial e a calibração cruzada são *post hoc*.

### 16.7 A fronteira e a rotatividade de JA4 (Seção V-D)

- **A fronteira vale em tráfego real.** Uma botnet nas 25 fingerprints mais comuns do
  endpoint (o caso adversarial) passa em sua maior parte: a binomial detém 7,0% e 23,8% de
  100 e 1.000 atacantes, e nenhum nos dois maiores endpoints, onde quase todos esses
  fingerprints estão acima do limite da razão, mas 73,5% de 1.000 no SSO, onde só 4 ou 5
  estão.
- **Fingerprints inéditos aparecem todo dia**, até 345 por dia no E1, mas raramente se
  concentram: 0,21% das janelas dos dias de teste têm uma com pelo menos k_min origens, um
  candidato para o filtro de inéditos.

### 16.8 O WAF não serve de rótulo

- O WAF bloqueou clientes em toda janela do E2 ao E4, uma mediana de 9%, 63% e 39% de cada
  janela, e nenhum no E1. Esses clientes estão, na maior parte, em fingerprints comuns: o mais comum da janela tem 13–55% deles, e só 25–37% estão em fingerprints que nenhum
  cliente não bloqueado da mesma janela apresenta.
- **Perfil sem os bloqueados** (o do escopo atrás do WAF): 84–99% dos clientes que os
  escopos bloqueariam no tráfego completo da API e do SSO foram bloqueados pelo WAF. Essa
  concordância está embutida: um fingerprint estável só é enriquecido ali se 70–88% dos seus
  clientes foram bloqueados (70% no console, 88% na API, 80% no SSO; seção 14.8).
- **Perfil com todos os clientes** (o de um escopo na frente do WAF): na API e no SSO os
  escopos produzem filtro em 2–3% das janelas, e do E2 ao E4 0,4–33% dos clientes que
  bloqueariam foram bloqueados, menos que uma escolha aleatória em todo endpoint (10–63%),
  para os três escopos relativos ao perfil. O filtro de inéditos é a exceção no console
  (precisão de 29% contra 10%, em 0,14% das janelas). Eles pegam de 0 a 2 dos 38 surtos de bloqueios
  do WAF, mais ou menos como o acaso (no máximo 0,5), e, no console, dois escopos pegam 5
  de 33 surtos contra menos de 1 por acaso, mas casam menos de 1% dos clientes bloqueados.
- **A leitura, nos dois sentidos**: as populações do WAF fazem parte do tráfego de todo
  dia, e um escopo que lê desvios desse tráfego as ignora por construção. Os veredictos
  não podem validar o escopo, e o escopo não recupera o que este WAF bloqueia.

### 16.9 Por endpoint e outros detalhes (Apêndice E)

A antiga Tabela VI repetia a Tabela IV por endpoint (dias de teste, em amostra), em %.
Ela saiu do artigo na rodada 29, porque a Fig. 2, a Tabela V e a Tabela VI (os gatilhos)
já mostram o essencial por endpoint. Os valores ficam aqui, com as linhas da
beta-binomial (*post hoc*):

| | Escopo | FA | Sem gatilho | Dano | Pico 1k | Novas 0,1× | Novas 1× | Compart. 0,1× | Compart. 1× |
|---|---|---|---|---|---|---|---|---|---|
| E1 | binomial | 0,0 | 1,0 | – | 0,3 | 11,8 | 70,8 | 7,7 | 68,6 |
| | beta-binomial* | 0,1 | 2,1 | 0,2 | 1,0 | 11,9 | 70,8 | 10,0 | 67,8 |
| E2 | binomial | 0,3 | 4,4 | 31,4 | 20,7 | 0,0 | 5,0 | 0,0 | 0,0 |
| | beta-binomial* | 1,3 | 10,8 | 10,7 | 74,4 | 0,7 | 25,9 | 0,2 | 13,2 |
| E3 | binomial | 0,1 | 1,8 | 48,5 | 33,8 | 0,0 | 1,9 | 0,0 | 0,5 |
| | beta-binomial* | 0,0 | 3,2 | – | 28,3 | 0,3 | 22,7 | 0,3 | 13,9 |
| E4 | binomial | 0,0 | 1,5 | – | 34,1 | 0,1 | 2,1 | 0,0 | 1,5 |
| | beta-binomial* | 0,1 | 1,4 | 3,5 | 9,8 | 0,1 | 6,0 | 0,1 | 3,9 |

O dano é uma mediana sobre poucos alarmes: 4 no E2 na binomial (19 na beta-binomial,
que concentra ali 19 dos seus 22 falsos alarmes), no máximo 2 nos demais.

Outros detalhes do Apêndice E:

- As exportações não trazem prefixos, então o escopo é julgado só pela JA4.
- Sem isentar frotas, o teste sozinho produz filtro em 1,5–6,3% das janelas do dia
  seguinte. Numa janela limpa do E2 ou do E3, a regra aponta uma frota e bloqueia cerca de
  metade dos clientes da janela, e o gatilho de origens reduz esses falsos alarmes à
  metade.
- O z-score sem calibração, atrás do gatilho de Ω, dispara em 2,6% das janelas limpas e em
  64,5% dos picos de 100 usuários (86,8% dos de 1.000).
- Das quatro frações de frota testadas nos três primeiros dias de teste, só a de 5% não
  passou os falsos alarmes da regra básica (5 contra 6; as outras, de 12 a 16); pelo dano
  esperado, a de 0,5% seria cerca de 25 vezes mais leve (seção 10.1).
- **O escopo como gatilho**, agregado: com as frotas conhecidas dispara em 2,2% das
  janelas limpas e 0,5% no dia novo, contra 3,5% e 8,8% sem elas. Na beta-binomial, a um
  décimo da janela do E1, detém 90,0% e 78,3% em pilhas novas e compartilhadas, com 2,1%
  das janelas limpas do E1.
- Um perfil por hora do dia não ajudou. Picos de 1.000 usuários disparam a regra básica
  em 21,8% das janelas.

## 17. Especificação, troca e custo (Seção VI; Apêndices B e D)

### 17.1 A consulta compilada confere

A consulta compilada da ontologia devolveu as contagens exportadas de origens distintas e
de pares /24 em toda janela de dois dias de produção, 1.152 janelas cada, e os tamanhos
das classes de JA4 nas 288 janelas por dia em que o WAF não bloqueou nenhum cliente. Em
6.000 sessões geradas, a execução em DuckDB reproduz a decomposição de Ω do código com
diferença máxima de 0,0.

### 17.2 STIX, TAXII, MISP e DOTS

- Os pacotes STIX 2.1 do escopo e da cadeia de evidência passam no validador da OASIS em
  modo estrito e atravessam o servidor TAXII 2.1 de referência sem mudança, exceto a
  definição de extensão, que o servidor não serve.
- O importador STIX do MISP descarta os fingerprints: o STIX 2.1 só as carrega numa extensão
  que o importador não mapeia para o objeto JA4 do próprio MISP.
- Os filtros do DOTS casam só campos de rede e transporte. O modelo de ACL que eles imitam
  casa parâmetros TLS do cliente desde a RFC 9761 (2025), como os valores que o perfil MUD
  de um dispositivo permite, mas não nomeia nenhum fingerprint, e o DOTS define os seus
  próprios filtros em vez de estender esse modelo.
- Nos dois casos o escopo se alargaria para o endpoint ou para prefixos de endereço. O
  que falta: uma propriedade padrão para JA4 no STIX e no DOTS, e um mapeamento da extensão
  STIX para o objeto JA4 do MISP.
- O OCSF, um esquema aberto de eventos e achados de segurança, registra JA4 em eventos
  de rede desde a versão 1.3.0 (agosto de 2024) e nas evidências de achados desde a
  1.4.0 (janeiro de 2025). Ele não define filtro nem remediação sobre JA4: as classes de
  remediação carregam contramedidas do D3FEND.
- **É a lacuna por trás da contribuição (iii), a ontologia**: dos padrões examinados, STIX 2.1, DOTS e Flowspec
  não têm propriedade para JA4 no vocabulário central, e o OCSF a registra sem filtro
  sobre ela. O artigo sugere um casamento de JA4 nos filtros do DOTS e uma propriedade
  JA4 no STIX, por exemplo numa extensão TLS do objeto *network-traffic*.

### 17.3 O custo (Apêndice D, Fig. 4)

A admissão acontece por requisição e a agregação de Ω uma vez por janela, então as duas
são medidas separadamente numa janela sintética (30% das sessões numa campanha com uma JA4
de botnet, JA4 legítimas de um conjunto de 2.000, oito endpoints, /24 dispersos), com
arestas de pares, como as regras estão escritas, e com contagens de classe, que dão o
mesmo Ω a menos de 7 × 10⁻¹².

| Operação | Com arestas de pares | Com contagens de classe |
|---|---|---|
| Admissão por sessão | 2,3 µs a \|S_W\| = 100, 127 µs a 10.000 (148 a 6.495 pares candidatos, 15–21 ns cada) | 0,33–0,42 µs de 100 a 100.000 sessões (constante, ~0,37 µs) |
| Agregação | 0,84 s a 100 e 52,8 s a 1.000 (198–309 µs por aresta RDF) | 0,33 s a 1.000 (161 vezes mais rápido) e 26,4 s a 100.000 (linear) |

A camada simbólica roda em `rdflib` no lugar de Jena/TDB2, então os números são um limite
superior. O termo quadrático vive no **valor** de Ω, que conta pares, e nas arestas das
sub-relações não transitivas, não no custo de contar classes. A Fig. 4 mostra quatro
curvas (admissão e agregação, cada uma com arestas de pares e com contagens de classe),
com retas pontilhadas de inclinação de referência.

### 17.4 A janela W

No gerador, W é o intervalo que separa as sessões de um endpoint em *clusters*. Nos
cenários de vocabulário quase uniforme contra uma botnet monolítica (os da seção 17.6;
K = 1.000, n = 10), de W = 60 s a 1.800 s, a AUC de (d) fica em 0,976–0,978 e a de (c) em
0,663–0,664. O
*cluster* da campanha tem 1.977–1.998 sessões em todo W, enquanto o *cluster* médio cresce
de 132 para 867, e o atributo discriminante é a **fração** do *cluster* que compartilha
uma JA4: a insensibilidade é uma propriedade do gerador.

### 17.5 Particionamento numa CDN

A regra lê um endpoint por S, então particionar por endpoint a avalia **exatamente**, sem
tráfego entre partições. Uma campanha que espalha uma JA4 por muitos endpoints junta
poucos pares em cada partição; um *sketch* global sobre identificadores de peso alto, não
implementado, precisaria ter a revocação medida antes.

### 17.6 A calibração dos pesos (Apêndice B)

Nas capturas de laboratório, com poucas dezenas de JA4, a otimização inverte o sinal do
TLS, porque sessões legítimas compartilham fingerprints mais do que campanhas parcialmente
coordenadas. Os pesos foram calibrados em cenários de vocabulário legítimo quase uniforme
(cerca de 800 fingerprints por 1.000 sessões) contra uma botnet monolítica, maximizando a
AUC por sessão de

> w_tls · z(ja4) + w_ep · z(convergência de endpoint) + w_net · z(proximidade de rede)

na grade {0,3 … 1,0}³ (125 combinações, 60 cenários, 91.500 sessões). O resultado é
(w_tls = 1,0; w_ep = 0,3; w_net = 0,3). Só o fingerprint TLS discrimina sozinha (AUC isolada
0,93, contra 0,50 da convergência de endpoint e 0,58 da proximidade de rede). Com os pesos
de TLS e de rede fixos, todo peso de endpoint da grade atinge a mesma AUC ótima de 0,943,
assim como os pesos da ontologia (1,0; 0,6; 0,3). A calibração sustenta só o topo da
ordem: os pesos médio e baixo não são identificáveis, e a regra por janela detecta tão bem
com pesos uniformes.

---

# Parte V. Recomendações, limites e consulta

## 18. Qual configuração recomendar, e os limites (Seção VI; Apêndice C)

### 18.1 Qual configuração recomendar

- **O piso e o gatilho decidem, por endpoint.** No E1, o escopo aponta uma botnet de
  menos de um décimo da janela (os pisos do E1, binomial e beta-binomial, em amostra e
  cruzados, vão de 85 a 286 atacantes), mas o gatilho de origens deixa passar a maior
  parte dela (Tabela VI). Nos três endpoints pequenos, a
  binomial só aponta pilhas compartilhadas a partir de 4 a 19 janelas e pilhas novas a
  partir de 2 a 4 janelas: abaixo disso o recurso é o limite de taxa ou o desafio a
  todos. Mas o gatilho também limita ali: uma botnet do tamanho da janela mediana abre o
  gatilho em só 14–33% das janelas (32,2%, 32,8% e 13,7% no E2, E3 e E4).
- **Entre configurações** (Seções V-B e V-D e Apêndice E), em amostra a binomial dá 0,25 falso alarme por endpoint e dia (4 dos 5 no console),
  e a beta-binomial e o z-score calibrado cerca de um, contra um orçamento do escopo de
  2,9; seus filtros bloqueiam uma mediana de um terço e de um décimo dos clientes da
  janela. Na calibração cruzada, a beta-binomial empata com os 6 falsos alarmes da
  binomial, com filtros mais leves, menos disparos em picos legítimos e um piso menor em
  pilhas compartilhadas em todo endpoint, enquanto o z-score perde a vantagem em detecção.
- **A recomendação.** Só a binomial atrás do gatilho de origens foi testada num dia que
  não tinha visto, como fixado de antemão, então é a configuração que o artigo implantaria
  agora em todo endpoint, com o recurso abaixo do piso. Uma botnet que não abre o gatilho
  não encontra nem filtro nem recurso em nenhum endpoint, por isso ela detém poucas
  botnets pequenas no E1 (nenhuma no dia novo). No console, onde caíram os dois falsos
  alarmes do dia novo (mediana de 41,2% dos clientes), um desafio pode ser a primeira
  resposta mais segura. O próximo teste, pré-especificado
  em dias novos, num ciclo semanal e com carimbo de tempo externo, teria como **base o
  filtro de inéditos como gatilho próprio**, que igualou todo escopo em pilhas novas de ao
  menos k_min origens dentro do orçamento em todo endpoint, e cobriria botnets de 100
  atacantes além das de um décimo da janela. Contra ela rodariam a **beta-binomial cruzada
  atrás do gatilho sazonal**, cujo ganho está nas pilhas compartilhadas e nas pilhas novas
  menores, e, só no E1, o **escopo binomial com frotas como gatilho próprio**, no limite do
  orçamento ali, subindo dia a dia e dependente da isenção de frotas. A beta-binomial
  cruzada como gatilho próprio fica de fora: no E1 ela detém 58% de 100 atacantes em
  pilhas novas (contra 43% do filtro de inéditos), mas disparou em 1,74% das janelas do
  dia novo (5 de 288).
- **Como se chegou aqui.** A rodada 17 dizia que o escopo sozinho cabia no orçamento no E1
  também na beta-binomial, o que era falso (2,08% em amostra); a rodada 18 corrigiu e
  propôs a beta-binomial atrás do sazonal como primária. A revisão da rodada 19 mostrou que
  em pilhas novas o filtro de inéditos sozinho faz o mesmo com menos alarmes, e a
  recomendação passou a tê-lo como base de comparação. A da rodada 20 mostrou que essa
  paridade vale só com ao menos k_min origens por pilha, e o texto passou a dizê-lo.

### 18.2 O ganho depende do regime

As campanhas geradas, de um terço à metade da janela, são mais fáceis que o décimo em que a
produção mostra o gatilho falhando. Limites por IP resolvem inundações de origem única, e
nos ataques de bases públicas um classificador por sessão forte já basta (Apêndice C). Só
as campanhas distribuídas **e** furtivas precisam de evidência entre sessões.

### 18.3 O que cada avaliação estabelece

- O gerador mostra o mecanismo, com uma imitação imposta por construção. Suas pilhas nunca
  aparecem no vocabulário legítimo (por isso o filtro de inéditos empata com o escopo
  ali), e um modelo ajustado a um número de pilhas não se transfere para outro.
- A produção mede falsos alarmes em clientes reais, e detecção só para uma botnet injetada
  de uma forma, 25 pilhas uniformes, em nove dias dos endpoints de um operador, poucos
  demais para calibrar um ciclo semanal.
- As cinco escolhas da Tabela II foram feitas nos dias em que são reportadas: só o dia
  novo as põe à prova, e a calibração cruzada remove só o ajuste em amostra dos níveis.
- Nenhuma avaliação cobre uma campanha furtiva capturada.

### 18.4 O escopo depende de um discriminador observável

- Um bot fora do modelo de ameaça que apresente um fingerprint comum o derrota, no gerador e
  em produção.
- O *Encrypted Client Hello* (ECH) esconde a JA4 de observadores no caminho, mas não de um
  defensor que termina o TLS, como aqui.
- O perfil precisa ser renovado. Uma versão de software que dê um fingerprint novo a uma
  população grande chegaria de imediato ao filtro de inéditos, e os nove dias não mostraram
  nenhum evento assim.
- Os picos legítimos sorteiam usuários do *mix* do próprio dia; um surto de um só tipo de
  cliente, o caso mais difícil, não foi injetado.
- Um atacante que molde o perfil ou a isenção de frotas antes da campanha não foi avaliado,
  então os perfis devem ser reconstruídos a partir das janelas que o escopo não apontou.

### 18.5 O que a ontologia acrescenta, e o que não acrescenta

Ela não acrescenta nada aos números de detecção nem ao gatilho, e o teste do escopo é
estatístico. Ela é a especificação que o operador implanta e troca: o que cada sub-relação
de igualdade iguala, seu peso e a unidade das suas classes, compilados na consulta que o
armazenamento de logs executa e levados à cadeia de evidência. O título nomeia o que a
evidência sustenta: o escopo por fingerprint TLS, os pisos de calibração e o dano colateral
nos endpoints de um operador. O grafo de conhecimento não é o método; a ontologia é a
especificação.

### 18.6 Outras limitações (Apêndice C)

- **Instrumentação e implantação.** Extração parcial ou ruidosa de sessões, identidades e
  fingerprints degrada o método. Contar origens por endereço subconta usuários atrás de um
  CGNAT e sobreconta clientes que trocam endereços IPv6 de privacidade (a unidade natural
  deles é o /64). A execução em produção é *offline*, sobre contagens agregadas por
  endpoint; uma implantação ao vivo ainda precisa do particionamento da seção 17.5.
- **Cobertura.** Ataques HTTP/2 e outros protocolos (DNS, gRPC) precisam de sub-relações
  além da família *Slow HTTP DoS* sobre HTTP/1.1. Identidade reutilizada, padrão temporal e
  assinatura de *payload* estão especificadas, mas não exercitadas, então seus pesos não
  foram testados.
- **Amplitude dos dados.** A validação de laboratório cobre uma base e um ataque contra o
  KLAGE, mais seis ataques entre CICIDS2017 e CIC-IoT2023. Não há captura independente do
  regime furtivo: o BCCC-cPacket-Cloud-DDoS-2024 critica a cobertura de camada de aplicação
  das bases anteriores e traz 17 cenários de DDoS baseados em TCP.

### 18.7 O trabalho futuro (Seção VII)

Um teste pré-especificado, em dias novos, desses gatilhos contra o filtro de inéditos
como gatilho próprio, ataques HTTP/2 e uma campanha furtiva capturada.

## 19. Os números do artigo, num só lugar

**O método**
- ρ = 3; k_min = 5; λ_e ≤ 0,01; orçamento de 1% das janelas de calibração, 2,9 de 288 por
  dia; gatilho e τ no percentil 99.
- Pesos: TLS 1,0; endpoint 0,6; rede 0,3 (identidade 1,0; temporal 0,9; *payload* 0,6).
- Moda falha quando M ≥ 3 (M < 2,3 com p₁ = 38,4% e A = n_b).
- Piso de pilha nova sob a união: ⌈5M/0,9⌉ = 139 (M = 25); 28 (M = 5); 556 (M = 100).

**O gerador**
- Medição real: 495 fingerprints, 38,4% no mais comum, 93,8% nos dez mais comuns; Zipf
  α = 1,5 canônico.
- Moda: 0,0% do ataque e 39,0% do legítimo a partir de 5 pilhas (61,1% com α = 2,0).
- Teste e z-score: 90% até 25 pilhas, sem dano observado; teste 38,6% a 100 pilhas (89,6%
  com perfil maior); inéditos 88,1% a 100.
- Adversarial: teste 30,4% com 3,78% de dano.
- (d): AUC 0,927/0,982; entre valores de M, 0,48–0,75; (a) no acaso (0,498/0,503).

**Produção** (dias de teste, em amostra, salvo "cruzada" ou "dia novo")
- E1–E4: 2.983, 62, 41 e 20 origens na janela mediana, os 4 de 12 endpoints exportados
  com TLS e janela mediana de pelo menos k_min; 5.643 janelas limpas de teste; 1.152 no
  dia novo.
- Falsos alarmes: binomial 0,1% (5; exato 0,03–0,21%; 4 no console; cada um bloqueia uma
  mediana de 32,9%), z-score e beta 0,4% (20 e 22, 13 de cada num dia do console).
- Componentes sozinhos: escopo 2,2% (binomial), 4,4% (beta), 6,1% (z); gatilho 3,0% (5,4% no E1).
  Conjuntos: 5, 22 e 20 contra 3,5, 7,5 e 11,9 se independentes (Poisson: P = 0,27,
  1,4 × 10⁻⁵ e 0,020); cruzada, 6, 6 e 13 contra 3,2, 1,8 e 4,6 (0,10, 0,011 e 0,001).
- Fração de frotas: pela taxa × dano mediano, a de 0,5% dava 0,0028% por janela limpa
  contra 0,070% da escolhida (5%), cerca de 25 vezes menos.
- Dano médio por alarme 30,6% / 11,4% / 7,7%; esperado 0,03–0,04% por janela limpa.
- Piso: pilhas novas 139 (84 no E4); compartilhadas, binomial 254 no E1 (8%) e 4–19
  janelas; beta 86 (3%) e 1,4–4,2 janelas; cruzada beta 6% e ≤ 4,4 janelas. Por M, no
  E1 em compartilhadas: 50 / 254 / 1.026 (M = 5 / 25 / 100).
- Picos de 1.000: a binomial dispara em 22,2%, com filtros de mediana 4,3% (p90 20,6%).
- Limite da razão: b > 0,9/(ρM) = 1,2%; os 4 a 28 fingerprints mais comuns, 86–94% das
  origens, nunca são apontadas por uma botnet de 25 pilhas.
- O gatilho no E1: abre em 6–13% das janelas de 25 atacantes a um décimo da janela; a
  binomial detém 3,4% de 100, 11,8% de um décimo (0,6–37,2% por dia), 70,8% de uma janela.
- Outros gatilhos no E1 (*post hoc*, Tabela VI), um décimo da janela: sazonal 20,4%
  (15,3% no dia novo); com a beta cruzada, 4 de 5.643 e 0 de 1.152 falsos alarmes; com a
  binomial, o console vai a 2,64%. Escopo sozinho: cerca de 90% em todo dia; binomial 0,97%
  no E1 (14 de 1.440, IC 0,53–1,63%; 0, 0, 1, 5, 8 por dia; 92 sem frotas, 95 de 288 no
  dia novo), beta cruzada 0,90% e 1,74% no dia novo; nos pequenos, a binomial dá 1,5–4,4%.
- Com 100 atacantes em pilhas novas (abaixo de k_min por pilha), a beta-binomial cruzada
  atrás do sazonal detém 53–84% nos pequenos e 3,9% no E1, contra 43% do filtro de inéditos.
- O filtro de inéditos sozinho (*post hoc*, Tabela VI): atrás do sazonal, 0 falsos
  alarmes e os mesmos 20,4% / 15,3%; como gatilho próprio, 0,28% no E1 (no máximo 0,42% nos
  demais) e 89,6% / 89,7%; em pilhas compartilhadas, 0%. O teste: 14,4–15,1% das
  compartilhadas atrás do sazonal e 61,1–65,7% como gatilho próprio.
- Detido pela binomial, agregado: 38,4% / 77,7% de 100 / 1.000 (novas), 21,7% / 63,3%
  (compartilhadas); inéditos sozinho 29,4%.
- Cruzada: binomial 6 contra 5 alarmes; z-score 13 alarmes, 2,5% sozinho, 33,6% contra
  54,7% de 100 atacantes; beta 1,1% sozinho, 6 alarmes, dano mediano 2,0%.
- Adversarial: 7,0% / 23,8%, nenhum no E1 e E2.
- WAF: piso embutido 70–88% (perfil sem bloqueados); com perfil de todos os clientes,
  precisão 0,4–33% contra 10–63% aleatória, 0–2 de 38 surtos na API e no SSO.
- Dia novo: 2 alarmes em 1.152, P = 0,27, poder 0,37; gatilho aberto em 3 janelas
  (0,26% contra 3,0%), escopo errou em 2 (P = 0,003); picos de 100: 1,1%; picos de 1.000
  no SSO: 97,2% (34,1% nos de teste), 98% num fingerprint, filtros de 1,1%.

**Especificação e custo**
- Consulta compilada: origens e pares /24 iguais em todas as janelas de dois dias; tamanhos
  das classes de JA4 iguais nas 288 janelas por dia sem bloqueio do WAF; um sinal novo = 4
  triplas.
- Admissão constante ~0,37 µs; agregação linear, 26,4 s a 100.000 sessões; arestas de
  pares 52,8 s a 1.000.

## 20. Glossário

### Siglas

| Sigla | Significado |
|---|---|
| ALPN | *Application-Layer Protocol Negotiation*, o protocolo de aplicação pedido no ClientHello |
| ASN | *Autonomous System Number*, o número do sistema autônomo de uma rede |
| AUC | Área sob a curva ROC |
| CDN | *Content Delivery Network*, rede de distribuição de conteúdo |
| CGNAT | NAT de operadora (*carrier-grade NAT*) |
| CVE | *Common Vulnerabilities and Exposures* |
| DDoS | Negação de serviço distribuída |
| DOTS | *DDoS Open Threat Signaling*, os canais IETF para pedir mitigação |
| DTW | *Dynamic Time Warping*, distância entre sequências temporais |
| ECH | *Encrypted Client Hello* |
| FA | Falso alarme |
| FPR | Taxa de falsos positivos |
| HHH | *Hierarchical heavy hitters* |
| JA4 | Fingerprint digital do ClientHello TLS |
| JSON-LD | JSON para dados ligados |
| JWT | *JSON Web Token* |
| KS | Teste de Kolmogorov–Smirnov |
| L7 | Camada de aplicação |
| MISP | Plataforma aberta de troca de inteligência de ameaças |
| OWL | *Web Ontology Language* |
| PCA | Análise de componentes principais |
| PoP | Ponto de presença de uma CDN |
| RF | *Random Forest* |
| ROC | *Receiver Operating Characteristic* |
| RUM | *Real-user monitoring*, monitoramento de usuário real (E1) |
| SNI | *Server Name Indication* |
| SPARQL | Linguagem de consulta a grafos RDF |
| SSO | *Single sign-on* (E4) |
| STIX | *Structured Threat Information Expression* |
| SWRL | *Semantic Web Rule Language* |
| TAXII | Protocolo de transporte de STIX |
| TLS | *Transport Layer Security* |
| WAF | *Web application firewall* |

### Símbolos

| Símbolo | Significado |
|---|---|
| A | Atacantes por janela |
| M | Número de pilhas TLS da botnet |
| K | Dispositivos que o atacante controla (grau de distribuição) |
| n | Origens distintas do alarme (ou da janela) |
| n₀ | Origens da janela mediana do endpoint |
| n_b | Origens legítimas |
| n_k | Tamanho, em origens, da classe k de uma sub-relação |
| c(f) | Origens do alarme com o fingerprint f |
| N | Pares origem–fingerprint do perfil |
| b(f) | Prevalência de f no perfil, mais 1/N |
| \|F\| | Fingerprints do perfil e do alarme juntos (divisor de Bonferroni) |
| ρ | Razão mínima de enriquecimento (3) |
| λ_e | Nível calibrado do endpoint e |
| c_min | Menor contagem que o nível aponta |
| k_min | Mínimo de origens (5) |
| τ_cluster | Limiar de Ω (percentil 99) |
| Ω(S) | Massa de coordenação |
| wᵢ, Eᵢ(S) | Peso e pares ligados da sub-relação i |
| φ | Correlação dentro da janela (beta-binomial) |
| a, β | Parâmetros da beta |
| z | z-score de um fingerprint |
| α | Expoente da curva de Zipf |
| p₁ | Fração das origens legítimas no fingerprint mais comum |
| S, s | Fração bloqueada pelo WAF na janela; no fingerprint |
| p₀, L | Taxa de acerto fora dos surtos; duração de um surto |
| r | Taxa de falso alarme dos dias de teste (5/5.643) |

### Termos em inglês das tabelas e figuras

| Termo | Onde aparece | O que quer dizer |
|---|---|---|
| *Gate* | Tabelas II e VI | o gatilho de volume que precisa abrir antes de o escopo agir |
| *Origin gate* | Tabela VI | o gate de origens distintas, no percentil 99 (o do protocolo) |
| *Seasonal gate* | Tabela VI | o gate sazonal, *post hoc*, contra a mediana da mesma hora |
| *No gate* | Tabelas IV e VI, Fig. 3 | sem gate: o escopo age em toda janela e é o próprio gatilho |
| *Scope alone* | Figs. 2 e 3 | o mesmo que *no gate*: o que o escopo barraria sem esperar o gate |
| *Own trigger* | Fig. 3 | o filtro de inéditos como o próprio gatilho, sem gate |
| *Lost to the gate* | Fig. 2 | a área cinza: o que o escopo apontaria, mas o gate deixa passar |
| FA | Tabelas IV e VI | *false alarms*: a fração das janelas limpas em que algo foi barrado |
| *Coll.* | Tabelas IV e VI | *collateral*: a fração dos clientes da janela que um falso alarme barra (mediana) |
| *Fl. 1k* | Tabelas IV e VI | *flash crowd* de 1.000 usuários reais: em quantas janelas ele dispara o filtro |
| *New*, *Shared* | Tabelas IV a VI, Figs. 2 e 3 | fingerprints da botnet ausentes do tráfego legítimo, ou que clientes reais também usam |
| 0.1×, 1× | Tabela IV | uma botnet de um décimo da janela típica, ou de uma janela inteira |
| *In sample*, *cross-fitted* | Tabelas IV e V, Fig. 3 | a calibração em amostra, ou a cruzada, contra os outros dias |
| *Held-out day*, *held* | Tabelas II, IV e VI | o dia novo, analisado com tudo fixado antes |
| *Post hoc* (\*) | todas | analisado depois de ver o dia novo |
| *Budget* | texto | o orçamento de 1% das janelas sem ataque |

## 21. Onde está cada coisa

**Os artigos**
- `papers/http-session-noms/article.tex`: o artigo em inglês, a versão submetida (12
  páginas, corpo em 8).
- `papers/http-session-noms-pt/article.tex`: a versão em português, ainda não sincronizada
  com a inglesa (este guia segue a inglesa).
- `papers/http-session-noms/figures/`: `make_figures_en.py` gera as Figs. 2 a 4;
  `src-drawio/fig1_scoping.drawio` é a fonte da Fig. 1.

**O código do método e da produção** (`experiments/sprint-6-noms/scripts/`)
- `rule_detection_production.py`: a avaliação por janela em produção (teste, z-score,
  inéditos, união, frotas, calibração do nível, beta-binomial com `--overdispersion`,
  calibração cruzada com `--split crossfit`, perfil com todos os clientes com
  `--waf-in-profile`, `log_tail`).
- `production_tables.py`: as Tabelas IV a VII, os dados das Figs. 2 e 3, o gatilho
  sazonal, o dano dos disparos em picos e a concentração deles (`flash_concentration`,
  só contagens), além de taxas, intervalos, dano, piso (`floor`, `deployed_floor`) e o
  bloco `sweep`.
- `waf_labels.py`: os veredictos do WAF como rótulos, sob os dois perfis.
- `ja4_churn.py`: a rotatividade de fingerprints.
- `compile_counts.py`: compila a consulta de contagem a partir da ontologia.
- `symbolic_detector.py`, `unseen_synth.py`, `rule_detection.py`, `cross_m_generalization.py`,
  `bench_latency.py`: Tabela III, a regra por janela, os testes entre valores de M e o custo
  (Fig. 4).
- `floor_bands.py`: o piso em pilhas compartilhadas por faixa de popularidade, na
  correlação de cada faixa, e os fingerprints acima do limite da razão (`make floor-bands`).
- `audit_paper.py`: confere cada número do artigo contra os resultados (`make audit`).

**Os resultados** (`experiments/sprint-6-noms/results/`)
- `production_tables.json`, `floor_bands.json`, `waf_labels.json`, `ja4_churn.json`: os resumos anonimizados de
  produção.
- `fresh_day_protocol.md`: o protocolo do dia novo.
- `compile_check.json`, `compile_production_check*.json`, `stix_validation.json`: a
  especificação e a troca.

**A ontologia e os documentos**
- `ontology/ddos_ontology.owl`: a ontologia (pesos, `kg:classKey`, `kg:countUnit`).
- `docs/concepts.md`: os conceitos e as fórmulas; `docs/metrics.md`: as métricas;
  `docs/evaluation.md`: o desenho da avaliação; `docs/runtime.md`: o custo.
- `experiments/sprint-6-noms/README.md`: o registro de cada experimento de produção.

**Os comandos**
- `cd experiments/sprint-6-noms && make audit`: confere o artigo.
- `make production-tables waf-labels`: regenera as tabelas de produção a partir dos
  resumos.
- `make compile-check stix-ingest`: confere a consulta compilada e a troca em STIX.
- `pdflatex article && bibtex article && pdflatex article && pdflatex article`, em
  `papers/http-session-noms/`: compila o artigo.
