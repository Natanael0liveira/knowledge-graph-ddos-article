# Guia de estudo: escopo calibrado por fingerprint TLS

*TLS-Fingerprint Scoping of Application-Layer DDoS Mitigation: Calibration Floors and
Collateral on a CDN Operator's Endpoints*

Este guia serve para entender o artigo a ponto de explicá-lo com as suas palavras, ler cada
tabela e figura e saber o que ele mostra e o que não mostra. A versão que vale é o artigo em
inglês, `papers/http-session-noms/article.tex`, e as seções, tabelas e figuras citadas aqui são
as dele. Os números vêm do artigo, que `make audit` confere contra os resultados. Esta versão
acompanha o artigo da rodada 76 (2026-10-20).

## Como usar este guia

O guia segue quatro princípios de estudo:

- **Do geral para o detalhe.** A Parte 1 conta a história inteira em 15 minutos. A Parte 2 volta
  a cada peça do método, e a Parte 3, às evidências. Cada parte se apoia na anterior.
- **Uma pergunta por seção.** Cada seção começa pela pergunta que responde e fecha com o que
  guardar.
- **Um exemplo do começo ao fim.** A portaria de um prédio e uma janela de 1.000 visitantes, com
  números redondos e hipotéticos, acompanham as explicações.
- **Lembrar em vez de reler.** Cada parte termina com algumas perguntas. Responda de cabeça antes
  de abrir a resposta: tentar lembrar fixa mais do que ler de novo.

As contas ficam recolhidas nas caixas **A conta**, para quem quiser ver de onde vem cada número.
Com pouco tempo, leia a Parte 1 e a seção 4.1.

**Convenções.** Vírgula decimal (0,1%). Os termos em inglês que as tabelas e figuras imprimem
ficam em inglês e estão no glossário (4.2). Nas tabelas, `*` marca o que é *post hoc*, pensado
depois de ver os dados, e `†`, o que usa calibração cruzada.

**Sumário**
- **Parte 1. A história em 15 minutos:** 1.1 O trabalho em cinco frases · 1.2 A portaria de um
  prédio · 1.3 O mapa do método · 1.4 O que o trabalho mostrou · 1.5 O que o artigo recomenda ·
  1.6 Os limites
- **Parte 2. Como o método funciona:** 2.1 O que o sistema vê · 2.2 O gatilho · 2.3 O escopo ·
  2.4 A calibração · 2.5 O piso · 2.6 As variantes · 2.7 A ontologia · 2.8 Um exemplo completo
- **Parte 3. As evidências:** 3.1 Como o artigo testa · 3.2 As tabelas e figuras · 3.3 O dia novo
  e o bloco · 3.4 O WAF · 3.5 A recomendação, passo a passo
- **Parte 4. Consulta:** 4.1 Os números para guardar · 4.2 Glossário · 4.3 Onde está cada coisa

---

# Parte 1. A história em 15 minutos

## 1.1 O trabalho em cinco frases

1. Um ataque DDoS lento e distribuído usa muitas máquinas, e cada uma manda tão pouco tráfego que
   nenhuma chama atenção sozinha.
2. Os detectores existentes, no máximo, avisam que há um ataque. Decidir **quem bloquear** sem
   bloquear os usuários de verdade fica em aberto, e é disso que o artigo trata.
3. O método bloqueia pelo fingerprint TLS (JA4) do software de cada visitante, e só os
   fingerprints que aparecem **muito mais que o normal** naquele serviço.
4. Um teste estatístico decide o que é "muito mais que o normal". Ele é **calibrado** em dias sem
   ataque para errar em no máximo 1% dos períodos de cinco minutos desses dias.
5. O artigo mede isso em tráfego gerado e em 23 dias de quatro serviços reais da Azion: o que o
   método barra, quanto custa aos usuários e onde ele deixa de funcionar.

## 1.2 A portaria de um prédio

Pense na portaria de um prédio comercial muito movimentado. O porteiro não conhece ninguém, mas
repara em duas coisas em cada pessoa que entra: **de onde ela vem**, o endereço de rede que o
artigo chama de *origem*, e **como ela se apresenta**, o *fingerprint*.

O fingerprint TLS funciona como um sotaque. Quando um navegador ou um programa abre uma conexão
segura (HTTPS), ele se apresenta de um jeito característico: as versões que aceita, as cifras que
oferece, a ordem delas. A JA4 resume essa apresentação numa sequência curta de letras e números.
O Chrome tem um sotaque, o Safari outro, e o software de uma câmera IP barata um terceiro.

- **Um dia normal.** Das pessoas que entram, 40% têm o sotaque "Chrome", 25% "Safari", 10%
  "Firefox", e o resto se divide entre muitos sotaques raros. O porteiro anota essa distribuição
  em dias tranquilos: é o **perfil** do prédio.
- **O ataque.** Chegam 300 pessoas a mais, cada uma de um endereço e todas educadas. Nenhuma chama
  atenção sozinha. Mas são aparelhos invadidos, câmeras e roteadores, e falam poucos sotaques
  raros.
- **A reação óbvia** é barrar o sotaque mais comum no saguão. É o "Chrome", e o porteiro barra os
  próprios clientes e nenhum invasor.
- **A reação do método** é comparar o saguão com um dia normal e barrar só os sotaques que ficaram
  muito mais frequentes do que costumam ser.
- **A exigência do porteiro.** Se ele for exigente demais, grupos pequenos de invasores passam: é
  o **piso**. Se for exigente de menos, ele barra uma excursão legítima: é um **falso alarme**. A
  exigência é ajustada em dias normais para errar em no máximo 1% dos períodos desses dias: é a
  **calibração**.
- **O alarme da portaria.** O porteiro só confere os sotaques quando o saguão está anormalmente
  cheio: é o **gate**. Num prédio enorme, 300 pessoas a mais quase não mudam a lotação. O alarme
  não toca e os invasores entram, mesmo que o porteiro soubesse reconhecê-los. Um achado central
  do artigo é este: **o gatilho decide**.

## 1.3 O mapa do método

A cada cinco minutos, para cada serviço, o sistema faz o percurso abaixo. É a Fig. 1 do artigo.

```
 log de acesso
      │   contagens por fingerprint (consulta gerada a partir da ontologia)
      ▼
 GATE: a janela está cheia demais?  ── não ──►  nada é aplicado
      │ sim
      ▼
 ESCOPO: quais fingerprints estão muito acima do perfil?
      │                                      │
 aponta algum                          não aponta nenhum
      ▼                                      ▼
 desafiar ou bloquear só esses         recurso: limite de taxa
 fingerprints e exportar a evidência   ou desafio a todos

 Tudo o que decide (perfil, limites, nível do teste) vem de dias sem ataque.
```

O gate decide **quando** agir, e o escopo decide **quem** barrar. Nenhum passo precisa saber de
antemão quem é atacante.

## 1.4 O que o trabalho mostrou

1. **A escolha óbvia é perigosa.** No tráfego gerado, barrar o fingerprint mais comum do alarme
   bloqueia 39% dos usuários e nenhum atacante quando a botnet usa cinco pilhas TLS ou mais.
   Comparar com o perfil bloqueia 90% de uma botnet com até 25 pilhas novas, sem dano observado.
2. **Em dados reais, a configuração calibrada erra pouco, mas cada erro pesa.** Nos dias de
   teste, os mesmos em que as escolhas do método foram feitas, ela deu falso alarme em 0,1% das
   janelas sem ataque (5 de 5.643). Em mediana, um falso alarme bloqueou um terço (32,9%) dos
   clientes da janela.
3. **Nos 14 dias seguintes, fixados de antemão, a taxa dobrou** para 0,19%, ainda dentro do
   orçamento de 1%. O gate abriu metade das vezes, mas, quando abria, o escopo errava mais: em 13%
   das aberturas, contra 3% antes. Em mediana, cada erro bloqueou 39% dos clientes da janela.
4. **Há um tamanho de botnet a partir do qual o escopo aponta uma pilha típica dela: o piso.**
   Uma botnet em fingerprints raros que clientes reais também usam só é apontada quando é grande:
   8% da janela no serviço mais movimentado e de 4 a 19 janelas inteiras nos pequenos. Uma botnet
   nos fingerprints mais comuns, em sua maior parte, passa.
5. **No serviço mais movimentado, o gate é o gargalo.** Nos dias de teste, o escopo
   sozinho barraria 90% de uma botnet de um décimo da janela em pilhas novas, mas o gate abre em
   poucas janelas, e a configuração detém 12%.
6. **Alternativas pensadas depois (*post hoc*) recuperam parte disso.** Nos 14 dias, o filtro de
   fingerprints inéditos usado como gatilho próprio deteve 90% dessa botnet em pilhas novas, sem
   nenhum falso alarme. A comparação fixada de antemão preferiu, em todos os serviços, a
   beta-binomial cruzada atrás de um gate sazonal. No serviço mais movimentado, ela só ganha nas
   pilhas compartilhadas e perde a maior parte das novas.
7. **Nenhum padrão de troca examinado sabe dizer "bloqueie este fingerprint".** STIX, DOTS e
   Flowspec não têm uma propriedade JA4 no vocabulário principal. A ontologia do artigo especifica
   esse filtro.

## 1.5 O que o artigo recomenda

- **Agora.** O candidato é a beta-binomial cruzada atrás do gate sazonal, com o recurso (um limite
  de taxa ou um desafio a todos) abaixo do piso dela. Ela foi construída depois de ver os dados,
  mas foi fixada antes do bloco de 14 dias, e lá a comparação fixada de antemão a preferiu ao
  filtro de inéditos em todos os serviços.
- **O preço dela.** Picos de 1.000 usuários legítimos a disparam em um terço das janelas, com
  filtros leves, e um falso alarme dela bloqueia, em mediana, dois terços dos clientes da janela.
  Quando o gate dela abre numa janela limpa e o escopo não aponta nada (1,5% das janelas), age o
  recurso, um custo que o orçamento de falsos alarmes não conta. No serviço mais movimentado, ela
  perde a maior parte da detecção de pilhas novas, que o filtro de inéditos como gatilho próprio
  mantém. Usar os dois juntos ali não foi testado.
- **Depois.** Uma avaliação mais longa, porque nenhum dia posterior ao bloco testou essa escolha.

## 1.6 Os limites

- Um único operador, quatro serviços e 23 dias, pouco para calibrar um ciclo semanal.
- A detecção em produção foi medida só com botnets injetadas, de um formato: 25 pilhas.
- Cinco escolhas do método foram feitas nos mesmos dias em que ele foi medido. Só o dia novo e o
  bloco de 14 dias as testam de forma prospectiva.
- O candidato atual é *post hoc* e passou por um único teste, o bloco de 14 dias.
- Um bot que usa um fingerprint comum, ou um diferente por aparelho, em sua maior parte escapa. É a
  fronteira declarada do método.
- A avaliação é offline, sobre contagens exportadas. Uma implantação ao vivo ainda precisa ser
  construída.
- Não foi medido se um ataque do tamanho do piso derrubaria o serviço.
- Não foram testados um pico legítimo concentrado num tipo de cliente nem um atacante que molde o
  perfil ou a lista de frotas conhecidas.
- O perfil precisa ficar atual. Uma versão nova de navegador que desse um fingerprint novo a muitos
  usuários dispararia o filtro de inéditos, algo que não aconteceu em 23 dias. Por isso os perfis
  devem ser refeitos com janelas em que o escopo não aponta nada, e um fingerprint novo persistente
  só deve entrar neles por decisão do operador.

## Teste-se: Parte 1

<details>
<summary>1. Por que barrar o fingerprint mais comum do alarme falha quando a botnet usa várias
pilhas?</summary>

Num serviço sob ataque, o fingerprint mais comum é o dos usuários legítimos. Quando a botnet se
espalha por várias pilhas, cada pilha dela fica menor que o fingerprint do navegador mais usado.
No tráfego gerado, a partir de cinco pilhas, essa escolha bloqueia 39% dos usuários e nenhum
atacante. Com uma pilha só, ela acerta tanto quanto o teste.

</details>

<details>
<summary>2. O que o gate decide, e o que o escopo decide?</summary>

O gate decide quando agir: ele abre quando a janela tem origens demais para o normal. O escopo
decide quem barrar: os fingerprints muito acima do perfil. Se o gate não abre, nada é aplicado,
mesmo que o escopo estivesse certo.

</details>

<details>
<summary>3. O que mudou nos 14 dias do bloco?</summary>

A taxa de falsos alarmes da configuração binomial dobrou, de 0,1% (5 de 5.643) para 0,19% (31 de
16.103), e continuou dentro do orçamento de 1%. O gate abriu metade das vezes, mas o escopo errou
em 13% das aberturas, contra 3% nos dias de teste.

</details>

---

# Parte 2. Como o método funciona

## 2.1 O que o sistema vê em cada janela

**A pergunta:** com que informação o método trabalha?

O defensor opera o serviço atacado. Para cada requisição, ele vê a apresentação TLS do cliente (o
*ClientHello*), o endereço de origem com o prefixo e a rede (ASN), o serviço de destino e a hora.
Do *ClientHello* ele calcula o fingerprint JA4, que resume a versão do TLS, as cifras, as extensões
e o protocolo de aplicação pedido (ALPN).

| Termo | O que é |
|---|---|
| Sessão | uma conexão de um cliente com o serviço |
| Origem | o endereço de rede (IP) de onde vem a sessão, contado uma vez por fingerprint que apresenta |
| Janela | um intervalo de cinco minutos (um dia tem 288) |
| Endpoint | o serviço protegido (o artigo usa quatro, E1 a E4) |
| Pilha TLS (*stack*) | o software que produz um fingerprint: um navegador, uma biblioteca |
| Botnet | os aparelhos invadidos que o atacante controla |

Os quatro endpoints da Azion, com o tamanho da janela mediana em origens:
- **E1**, os sinais de monitoramento de usuários reais (*RUM beacons*), que os navegadores mandam
  para medir as páginas: cerca de 3.000 origens. É o mais movimentado.
- **E2**, o console web, onde os clientes configuram os serviços: 62.
- **E3**, a API: 41.
- **E4**, o login único (*SSO*): 20.

**O modelo de ameaça.** O atacante controla K aparelhos e pode fazer cada sessão parecer legítima,
sem taxa alta nem conteúdo estranho. O dano vem da capacidade esgotada, porque cada sessão ocupa
uma conexão como uma legítima. O artigo assume que um bot mantém o fingerprint da sua pilha: um
roteador invadido fala TLS com a biblioteca do próprio firmware. Imitar um navegador exige um
navegador completo ou uma biblioteca de imitação atualizada a cada versão. Os bots que fazem isso
ficam fora do modelo, e o artigo os avalia como a fronteira do método.

**Guarde:** o método conta origens por fingerprint, por serviço e por janela. Ele não lê o
conteúdo das requisições.

## 2.2 O gatilho: quando agir

**A pergunta:** como o sistema sabe que é hora de agir?

O gatilho é uma condição de volume: ele abre quando a janela está mais cheia do que costuma ficar.
O artigo usa estes:
- **Origin gate**, o gate de origens distintas. Abre quando a janela tem pelo menos k_min = 5
  origens e o número de origens chega ao percentil 99 dos dias sem ataque. É o gatilho da
  avaliação em produção.
- **Ω gate**, o da regra básica (*base rule*), a referência do protocolo. A massa de coordenação Ω
  conta os pares de origens cujas sessões compartilham o JA4, o endpoint ou o prefixo /24, com
  pesos 1,0, 0,6 e 0,3. Na prática, Ω mede volume: na campanha padrão, 91% dele vem do termo de
  endpoint.
- **Seasonal gate**, o gate sazonal (*post hoc*). Divide as origens da janela pela mediana da mesma
  hora nos dias de calibração e abre no percentil 99 dessa razão. Ele pergunta se a janela está
  cheia para aquela hora do dia.
- **No gate**, sem gate (*post hoc*). Não há condição de volume: o escopo roda em toda janela, e
  apontar um fingerprint já é o alarme. As figuras chamam isso de *scope alone* ou *own trigger*.

**Guarde:** se o gate não abre, nada é aplicado. Num serviço grande, uma botnet pequena quase não
muda o volume, e o gate quase nunca abre: no E1, em 6% a 13% das janelas.

## 2.3 O escopo: quem barrar

**A pergunta:** dado o alarme, quais fingerprints bloquear?

**Por que a escolha óbvia falha.** Num serviço sob ataque, o fingerprint mais comum do alarme é o
dos usuários legítimos. Uma botnet espalhada por M pilhas divide entre elas 90% dos atacantes, e
cada pilha fica pequena. Com o fingerprint legítimo mais comum em 38,4% das requisições e uma botnet do
tamanho do tráfego legítimo, a moda só aponta o ataque com menos de 2,3 pilhas.

**O perfil.** É a distribuição dos fingerprints num período normal, que o operador guarda fora dos
ataques. Para cada fingerprint f, b(f) é a fatia dele no perfil, mais um termo pequeno para que um
fingerprint inédito não tenha fatia zero.

**O teste binomial de enriquecimento.** Para cada fingerprint, o teste pergunta: *isto pode ser
sorte?* Ele aponta f quando duas condições valem juntas:
1. **efeito:** f aparece pelo menos três vezes mais (ρ = 3) entre as origens do alarme do que no
   perfil;
2. **improbabilidade:** a chance de ver tantas origens com f por sorte é menor que o nível λ_e
   dividido pelo número de fingerprints testados. Essa divisão é a correção de Bonferroni: quanto
   mais fingerprints testados, mais exigente fica cada teste.

O resultado é um **conjunto** de fingerprints, e por isso ele cobre uma botnet espalhada por muitas
pilhas.

**As peças em volta do teste:**
- **Filtro de fingerprints inéditos (*unseen*).** Aponta os fingerprints ausentes do perfil vistos
  em pelo menos k_min = 5 origens, sem precisar de estatística do perfil. Junto com o teste, forma
  a **união**, que pega pilhas novas pequenas demais para o nível.
- **Frotas conhecidas.** São os fingerprints que o teste aponta no nível padrão (0,01) em pelo menos 5%
  das janelas de calibração, como robôs de monitoramento. No E1 e na API, elas ficam numa lista de exceções. A
  consequência: um bot que use o fingerprint de uma frota nunca é bloqueado.
- **z-score.** Uma regra mais simples, que mede quantos desvios a contagem de f está acima do
  esperado. Serve de comparação.

**Dois cuidados.** O perfil não pode conter o ataque: se a campanha estivesse nele, nenhum
fingerprint pareceria enriquecido. E atacantes escondidos num fingerprint popular não o
enriquecem, então o teste não o aponta. Isso é o certo quando nada distingue o ataque do tráfego
legítimo.

<details>
<summary><b>A conta</b>: as duas condições do teste</summary>

Sejam c(f) as origens do alarme com o fingerprint f, n o total de origens do alarme e |F| o número
de fingerprints do perfil e do alarme. O teste aponta f quando

- c(f)/n ≥ ρ · b(f), com ρ = 3, e
- P[X ≥ c(f)] < λ_e/|F|, com X ~ Bin(n, b(f)).

Exemplo hipotético: b(f) = 0,1%, n = 1.300 e c(f) = 101. Esperava-se 1,3 origem com f, e há 101,
quase 80 vezes mais. A chance de isso ser sorte é praticamente zero, e f entra no escopo.

</details>

**Guarde:** o escopo compara a janela com o normal do próprio serviço. Ele não precisa de nenhum
rótulo de ataque.

## 2.4 A calibração: o orçamento de 1%

**A pergunta:** quão exigente deve ser o teste?

**Por que calibrar.** A binomial supõe que cada origem é um sorteio independente. Em produção isso
falha, porque frotas de clientes legítimos ligam juntas, como uma frota de sondas ativa só no
horário comercial. No nível padrão de 0,01, o escopo produziria filtro em 26,9% das janelas limpas
contando origens, e em 60,1% contando conexões.

**Como se calibra.** Para cada endpoint e, o nível λ_e é o maior valor até 0,01 com que o escopo
produz filtro em no máximo 1% das janelas de calibração. Esse 1% é o **orçamento**: cerca de 2,9
das 288 janelas de um dia. Os níveis ficam muito pequenos: 10⁻²¹ no E1 com as frotas conhecidas
isentas (10⁻⁶⁰ sem elas), 10⁻⁷³ no E2, 10⁻¹¹ no E3 e 10⁻⁴ no E4. Num nível como 10⁻⁶⁰, a cauda
binomial deixa de ser uma probabilidade e vira um escore, cujo limiar o orçamento fixa. O z-score
calibrado segue o mesmo orçamento: o limiar é o percentil 99 do maior z de cada janela de
calibração, nunca abaixo de 3.

**Em amostra e calibração cruzada.** Na calibração **em amostra**, cada dia de calibração é julgado
contra um perfil que o inclui, e o nível pode ficar ajustado aos próprios dias. Na **calibração
cruzada** (*cross-fitting*, *post hoc*), cada dia de calibração é julgado, como um dia de teste,
contra o perfil dos outros dias. A diferença entre as duas mostra quanto do resultado em amostra
era otimismo.

**O que o 1% garante.** Nas janelas de calibração, o orçamento vale por construção. Nos dias
seguintes, ele precisa ser medido. Somando os quatro endpoints, nos dias de teste, cada peça sozinha passou do
orçamento: o escopo deu 2,2%, e o gate, 3,0% (5,4% no E1). Juntos deram 0,1%, porque raramente erravam na mesma
janela.

**Guarde:** a calibração escolhe o teste mais tolerante que ainda erra em no máximo 1% das janelas
dos dias de calibração. Fora desses dias, o erro precisa ser medido.

## 2.5 O piso de calibração: a partir de que tamanho o escopo enxerga

**A pergunta:** a partir de que tamanho uma botnet é apontada?

**A intuição.** Um nível exigente cala as frotas, mas também exige que a botnet seja grande para
parecer improvável. O tamanho a partir do qual o escopo aponta uma pilha típica da botnet é o
**piso de calibração**. Ele serve para planejar: acima do piso, o escopo pode ser um filtro de
fingerprints. Abaixo dele, o recurso é um limite de taxa ou um desafio a todos.

**Os três casos:**
- **Pilhas novas**, ausentes do tráfego legítimo. O filtro de inéditos fixa o piso: ele aponta uma
  pilha assim que ela tem 5 origens, e com 25 pilhas isso exige 139 atacantes, qualquer que seja o
  nível. No E4, o teste aponta antes, a partir de 84.
- **Pilhas compartilhadas**, raras, mas usadas também por clientes reais. Aqui o nível decide: uma
  pilha típica só é apontada a partir de 254 atacantes no E1, 8% da janela, e de 4 a 19 janelas
  inteiras nos serviços pequenos.
- **Pilhas comuns.** Vale o **limite de enriquecimento**. Por maior que seja a botnet, cada uma das suas 25
  pilhas fica com menos de 0,9/25 = 3,6% da janela. Para ser três vezes mais frequente que o
  normal, o fingerprint precisaria ter menos de 1,2% do perfil. Os 4 a 28 fingerprints mais comuns
  de cada serviço, que somam de 86% a 94% das origens, ficam fora de alcance.

**O piso não é um degrau.** Abaixo dele, o escopo ainda aponta as pilhas que o acaso deixou
maiores, e por isso a detecção sobe aos poucos com o tamanho da botnet. Para 100 atacantes em
pilhas novas no E1, um modelo binomial do tamanho das pilhas prevê que o escopo sozinho, em toda
janela, barre 43,1% da botnet, e as botnets injetadas dão 43,2%.

<details>
<summary><b>A conta</b>: o piso e o limite de enriquecimento</summary>

Uma botnet de A atacantes em M pilhas põe cerca de 0,9 · A/M atacantes em cada pilha, numa janela
de n₀ + A origens (n₀ é a janela mediana). O piso é o menor A em que essa pilha média passa nas
duas condições do teste.

- Pilha nova, pelo filtro de inéditos: ⌈k_min · M/0,9⌉ = ⌈5 × 25/0,9⌉ = 139.
- Limite de enriquecimento: a fatia esperada de uma pilha é menor que 0,9/M, então o efeito falha para todo
  fingerprint com b > 0,9/(ρ · M) = 0,9/(3 × 25) = 1,2%.

Exemplo hipotético de como o nível empurra o piso, só com o teste, num endpoint de 2.000 origens
por janela e uma botnet em 25 pilhas novas:

| Nível λ_e | Origens por pilha | Menor botnet | Fração da janela |
|---|---|---|---|
| 10⁻² | 3 | 84 | 4% |
| 10⁻²¹ | 10 | 278 | 14% |
| 10⁻⁶⁰ | 22 | 612 | 31% |

A conta da primeira linha: 3 origens por pilha pedem 0,9 · A/25 ≥ 3, ou seja,
A ≥ ⌈3 × 25/0,9⌉ = 84. Os números exatos dependem do perfil: com os perfis reais do artigo, o nível de
10⁻⁶⁰ só aponta uma pilha a partir de 15 a 18 origens.

</details>

**Guarde:** a calibração tem um preço, o piso. Nos serviços pequenos, uma botnet em pilhas
compartilhadas só é apontada quando é maior que todo o tráfego normal de uma janela.

## 2.6 As variantes que o artigo compara

**A pergunta:** o que muda entre as configurações das tabelas?

Uma configuração é um gatilho mais um escopo. As tabelas combinam estas peças:

| Peça | O que faz | Para quê | Status |
|---|---|---|---|
| Frotas conhecidas | isenta os fingerprints de frotas | sobe o nível do E1 de 10⁻⁶⁰ para cerca de 10⁻²¹ e baixa o piso | escolhida nos dias de teste |
| Beta-binomial | aceita que as origens cheguem em grupos | a calibração não precisa empurrar o nível tão para baixo | *post hoc* |
| Calibração cruzada | julga cada dia de calibração contra os outros | mede quanto do resultado era otimismo | *post hoc* |
| z-score calibrado | outra regra relativa ao perfil | termo de comparação | no código antes do dia novo, fora do protocolo dele |
| Gate sazonal | compara a janela com a mesma hora | um gate mais sensível no E1 | *post hoc* |
| Sem gate | o escopo é o próprio gatilho | pega botnets que o gate deixa passar | *post hoc* |

**A beta-binomial, em uma ideia.** Uma frota põe várias origens na mesma janela de uma vez, e a
contagem de um fingerprint varia de janela para janela mais do que a binomial permite. A
beta-binomial acrescenta uma correlação φ dentro da janela, estimada nos dias de calibração para
cada fingerprint do perfil. Com ela, uma frota que põe 8 origens numa janela deixa de ser um evento
quase impossível. Um fingerprint ausente do perfil continua binomial.

<details>
<summary><b>A conta</b>: binomial e beta-binomial</summary>

As duas têm a mesma média, n · b. A variância da beta-binomial é n · b · (1 − b) · (1 + (n − 1) · φ).
Com φ = 0, ela volta a ser a binomial.

Exemplo hipotético: n = 100, b = 0,01 e φ = 0,05. A variância vai de 0,99 para 5,89, e as caudas
ficam assim:

| Contagem | Chance de sorte, binomial | Chance de sorte, beta-binomial |
|---|---|---|
| 5 | 3,4 × 10⁻³ | 0,069 |
| 8 | 8,2 × 10⁻⁶ | 0,030 |

</details>

**Guarde:** a configuração principal do protocolo é a binomial com frotas conhecidas, atrás do
origin gate. As outras são referências (a regra básica e o z-score) ou alternativas construídas
depois (*post hoc*).

## 2.7 A ontologia: a especificação

**A pergunta:** para que serve a ontologia, se ela não detecta nada?

A ontologia OWL é um dicionário formal do domínio. A classe central, `ApplicationSession`, liga uma
sessão à sua identidade (`Identity`), ao endereço de origem (`IPAddress`) e ao endpoint
(`Endpoint`). Um ataque (`Attack`) se liga à sua mitigação (`Mitigation`), cujo escopo a cadeia de
evidência carrega. Subpropriedades de `relatedTo` dizem o que liga duas sessões. As três usadas
aqui são igualdades: o mesmo JA4, o mesmo endpoint, o mesmo /24.

Ela cumpre três papéis:
1. **Especifica as contagens.** A consulta SQL que roda no banco de logs é compilada a partir das
   anotações da ontologia. Um sinal novo de igualdade entra com quatro triplas e o mapeamento de
   uma coluna, sem mudar código. Nos dados da Azion, a consulta compilada reproduziu as contagens
   de endereços e de pares /24 de dois dias inteiros, e as de pares JA4 no endpoint em que o WAF não
   bloqueou ninguém. Contagens de pares limitam, mas não identificam, as contagens por fingerprint
   que o escopo testa.
2. **Especifica o que se exporta.** Quando a regra dispara, a cadeia de evidência (a regra, o
   grupo, o escopo e a divisão de Ω por tipo de ligação) sai em JSON-LD e em STIX 2.1.
3. **Especifica o que os padrões examinados não expressam.** STIX 2.1, DOTS e Flowspec não têm uma
   propriedade JA4 no vocabulário principal. O OCSF registra JA4, mas não define filtro sobre ele,
   e o importador do MISP descarta os fingerprints. Para trocar esse filtro, o DOTS precisaria de
   um campo JA4 nos filtros, e o STIX, de uma propriedade JA4.

A ontologia não melhora a detecção nem o gatilho, e nenhum raciocinador roda na avaliação.

**Por que o título não fala mais em *knowledge graph*.** O projeto começou com a ideia de que um
grafo de conhecimento detectaria ataques melhor. Os testes mostraram que a vantagem vinha de contar
quantas origens compartilham um fingerprint, e uma contagem simples faz essa conta. E a pergunta
em aberto era outra: quem bloquear, e a que custo. O artigo não encontrou método publicado que
escolha o filtro pelo fingerprint e meça o custo de cada filtro. O grafo ficou como a especificação do que o
operador implanta.

**Guarde:** a ontologia especifica o filtro e as contagens. Quem decide são o gatilho e o teste.

## 2.8 Um exemplo completo (hipotético)

Uma janela normal de um serviço tem **1.000 visitantes legítimos**: 400 com o fingerprint A, de um
navegador comum (40%), 250 com B, 100 com C, e 250 espalhados por fingerprints raros. Entre os
raros estão X, Y e Z, com 1 visitante cada (0,1%).

Chega uma botnet de **300 aparelhos**, com 100 em cada um de X, Y e Z. A janela passa a ter 1.300
visitantes.

1. **O gate.** Suponha que 1.300 origens passem do percentil 99 dos dias normais. O gate abre.
2. **A escolha óbvia falha.** O fingerprint mais comum continua sendo A, com 400. Barrar A bloqueia
   40% dos usuários e nenhum aparelho da botnet. No tráfego gerado do artigo, esse número é 39%.
3. **O teste acerta.** Para A, esperava-se 40% de 1.300, ou 520, e há 400: A está abaixo do normal
   e fica fora. Para X, esperava-se 1,3, e há 101: X entra, e Y e Z também. O bloqueio atinge os
   300 aparelhos e 3 usuários legítimos, um de cada fingerprint: dano colateral de 0,3%.
4. **O piso.** Se a botnet tivesse só 5 aparelhos por fingerprint, X teria 6 visitantes em vez de
   1. É seis vezes o normal, mas a chance de sorte é de cerca de 6 em 10.000. Com o nível de 0,01
   dividido por 100 fingerprints testados, o limite é de 1 em 10.000, e X não entra. A botnet fica
   abaixo do piso.
5. **O limite de enriquecimento.** Se os 300 aparelhos usassem o fingerprint A, ele precisaria chegar a 120%
   da janela para ficar três vezes acima do normal, o que é impossível. Um bot no fingerprint
   mais comum nunca é apontado, qualquer que seja o tamanho da botnet.
6. **O gate num serviço grande.** No E1, a janela normal tem cerca de 3.000 origens. Uma botnet de
   300 acrescenta 10%, e o gate abre em só 6% a 13% das janelas para botnets desse porte. Quando
   ele não abre, ninguém confere os fingerprints, e a botnet passa.

## Teste-se: Parte 2

<details>
<summary>1. Por que o nível do E1 é tão exigente (10⁻²¹), e qual é o preço disso?</summary>

Frotas de clientes legítimos ligam juntas e, para a binomial, parecem improváveis. Para errar em
no máximo 1% das janelas de calibração, o nível precisa ser muito exigente: 10⁻⁶⁰ sem isentar as
frotas conhecidas, cerca de 10⁻²¹ com elas. O preço é o piso: uma botnet em pilhas compartilhadas
só é apontada a partir de 254 atacantes, 8% da janela.

</details>

<details>
<summary>2. Uma botnet usa 25 pilhas novas. A partir de quantos atacantes por janela ela é
apontada, e por quem?</summary>

A partir de 139, pelo filtro de inéditos: 5 origens por pilha, vezes 25 pilhas, divididas pelos
90% da botnet que estão nelas. Isso vale qualquer que seja o nível. No E4, o teste aponta antes, a
partir de 84.

</details>

<details>
<summary>3. Uma botnet inteira imita o Chrome, o fingerprint mais comum. Por que nenhum tamanho de
botnet a torna visível?</summary>

Pelo limite de enriquecimento. Para o teste apontar o fingerprint do Chrome, ele precisaria ficar três
vezes acima da sua fatia normal. Com cerca de 38% do perfil, a fatia do fingerprint mais comum na
medição do artigo, isso passaria de 100% da janela, o que é impossível. Com a botnet espalhada em
25 pilhas, o mesmo vale para todo fingerprint com mais de 1,2% do perfil.

</details>

<details>
<summary>4. O que a ontologia acrescenta à detecção?</summary>

Nada. Ela especifica as contagens que a consulta lê e o escopo que se exporta. A detecção e o
gatilho não dependem dela.

</details>

---

# Parte 3. As evidências

## 3.1 Como o artigo testa

**A pergunta:** com que dados e com que cuidados o método foi avaliado?

**Três fontes de tráfego, três perguntas.**

| Fonte | O que responde | Onde |
|---|---|---|
| Gerador calibrado | o mecanismo funciona quando se sabe quem é atacante? | Seção V-A, Tabela III |
| Capturas de laboratório (CICIDS2017, CIC-IoT2023) | e em ataques convencionais? E diante do número publicado do KLAGE, numa comparação sem controle? | Apêndice C |
| Tráfego da Azion, 23 dias | quantos falsos alarmes em clientes reais, e o que se detém de botnets injetadas? | Seções V-B a V-D |

**O gerador.** Produz campanhas de Slow HTTP DoS com a verdade conhecida. Os fingerprints
legítimos seguem uma curva de Zipf, conferida contra 6,33 milhões de requisições TLS medidas num
ponto de presença da Azion: 495 fingerprints, o mais comum com 38,4% das requisições e os dez mais
comuns com 93,8%. No modo furtivo, cada sessão de ataque é sorteada das mesmas distribuições das
legítimas, e o ataque só aparece na estrutura entre sessões. Por isso a detecção sessão por sessão
fica no acaso, com AUC de 0,50 (Apêndice C).

**As botnets injetadas em produção.** Em cada janela dos dias de teste, o artigo injeta uma botnet
construída como no gerador: de 25 a 1.000 atacantes, ou de um décimo da janela mediana (0,1×) a
uma janela inteira (1×). Ela põe 90% dos atacantes em 25 pilhas e o resto em fingerprints avulsos,
que nenhum escopo aponta. Por isso nenhum escopo passa de cerca de 90%. As pilhas são novas
(*new*), compartilhadas (*shared*, tiradas do perfil depois dos dez fingerprints mais comuns) ou os
25 fingerprints mais comuns do serviço (*adversarial*). Um pico legítimo (*flash crowd*) acrescenta
100 ou 1.000 usuários do próprio dia a uma janela.

**Atrás do WAF.** O escopo foi avaliado atrás do WAF da Azion. Os perfis e os pisos descrevem,
portanto, os clientes que o WAF deixa passar.

**A linha do tempo dos 23 dias.**

```
 17 a 24/09     8 dias    os 3 primeiros só calibram. Cada um dos 5 seguintes é testado
                          com o que veio antes. As escolhas do método foram feitas aqui.
 25/09          1 dia     o dia novo (held-out), analisado com o protocolo fixado antes.
 26/09 a 09/10  14 dias   o bloco: protocolo público antes da exportação, análise só depois
                          de publicados os hashes dos arquivos. Cada dia é calibrado com
                          todos os anteriores.
```

**Fixado antes e *post hoc*.** Uma análise fixada antes declara o que vai medir e como vai decidir
antes de ver os dados. Uma análise *post hoc* foi pensada depois de ver os dados, e por isso pode
estar ajustada a eles. No artigo, o `*` marca o que foi construído depois de ler o dia novo. O
bloco de 14 dias é o teste fixado antes para essas ideias. O Apêndice F declara três ressalvas:
- o protocolo do dia novo entrou no Git 17 horas depois da hora declarada, sem carimbo externo;
- no bloco, uma regra foi emendada depois da exportação, antes de qualquer resultado e sem mudar o
  veredito;
- algumas linhas de contagens brutas apareceram na tela durante a exportação.

**As métricas de produção.** As janelas dos dias de teste antes da injeção são as **janelas
limpas**, tomadas como sem ataque: um ataque real ali contaria como falso alarme. Janelas com menos
de 5 origens ficam de fora.
- **FA, a taxa de falso alarme:** a fração das janelas limpas em que a configuração produz um
  filtro. O intervalo exato de 95% supõe janelas independentes. Como os falsos alarmes se
  concentram em certos dias, a incerteza real é maior.
- **Coll., o dano colateral:** quando há um falso alarme, a fração dos clientes da janela que o
  filtro bloqueia, em mediana sobre os alarmes: metade dos alarmes bloqueia mais que isso, metade
  menos.
- **O dano esperado:** a taxa vezes o dano médio, ou seja, a fração de clientes bloqueados por
  janela limpa.
- **Fl. 1k:** a fração das janelas em que um pico de 1.000 usuários reais dispara a configuração.
- **A fração bloqueada da botnet:** a média sobre todas as janelas de ataque, inclusive aquelas em
  que o gate não abre. É o produto de três coisas: o gate abrir, o escopo apontar a botnet e o
  filtro cobrir os atacantes.

## 3.2 As tabelas e figuras, uma por uma

Cada item traz a pergunta, como ler, o que tirar e o cuidado. A ordem é a do artigo.

**Quatro convenções**
- **Escala logarítmica** (Figs. 2, 3 e 4): cada marca do eixo vale dez vezes a anterior, e subir
  uma marca é multiplicar por 10. No eixo vertical da Fig. 4, as marcas vão de duas em duas
  potências: de 10⁻⁶ para 10⁻⁴ é multiplicar por 100.
- **Números como 10⁻²¹:** um limiar muito exigente, com a vírgula 21 casas à esquerda. Com as
  frotas, a cauda binomial deixa de ser a chance real dos dados e funciona como um escore. Na Tabela
  V, quanto menor o nível, mais exigente o teste e mais alto o piso.
- **"254/286":** duas medidas da mesma coisa. A primeira é em amostra, e a segunda, com calibração
  cruzada.
- **`*` e `†`:** `*` é *post hoc*, e `†` é calibração cruzada. Um resultado com `*` é uma pista que
  precisa de um teste fixado antes.

### Fig. 1. O método

- **Pergunta:** como o sistema decide quem barrar, a cada cinco minutos?
- **Como ler:** da esquerda para a direita. O log de acesso alimenta a consulta de contagem (*count
  query*), compilada da ontologia, a caixa de baixo. Ela devolve os tamanhos das classes (*class
  sizes*): quantas origens têm cada fingerprint, c(f), o total n e os pares no mesmo /24. O
  gatilho (*trigger*) abre no percentil 99 das origens, com pelo menos k_min. O escopo (*scope*)
  lista os fingerprints enriquecidos e os inéditos, sem as frotas conhecidas. Se a lista tem algo,
  o sistema desafia ou bloqueia e exporta a evidência em STIX 2.1. Se ela sai vazia, o recurso é um
  limite de taxa ou um desafio a todos. A caixa larga de baixo (*calibration on attack-free days*)
  fornece todos os limites.
- **O que tirar:** o método conta e compara com o normal do próprio serviço. Nenhum passo usa um
  rótulo de ataque.
- **Cuidado:** se o gatilho não abre, nada é aplicado (*otherwise: no action*).

### Tabela I. O que já existe

- **Pergunta:** o que as outras soluções filtram, quem escolhe o filtro e quanto ele custa aos
  usuários?
- **Como ler:** uma linha por família de soluções. As colunas dizem o que o filtro compara
  (*Filter matches*), o que o escolhe (*Chosen by*) e quem paga por ele (*Cost to legitimate
  users*).
- **O que tirar:** só a última linha filtra pelo fingerprint TLS **e** mede o custo, por alarme e
  por janela. Uma plataforma de *bot management* filtra por JA4, mas a descrição publicada não diz
  como escolhe o filtro nem quanto ele custa (*Undisclosed*).
- **Cuidado:** é sobretudo uma comparação de desenho. Só dois detectores da linha *Detectors*
  (Bharathi e Kemp) foram reimplementados e rodados no tráfego gerado (Apêndice C), e o KLAGE foi
  comparado, sem controle, com o número que publicou.

### Tabela II. As configurações avaliadas em produção

- **Pergunta:** o que exatamente foi testado nos dados reais?
- **Como ler:** cada linha é uma configuração. As colunas dão o gate (*Gate*), a regra do escopo
  (*Scope*), o modelo do normal (*Background*), o que fica isento (*Exempt*), onde as escolhas
  foram feitas (*Chosen*) e o status no dia novo (*Held-out day*).
- **O que tirar:** a *Binomial* (origin gate, teste ∪ inéditos, frotas isentas) é a configuração
  principal do protocolo. A *Base rule* e o *z-score* são referências, e a *Beta-binomial* é
  *post hoc*.
- **Cuidado:** *outside* (nota *a*) quer dizer que o z-score já estava no código antes do dia
  novo, mas fora do que o protocolo prometia avaliar.

### Tabela III. O escopo no tráfego gerado

- **Pergunta:** quem acerta a botnet quando ela usa 1, 5, 25 ou 100 pilhas?
- **Como ler:** cada linha é um cenário, e M é o número de pilhas. *Shared*: pilhas que clientes
  reais também usam. *Adversarial*: a botnet usa os fingerprints mais comuns. Para o teste binomial
  há *Recall* (quanto da botnet é barrado), FPR (quanto do tráfego legítimo é barrado) e F1. As
  outras colunas dão o *Recall* da moda (*Modal*), do z-score, dos inéditos (*Unseen*) e de dois
  modelos aprendidos, travados em zero falso positivo.
- **O que tirar:** com M = 25, o teste barra 90,3% da botnet e 0,00% dos legítimos, e a moda barra
  0,0%. A partir de cinco pilhas, a moda falha.
- **Cuidado:** o tráfego gerado é mais fácil que a produção, porque as campanhas ocupam de um terço
  à metade da janela. E as pilhas novas nunca aparecem no tráfego legítimo, por isso o filtro de
  inéditos empata com o teste ou o supera ali. A linha *adversarial* (30,4%) mostra a fronteira. E nenhum escopo passa de
  cerca de 90%, porque 10% dos atacantes usam fingerprints avulsos.

### Tabela IV. A produção nos dias de teste

- **Pergunta:** nos dados reais, quantos falsos alarmes, quanto eles custam e quanto de uma botnet
  injetada é barrado?
- **Como ler:** dois blocos, os dias de teste em amostra e os mesmos dias com calibração cruzada
  (`*`), com todos os endpoints juntos. Nas janelas limpas (*Clean windows*): FA, a taxa sem gate
  (*No gate*), o dano por alarme (*Coll.*) e os picos de 1.000 (*Fl. 1k*). Em *New* e *Shared*:
  quanto de uma botnet de 0,1× ou 1× janela é barrado, sobre todas as janelas de ataque.
- **O que tirar:** a binomial dá FA de 0,1% (5 de 5.643), mas um alarme barra, em mediana,
  32,9% dos clientes da janela. Picos de 1.000 a disparam em 22,2% das janelas. De uma botnet de um
  décimo da janela em pilhas novas, só 3,0% é barrado. Esse número soma os quatro serviços: no E1
  são 11,8%, e nos pequenos um décimo da janela são só de 2 a 6 atacantes, espalhados em 25 pilhas, e
  quase nada é barrado.
- **Cuidado:** com 5 eventos, a incerteza é grande, e o intervalo de 95% vai de 0,03% a 0,21%.
  Sozinho, o escopo daria 2,2% (*No gate*), acima do orçamento.

### Tabela V. O piso por endpoint

- **Pergunta:** a partir de que tamanho a botnet é apontada, em cada serviço?
- **Como ler:** n₀ é a janela mediana, e λ_e, o nível calibrado. As colunas de piso dão atacantes
  por janela, em amostra e cruzado, para pilhas novas (*new*) e compartilhadas (*shared*), na
  binomial e na beta-binomial (`*`).
- **O que tirar:** no E1, com 2.983 origens, o piso em pilhas compartilhadas é de 254 atacantes,
  8% da janela. No E2, com 62 origens, são 1.090, mais de 17 vezes o tráfego normal. O 139 das
  pilhas novas vem do filtro de inéditos e não depende do nível.
- **Cuidado:** o piso não é um degrau. Abaixo dele, o escopo ainda aponta parte das pilhas.

### Fig. 2. O que a configuração barra, pelo tamanho da botnet

- **Pergunta:** o escopo reconhece uma botnet pequena. Por que ela não é barrada?
- **Como ler:** um painel por endpoint. No eixo horizontal, os atacantes por janela, em escala
  logarítmica. No vertical, a porcentagem barrada. A linha tracejada é o que o escopo barraria
  sozinho, em toda janela. A cheia é o que a configuração barra de fato. A área cinza entre elas é
  o que o gate deixa passar. O triângulo marca um décimo da janela.
- **O que tirar:** no E1, no triângulo, com cerca de 300 atacantes, a tracejada está em 90% e a
  cheia em 12%. São 300 a mais num saguão de 3.000, o que quase não muda a lotação. Nos serviços
  pequenos, 100 atacantes já valem várias janelas, o gate abre, e o limite passa a ser o piso.
- **Cuidado:** é uma botnet injetada de um formato só, em 25 pilhas novas. As pilhas compartilhadas
  ficaram fora da figura.

### Tabela VI. Os escopos atrás de cada gatilho

- **Pergunta:** trocar o gatilho recupera a botnet pequena do E1 sem encher o dia de falsos
  alarmes?
- **Como ler:** três blocos de gatilho: *Origin gate*, o do protocolo, *Seasonal gate* (`*`) e *No
  gate* (`*`), o escopo como gatilho próprio. Em cada um, três escopos: binomial, beta-binomial
  cruzada (`†`) e inéditos. As colunas dão os falsos alarmes no E1 e o maior valor do E2 ao E4, nos
  dias de teste (*test*) e no dia novo (*held*), e quanto da botnet de um décimo do E1 é barrado,
  em pilhas novas e compartilhadas.
- **O que tirar:** *No gate / unseen* fica em 0,28% de falsos alarmes no E1 e no máximo 0,42% nos
  pequenos, e barra 89,6% da botnet em pilhas novas e 0,0% nas compartilhadas. A beta-binomial
  cruzada atrás do gate sazonal chega a 15,1% nas compartilhadas.
- **Cuidado:** tudo o que tem `*` foi examinado depois do dia novo. A Tabela VII mostra o que o
  bloco de 14 dias, fixado antes, encontrou para essas ideias.

### Fig. 3. O equilíbrio de cada configuração

- **Pergunta:** qual configuração faz o melhor acordo entre falsos alarmes e detecção?
- **Como ler:** dois painéis, pilhas novas e compartilhadas. No eixo horizontal, os falsos alarmes
  (% das janelas limpas, escala logarítmica). No vertical, a porcentagem barrada de 100 atacantes.
  O melhor canto é em cima à esquerda, e a linha tracejada vertical é o orçamento de 1%. Três
  regras leem a figura inteira. A forma é o escopo: círculo, a regra básica; losango, a binomial;
  quadrado, a beta-binomial; triângulo para cima, o z-score; triângulo para baixo, o filtro de
  inéditos. Preto é atrás de um gate, e branco é o escopo sozinho, sem gate (*the scope alone*).
  Cinza é a calibração cruzada, com uma seta saindo do ponto em amostra.
- **O que tirar:** a binomial (o losango preto) fica perto de 0,1% de falsos alarmes e 38% em
  pilhas novas. A beta-binomial sozinha (o quadrado branco) chega a 86%, com 4,4% de falsos
  alarmes. Com a calibração cruzada, ela vai para 1,1% e 66%, ainda um pouco acima do orçamento.
- **Cuidado:** os 100 atacantes estão somados sobre os quatro serviços, e os pequenos pesam mais. O
  dia novo ficou fora da figura.

### Tabela VII. As seis configurações no bloco de 14 dias

- **Pergunta:** o que acontece com as configurações em dias que ninguém tinha visto, com tudo
  fixado antes?
- **Como ler:** 16.103 janelas limpas, com cada dia calibrado nos dias anteriores. FA em todos os
  serviços (*all*), no E1 e o maior valor do E2 ao E4. *E1, 0.1×*: quanto da botnet de um décimo
  do E1 é barrado. *100 attackers*: 100 atacantes, somados sobre os serviços. *Fl. 1k* e *Coll.*,
  como antes. A última linha (`a`) só vale para o E1.
- **O que tirar:**
  - a binomial do protocolo dá 0,19%, o dobro dos dias de teste, ainda dentro do orçamento;
  - o filtro de inéditos como gatilho próprio não deu nenhum falso alarme e barrou 89,6% da botnet
    do E1 em pilhas novas;
  - a beta-binomial cruzada atrás do gate sazonal dá 0,12% no total (0,35% no E1) e barra 61,0% de
    100 atacantes em pilhas novas e 39,7% em compartilhadas, somando os serviços, mais que qualquer
    outra;
  - a binomial sem gate, no E1, passa do orçamento (1,56%).
- **Cuidado:** a coluna *Coll.* é a mediana sobre os falsos alarmes: os 65,7% da beta-binomial
  querem dizer que, em mediana, um erro dela bloqueia dois terços dos clientes da janela. E a
  escolha da melhor configuração foi feita nesses mesmos dias, sem um dia posterior que a teste.

### Fig. 4 (Apêndice D). O custo de processamento

- **Pergunta:** o método aguenta rodar em tempo real numa CDN?
- **Como ler:** as sessões ativas na janela, de 100 a 100.000, contra o tempo, os dois em escala
  logarítmica. Há quatro linhas: a admissão, feita a cada requisição, e a agregação, feita uma vez
  por janela, cada uma guardando pares de sessões (cinza) ou só contando classes (preto). As
  pontilhadas são inclinações de referência.
- **O que tirar:** guardando pares, a agregação leva 52,8 s com 1.000 sessões. Contando classes,
  leva 0,33 s. A admissão por contagem fica entre 0,33 e 0,42 milionésimo de segundo até 100.000
  sessões.
- **Cuidado:** a medição usa uma biblioteca em Python (rdflib), então os tempos são provavelmente um teto.

### Listagem 1 (Apêndice D). A cadeia de evidência

- **Pergunta:** o que o sistema entrega ao operador quando dispara?
- **Como ler:** um registro JSON-LD com a regra que disparou (*CoordinatedHTTPFlood*), o tamanho
  do grupo (1.991 origens), a massa Ω (1.303.422,8), a divisão de Ω por tipo de ligação (o mesmo
  fingerprint com peso 1,0, o mesmo serviço com 0,6, o mesmo /24 com 0,3) e o escopo: o serviço e
  os 25 fingerprints.
- **O que tirar:** os 1.981.045 pares ligados pelo mesmo serviço, vezes 0,6, dão 91% de Ω. É por
  isso que Ω mede sobretudo volume.

## 3.3 O dia novo e o bloco: o teste prospectivo

**A pergunta:** o que as configurações fazem em dias que não foram usados para escolhê-las?

**O dia novo.** A configuração binomial deu 2 falsos alarmes em 1.152 janelas limpas, compatível
com os dias de teste (P = 0,27). Mas o gate abriu em só 3 dessas janelas, e o escopo errou em 2,
ambas no console. É mais do que os 5 erros em 168 aberturas dos dias de teste preveem (*post hoc*,
P = 0,003). A contagem total parecia boa porque o gate ficou quieto.

**O bloco de 14 dias.** O protocolo foi publicado antes da exportação, e a análise só rodou depois
de publicados os hashes dos arquivos. A configuração errou em 31 de 16.103 janelas limpas (0,19%,
com intervalo de 95% de 0,13% a 0,27%). É o dobro da taxa dos dias de teste e, pelo teste do
protocolo, incompatível com ela (P < 10⁻⁴), embora dentro do orçamento.

**Por que dobrou: uma multiplicação.** A taxa de falsos alarmes é a taxa de abertura do gate vezes
a taxa de erro do escopo quando o gate abre.

| | O gate abre | O escopo erra, quando abre | Falsos alarmes |
|---|---|---|---|
| Dias de teste | 2,98% (168 de 5.643) | 2,98% (5 de 168) | 0,089% |
| Bloco | 1,45% (233 de 16.103) | 13,3% (31 de 233) | 0,19% |

Na analogia, o alarme tocou metade das vezes, mas, quando tocou, o porteiro errou 4,5 vezes
mais. A parte firme do resultado é essa queda do escopo. Contando a incerteza dos próprios dias de
teste (um teste de Fisher, *post hoc*, Apêndice E), a alta da taxa total tem P = 0,07, e a alta
dos erros com o gate aberto, P = 0,0002.

**Onde os erros caíram.** Em 30 dos 31 casos, num dia útil. Todos nos serviços pequenos: 17 nas 29
aberturas do console, 10 nas 98 da API e 4 nas 95 do login único. Nenhum no E1. Em mediana, um erro
bloqueou 39% dos clientes da janela.

**A comparação fixada antes.** O protocolo do bloco comparou, por uma regra escrita antes, o filtro
de inéditos como gatilho próprio e a beta-binomial cruzada atrás do gate sazonal. A beta-binomial
ficou dentro do orçamento em todos os serviços (0,05% a 0,35%) e foi a preferida em todos eles:
- nos serviços pequenos, deteve de 68% a 88% de 100 atacantes em pilhas novas, contra 43% do
  filtro, e de 34% a 66% em pilhas compartilhadas, que o filtro não pega;
- no E1, ela só é preferida pelas pilhas compartilhadas: acrescenta 11,4% da botnet de um décimo,
  mas detém só 11,8% em pilhas novas, contra 89,6% do filtro.

O filtro de inéditos não deu nenhum falso alarme. A binomial sem gate, no E1, passou do orçamento
(1,56%).

**Guarde:** no bloco, a configuração principal ficou dentro do orçamento (0,19%), e duas das três
configurações *post hoc* também. A binomial sem gate passou do orçamento no E1 (1,56%). O que piorou
na configuração principal foi o escopo, que errou mais vezes quando o gate abria.

## 3.4 Por que o WAF da Azion não serve de gabarito

O WAF bloqueou uma mediana de 9% a 63% dos clientes de cada janela do E2 ao E4, e nenhum no E1. A
maior parte dos clientes que ele bloqueou compartilhava fingerprints com clientes que ele deixou
passar. Com um perfil sem os clientes bloqueados, os escopos concordam
com o WAF por construção. Com um perfil de todos os clientes, a concordância fica abaixo de uma
escolha aleatória em todos os serviços. Por isso o artigo não usa o WAF como rótulo de ataque.

## 3.5 A recomendação, passo a passo (Seção VI)

1. **Dois fatores guiam a escolha em cada serviço:** o piso e a sensibilidade do gatilho. Nos três
   serviços pequenos, a beta-binomial cruzada só aponta pilhas compartilhadas a partir de 3 a 4
   janelas medianas e pilhas novas a partir de 2 a 3. Abaixo disso, o recurso é um limite de taxa
   ou um desafio a todos.
2. **O candidato** é a beta-binomial cruzada atrás do gate sazonal, com o recurso abaixo do piso
   dela. Pensada *post hoc*, ela foi fixada antes do bloco de 14 dias, e lá a comparação fixada de
   antemão a preferiu ao filtro de inéditos em todos os serviços. Nos mesmos 14 dias, ela errou
   em menos janelas que a binomial (20 contra 31, mas 14 contra nenhuma no E1) e deteve uma parte
   maior de uma botnet de 100 atacantes.
3. **O custo dela:** picos de 1.000 usuários a disparam em um terço das janelas, com filtros
   leves, e, em mediana, um erro dela bloqueia dois terços da janela. Quando o gate dela abre
   numa janela limpa e o escopo não aponta nada, entra o recurso, o limite de taxa ou o desafio a
   todos. Isso acontece em 1,5% das janelas limpas, um custo para os usuários que o orçamento de
   falsos alarmes não conta.
4. **A alternativa mais simples,** o z-score calibrado, errou tantas vezes quanto ela (20) e
   disparou em menos picos, mas deteve menos.
5. **No E1,** a beta-binomial perde a maior parte das pilhas novas, que o filtro de inéditos como
   gatilho próprio mantém sem falso alarme. Usar os dois juntos ali não foi testado.
6. **Depois,** uma avaliação mais longa, porque nenhum dia posterior testou essa escolha. A
   binomial errou em dias úteis, o que um gatilho calibrado por dia da semana talvez absorva. E os
   erros da beta-binomial no E1 se concentram em dois dias.

## Teste-se: Parte 3

<details>
<summary>1. Na Tabela IV, a binomial dá só 0,1% de falsos alarmes. Por que se diz que cada erro
pesa?</summary>

Porque, em mediana, um falso alarme bloqueia 32,9% dos clientes da janela, um terço. Na média,
isso dá 0,03% dos clientes por janela limpa.

</details>

<details>
<summary>2. Nos dias de teste, por que a configuração barra no E1 só 12% de uma botnet de um décimo
da janela em pilhas novas, que o escopo reconheceria em 90%?</summary>

Porque o gate quase não abre. Uma botnet de cerca de 300 atacantes acrescenta 10% às cerca de 3.000
origens do E1, e o gate abre em só 6% a 13% dessas janelas.

</details>

<details>
<summary>3. No bloco, o gate abriu metade das vezes, e mesmo assim a taxa dobrou. Como?</summary>

A taxa é a abertura do gate vezes o erro do escopo quando ele abre. O gate caiu de 2,98% para
1,45%, mas o erro do escopo subiu de 2,98% para 13,3%, mais de quatro vezes. O produto foi de
0,089% para 0,19%.

</details>

<details>
<summary>4. A recomendação final foi confirmada por um teste independente?</summary>

Não. A configuração foi construída depois de ver os dados e escolhida pela comparação fixada
antes, nos mesmos 14 dias. Nenhum dia posterior a testou, e o artigo diz isso.

</details>

---

# Parte 4. Consulta

## 4.1 Os números para guardar

**O método**
- ρ = 3, k_min = 5, λ_e de no máximo 0,01, gates no percentil 99.
- Orçamento: 1% das janelas de calibração, cerca de 2,9 das 288 de um dia.
- Pesos de Ω: TLS 1,0, endpoint 0,6, /24 0,3.
- Piso de pilhas novas pelo filtro de inéditos: 139 atacantes no E1 a E3 (25 pilhas). No E4, o
  teste aponta antes, a partir de 84. Limite de enriquecimento: 1,2% do perfil.

**Tráfego gerado**
- Moda: 0,0% do ataque e 39,0% do legítimo a partir de cinco pilhas (61,1% com α = 2,0).
- Teste binomial: 90,3% da botnet com 25 pilhas novas, sem dano observado.
- Adversarial: o teste barra 30,4%, com 3,78% de dano.
- Detecção sessão por sessão: no acaso (AUC de 0,50).

**Produção, dias de teste**
- Janela mediana: E1 2.983 origens, E2 62, E3 41, E4 20.
- Binomial: 0,1% de falsos alarmes (5 de 5.643, de 0,03% a 0,21%). Em mediana, um
  deles bloqueia 32,9% da janela. Dano esperado: 0,03% dos clientes por janela limpa.
- Sozinhos: escopo 2,2%, gate 3,0% (5,4% no E1).
- O gate abriu em mais 163 janelas limpas (2,9%) sem que o escopo apontasse nada: nelas age o
  recurso, o limite de taxa ou o desafio a todos.
- Picos de 1.000 disparam a binomial em 22,2% das janelas, com filtros de 4,3%.
- Níveis: 10⁻²¹ (E1), 10⁻⁷³ (E2), 10⁻¹¹ (E3), 10⁻⁴ (E4).
- Piso em pilhas compartilhadas: 254 no E1 (8% da janela), de 4 a 19 janelas nos pequenos.
- No E1: o gate abre em 6% a 13% das janelas, e a binomial detém 11,8% da botnet de um décimo em
  pilhas novas, contra 89,6% do escopo sozinho.

**Teste prospectivo**
- Dia novo: 2 falsos alarmes em 1.152 janelas (P = 0,27). O gate abriu 3 vezes, e o escopo errou 2.
- Bloco: 31 de 16.103 (0,19%, de 0,13% a 0,27%, P < 10⁻⁴). O gate abriu em 1,45% das janelas, e o
  escopo errou em 13% das aberturas, contra 3%. 30 dos 31 erros em dias úteis.
- Beta-binomial cruzada atrás do gate sazonal: 0,12% de falsos alarmes (0,35% no E1). Somando os
  serviços, detém 61,0% de 100 atacantes em pilhas novas e 39,7% em compartilhadas. Picos de 1.000 a
  disparam em 33,5% das janelas, e, em mediana, um erro dela bloqueia 65,7% da janela.
- Filtro de inéditos sem gate: nenhum falso alarme, 89,6% da botnet de um décimo do E1 em pilhas
  novas.

**Custo**
- Agregação contando classes: 0,33 s com 1.000 sessões, contra 52,8 s guardando pares.
- Admissão contando classes: de 0,33 a 0,42 milionésimo de segundo por requisição. Guardando pares,
  de 2,3 a 127 milionésimos, de 100 a 10.000 sessões.

## 4.2 Glossário

Os termos estão agrupados por tema. A primeira coluna é como o artigo escreve, em itálico; a
segunda, como este guia diz em português.

**O tráfego e o que se conta**

| No artigo | Em português | O que é |
|---|---|---|
| *endpoint* (E1 a E4) | serviço | o serviço protegido. E1: sinais de monitoramento de usuários reais, o mais movimentado; E2: console web; E3: API; E4: login único |
| *JA4 fingerprint* | fingerprint, impressão digital TLS | o resumo de como o software do cliente abre a conexão TLS: o "sotaque" do visitante |
| *stack* | pilha TLS | o software que produz um fingerprint. Uma botnet usa poucas pilhas, repetidas em muitos aparelhos |
| *origin* | origem | o endereço de rede (IP) de onde vem a sessão, contado uma vez por fingerprint que apresenta |
| *window*, n₀ | janela, janela mediana | cinco minutos de um serviço, 288 por dia; n₀ é o tamanho típico de uma janela, em origens |
| *clean windows* | janelas limpas | janelas sem botnet injetada, tomadas como sem ataque. Janelas com menos de 5 origens ficam de fora |
| *fleet* | frota | clientes legítimos que chegam juntos, como robôs de monitoramento |
| *flash crowd* (*Fl. 1k*) | pico legítimo | muitos usuários reais chegando de uma vez. *Fl. 1k* é a fração das janelas em que um pico de 1.000 usuários dispara a configuração |
| *Ω*, *coordination mass* | massa de coordenação | contagem ponderada de pares de origens que compartilham JA4, endpoint ou /24. Mede sobretudo volume |

**O gatilho: quando agir**

| No artigo | Em português | O que é |
|---|---|---|
| *trigger*, *gate* | gatilho | a condição que faz o sistema agir. Se não dispara, nada é aplicado |
| *distinct-origin gate* (*Origin gate*) | gate de origens distintas | dispara quando a janela passa do percentil 99 de origens das janelas normais (e tem pelo menos 5). É o gatilho da configuração binomial |
| *base rule* (*Ω gate*) | regra básica | o gatilho pela massa Ω no percentil 99, com o teste binomial como escopo. É a referência dos protocolos |
| *seasonal gate* | gate sazonal | compara as origens da janela com a mediana da mesma hora nos dias de calibração (*post hoc*) |
| *No gate*, *the scope alone*, *own trigger* | sem gate, o escopo sozinho | o escopo age em toda janela e é o próprio gatilho (*post hoc*) |
| *fallback* | recurso de contingência | o limite de taxa ou o desafio a todos, quando o gatilho dispara e o escopo não seleciona nada |

**O escopo: quem bloquear**

| No artigo | Em português | O que é |
|---|---|---|
| *scope* | escopo | o conjunto de fingerprints que o filtro vai bloquear ou desafiar, naquele serviço e naquela janela. Não é uma lista fixa: é recalculado a cada alarme, comparando o alarme com o perfil. Se uma botnet usa 25 pilhas raras, o escopo são esses 25 fingerprints: quem apresenta um deles é barrado, quem apresenta outro passa. Um bom escopo é estreito, pega os atacantes e quase nenhum cliente legítimo. Se o gatilho dispara e o escopo sai vazio, entra o recurso |
| *selects* | selecionar (o guia diz "apontar") | o escopo seleciona um fingerprint quando o põe no filtro |
| *modal fingerprint* | fingerprint modal | o fingerprint mais comum do alarme: a escolha óbvia, que falha quando a botnet se divide em várias pilhas |
| *profile*, b(f) | perfil | a distribuição normal dos fingerprints, medida em dias sem ataque; b(f) é a fração de cada um |
| *binomial (enrichment) test* | teste binomial de enriquecimento | seleciona um fingerprint pelo menos três vezes acima do perfil (ρ = 3) e improvável por acaso, no nível λₑ |
| *Bonferroni* | correção de Bonferroni | dividir o nível pelo número de fingerprints testados, para não confundir coincidência com ataque |
| *unseen filter* | filtro de inéditos | seleciona fingerprints ausentes do perfil com pelo menos 5 origens |
| *union* | união | o teste junto com o filtro de inéditos: o escopo da configuração binomial |
| *z-score* | escore z | uma regra mais simples relativa ao perfil, usada como comparação |
| *known fleets* | frotas conhecidas | as frotas frequentes, postas numa lista de exceções: o escopo nunca as bloqueia |
| *enrichment limit* | limite de enriquecimento | não se espera que fingerprints comuns demais fiquem três vezes acima do normal (acima de 1,2% do perfil, com 25 pilhas) |

**A calibração: quão exigente ser**

| No artigo | Em português | O que é |
|---|---|---|
| *level* λₑ | nível | o limite de improbabilidade do teste, calibrado por endpoint, no máximo 0,01 |
| *false-alarm budget* | orçamento de falsos alarmes | no máximo 1% das janelas de calibração com falso alarme |
| *background* | modelo do normal | o que o teste espera ver por acaso: binomial ou beta-binomial |
| *beta-binomial* | beta-binomial | um modelo do normal mais tolerante que a binomial. A binomial supõe que cada origem escolhe o seu fingerprint sozinha, como moedas jogadas uma a uma. Em produção, frotas de clientes legítimos ligam juntas, e um fingerprint aparece em bloco, muito acima do que a binomial espera. Para não tratar isso como ataque, a binomial precisa de um nível exigentíssimo (10⁻²¹ no E1, mesmo com as frotas conhecidas isentas), que sobe o piso. A beta-binomial mede, nas janelas de calibração, uma correlação φ para cada fingerprint do perfil: o quanto os seus clientes tendem a chegar juntos. Com isso, o surto de uma frota fica dentro do esperado, o nível pode ser menos exigente (10⁻⁴ no E1) e o piso cai. Fingerprints fora do perfil seguem a binomial, porque não há como medir φ para eles. O preço, em amostra, foram mais falsos alarmes (19 dos 22 no console). Com a calibração cruzada, ela erra tão pouco quanto a binomial, com erros mais leves. É *post hoc* e é o modelo do candidato atual |
| *in sample* | em amostra | calibrar e julgar com os mesmos dias |
| *cross-fitted* (`†`) | calibração cruzada | julgar cada dia de calibração contra o perfil dos outros dias, como se julga um dia de teste |
| *calibration floor* | piso de calibração | o tamanho de botnet a partir do qual o escopo seleciona uma pilha típica dela. Abaixo dele, o escopo ainda seleciona as pilhas que o acaso deixou maiores |

**Os resultados: como se mede**

| No artigo | Em português | O que é |
|---|---|---|
| *false alarm* (*FA*), *misfire* | falso alarme, disparo indevido | a configuração produz um filtro numa janela limpa: com gate, o gate abre e o escopo seleciona algo; sem gate, basta o escopo. FA é a fração das janelas limpas em que isso acontece |
| *collateral* (*Coll.*) | dano colateral | a fração dos clientes da janela que um falso alarme bloqueia, em mediana |
| *coverage*, *covers* | cobertura | a fração da botnet injetada que a configuração barra, na média de todas as janelas de ataque, inclusive as que o gate perde |
| *New*, *Shared* | pilhas novas, compartilhadas | pilhas da botnet ausentes do tráfego legítimo, ou raras e usadas também por clientes reais |
| *tenth-size* (*0.1×*), *1×* | botnet de um décimo, de uma janela | uma botnet de um décimo da janela mediana, ou de uma janela inteira |
| *adversarial* | botnet adversarial | botnet nos 25 fingerprints mais comuns do serviço: a fronteira do método |
| *lost to the gate* | perdido para o gate | na Fig. 2, o que o escopo selecionaria e o gate deixa passar |

**Os testes fixados antes**

| No artigo | Em português | O que é |
|---|---|---|
| *held-out day* (*held*) | dia novo | o nono dia, analisado com o protocolo fixado antes |
| *14-day block* | bloco de 14 dias | os 14 dias de 26/09 a 09/10, analisados com tudo fixado antes |
| *pre-specified* | fixado antes | escolhido antes de os dados serem lidos |
| *post hoc* (`*`) | pensado depois | pensado depois de ver os dados (depois do dia novo) |
| *binomial configuration* | configuração binomial | o gate de origens distintas com a união e as frotas conhecidas: a principal, fixada antes |
| *current candidate* | candidato atual | a beta-binomial cruzada atrás do gate sazonal, com o recurso abaixo do piso; *post hoc*, fixado antes do bloco |

**Siglas.** ALPN: o protocolo de aplicação pedido no *ClientHello*. ASN: o número da rede de
origem. AUC: área sob a curva ROC. CDN: rede de distribuição de conteúdo. DOTS e Flowspec: canais
padrão para pedir mitigação. OCSF, STIX e MISP: formatos e plataformas de troca de alertas. OWL:
a linguagem da ontologia. RUM: monitoramento de usuários reais (E1). SSO: login único (E4). WAF:
firewall de aplicação.

## 4.3 Onde está cada coisa

**O artigo** (`papers/http-session-noms/article.tex`)

| Seção | Conteúdo | Elementos |
|---|---|---|
| I, II | o problema e o que já existe | Tabela I |
| III | o método: ameaça, gatilho, escopo e calibração, piso, ontologia | Fig. 1 |
| IV | a avaliação: fontes, configurações, métricas | Tabela II |
| V-A | o tráfego gerado | Tabela III |
| V-B | falsos alarmes e piso em produção | Tabelas IV e V |
| V-C | o gatilho decide | Fig. 2, Tabela VI |
| V-D | o que a evidência sustenta: *post hoc*, dia novo, bloco, WAF | Fig. 3 |
| VI | a recomendação e os limites | Tabela VII |
| VII | a conclusão | |
| Apêndices A a F | especificação, pesos, limites e laboratório, custo, detalhes de produção, reprodutibilidade | Fig. 4, Listagem 1 (D) |

**No repositório**
- `experiments/sprint-6-noms/results/`: os resultados anonimizados (`production_tables.json`,
  `production_tables_block.json`, `block_report.json`) e os protocolos (`fresh_day_protocol.md`,
  `heldout_block_protocol.md` e seus adendos).
- `experiments/sprint-6-noms/scripts/`: a avaliação em produção (`rule_detection_production.py`),
  as tabelas (`production_tables.py`), o relatório do bloco (`block_report.py`), a consulta
  compilada (`compile_counts.py`) e a auditoria (`audit_paper.py`).
- `ontology/ddos_ontology.owl`: a ontologia.
- `docs/concepts.md` e `docs/metrics.md`: os conceitos e as métricas, em inglês.
- `cd experiments/sprint-6-noms && make audit`: confere os números do artigo contra os resultados.
