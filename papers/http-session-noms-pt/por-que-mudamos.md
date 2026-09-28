# Por que o artigo deixou de ser "sobre grafos de conhecimento"

Este texto conta, sem matemática, como o trabalho começou, o que os dados mostraram e
por que o artigo mudou de foco. Ele serve para entender a história e para responder,
numa apresentação, à pergunta "por que o título não fala mais em *knowledge graph*?".

---

## Em uma frase

Começamos achando que um **grafo de conhecimento** de sessões detectaria ataques melhor e
explicaria o veredicto. Os dados mostraram que detectar é a parte fácil. O difícil, e o
que ninguém mede, é decidir **quais clientes bloquear sem bloquear os usuários de
verdade**. O artigo passou a medir isso, e o grafo ficou como a **especificação** que
diz o que contar.

---

## 1. De onde partimos (abril a agosto de 2026)

O primeiro título do artigo para o NOMS (22 de agosto de 2026) era:

> *Session-Centric Knowledge Graphs for Explainable Detection and Scoped Mitigation of
> Application-Layer DDoS*
> (Grafos de conhecimento centrados em sessões para detecção explicável e mitigação com
> escopo de DDoS na camada de aplicação)

**A ideia, em palavras simples.** Cada visita ao site (uma *sessão*) vira um ponto de um
grafo. Duas sessões ficam ligadas quando têm algo em comum:
- a mesma impressão digital TLS, o "sotaque" do software do cliente;
- o mesmo endereço atacado (*endpoint*);
- a mesma vizinhança de rede (/24).

Cada tipo de ligação tinha um **peso**, maior para o sinal mais difícil de o atacante
disfarçar. Uma **regra lógica** (escrita em SWRL e SPARQL) somava essas ligações. Essa
soma se chamava **massa de coordenação Ω**, e quando ela passava de um limite a regra
declarava "ataque coordenado". Tudo isso vivia numa **ontologia OWL**, o dicionário
formal que define o que é uma sessão, uma origem e uma relação.

**As quatro promessas daquela versão:**
1. **Detectar melhor.** Olhar as relações *entre* sessões pegaria ataques furtivos que
   escapam de quem olha cada sessão sozinha.
2. **Explicar.** O caminho lógico da regra (a *derivação*) seria a própria explicação do
   veredicto.
3. **Dizer o que bloquear.** Da mesma evidência sairia o escopo da mitigação.
4. **Exportar a evidência** em padrões usados pela área (JSON-LD e STIX 2.1).

Entre maio e junho construímos tudo isso: o pipeline que transforma capturas de rede em
grafo (Jena/TDB2), um gerador de ataques furtivos, os testes contra modelos de
aprendizado de máquina e a comparação com o KLAGE, o sistema publicado mais próximo.

---

## 2. O que os dados mostraram: o que não batia

Cada item diz o que esperávamos, o que vimos e por que isso pesou.

### 2.1 A vantagem na detecção vinha de contagens, e o grafo era só a calculadora

- **Esperado:** o grafo detectaria o ataque furtivo que o modelo por sessão não vê.
- **Visto:** no tráfego gerado, o modelo por sessão fica no acaso (AUC 0,50) e o que usa
  informação entre sessões chega a 0,98. Mas essa informação é uma contagem: *quantas
  outras sessões têm a mesma impressão TLS, o mesmo endpoint, a mesma /24*. Uma tabela
  comum, com essas contagens como colunas, dá o mesmo resultado.
- **Por que pesou:** o ganho é da **estrutura entre sessões**, qualquer que seja o jeito
  de calculá-la. O artigo não podia dizer que o grafo detecta melhor.

### 2.2 Em ataques reais de laboratório, olhar cada sessão já bastava

- **Esperado:** a vantagem apareceria também em dados públicos.
- **Visto:** no CIC-IoT2023 (*DDoS Slowloris*), um bom classificador por sessão chega a
  F1 = 0,900, e a representação entre sessões a 0,911. Esses ataques deixam uma marca em
  cada sessão, então olhar a sessão sozinha já resolve.
- **Por que pesou:** a grande diferença (0,50 contra 0,98) só existe no tráfego furtivo
  que **o nosso gerador fabrica por construção**. Isso não prova que ela exista na vida
  real.

### 2.3 O modelo aprendido não se transferia

- **Visto:** treinado e testado com o mesmo número de "pilhas" da botnet, o modelo acerta
  0,95 a 0,995. Quando a botnet muda de forma (outro número de pilhas), cai para 0,48 a
  0,75, ou seja, perto do chute.
- **Por que pesou:** o modelo decorava a faixa de valores de uma configuração do
  gerador. Já a regra por impressão TLS, que não treina nada, mantém cerca de 90% em
  qualquer número de pilhas até 25.

### 2.4 A "massa de coordenação" Ω era quase só volume

- **Visto:** 91% do valor de Ω vem de um único termo, o que conta pares de visitantes no
  mesmo endpoint. Isso cresce com o número de visitantes, seja ataque, seja multidão
  legítima. Por janela de cinco minutos, Ω sozinha dispara em 80% a 100% dos **picos
  legítimos** (um *flash crowd*, como a abertura de vendas de ingressos).
- **Analogia:** era um alarme que tocava sempre que o saguão enchia, fosse invasão ou
  show.
- **Consequência:** nos dados reais, **contar visitantes distintos** faz o mesmo papel
  com metade dos alarmes falsos. Os dois concordam em 136 das 181 janelas limpas em que
  algum dispara. O gatilho do artigo virou essa contagem, e Ω ficou como a regra de
  referência.

### 2.5 Os pesos das relações não se sustentaram

- **Visto:** ao procurar os melhores pesos entre 125 combinações, só se confirmou que a
  **impressão TLS** importa mais. Qualquer peso para o endpoint dava o mesmo resultado, e
  a vizinhança de rede quase não ajudava.
- **Por que pesou:** a hierarquia de pesos era uma das novidades prometidas, e os dados
  sustentam só o topo dela.

### 2.6 Na escala de uma CDN, o grafo virou contagem

- **Visto:** guardar cada ligação entre pares de sessões cresce com o quadrado do número
  de sessões. Com 1.000 sessões, isso leva 52,8 s. Contando **classes** (quantas sessões
  têm cada impressão TLS, o que equivale a um `GROUP BY` em SQL), o mesmo cálculo leva
  0,33 s, e 26,4 s com 100.000 sessões.
- **Consequência:** na avaliação real **nenhum "raciocinador" lógico roda**. O que
  funciona é contar.

### 2.7 A explicabilidade não podia ser provada

A promessa de que a derivação lógica "explica" o veredicto exigiria um estudo com
operadores humanos, e esse estudo não foi feito. Sem ele, o artigo não pode afirmar que
a explicação ajuda alguém.

### 2.8 Os dados reais da CDN mudaram a pergunta

Com oito dias de quatro serviços da Azion, ficou claro:
- **perceber** que um endpoint está sob ataque é fácil, basta contar visitantes
  distintos;
- **escolher quem bloquear** é difícil, porque grupos de clientes legítimos que chegam
  juntos (as *frotas*, como robôs de monitoramento) parecem ataques para um teste
  estatístico ingênuo.

A pergunta nova e útil passou a ser: **quem bloquear, a que custo para os usuários, e
onde isso deixa de ser possível?** Ninguém na literatura mede isso.

### 2.9 As revisões simuladas diziam o mesmo

Usamos agentes revisores que imitam o comitê do NOMS. Com o enquadramento de grafo, a
nota travou em *weak reject* (3/3/2/4) por várias rodadas, mesmo com análises novas a
cada rodada. Um revisor escreveu que a ontologia era, no máximo, "uma especificação de
apoio: um esquema de configuração mais um vocabulário de exportação". Ele também notou
que a lacuna de troca entre ferramentas (item 4 abaixo) se sustenta sem OWL.

---

## 3. O que mudamos, e por quê

**A regra de ouro de uma conferência como o NOMS** é que o que o artigo promete tem que
ser o que os dados mostram. Prometer mais do que a evidência sustenta derruba a nota,
por melhor que seja o resto.

Por isso mudamos o foco para a parte que é **nova e medida em tráfego real**:
- o **escopo por impressão TLS**, escolhido por um teste estatístico **calibrado** para
  errar pouco em dias normais;
- o **custo** de cada filtro em clientes legítimos bloqueados;
- os **limites**: o piso de calibração, o limite da razão e o papel do gatilho.

**Como o título mudou:**

| Data | Título | O que mudou |
|---|---|---|
| 22 ago 2026 | *Session-Centric Knowledge Graphs for Explainable Detection and Scoped Mitigation of Application-Layer DDoS* | o grafo detecta e explica |
| 25 set 2026 | *Scoped Mitigation of Application-Layer DDoS with a Session-Centric Knowledge Graph* | a decisão passa a ser o escopo, e entram os dados reais |
| 26 set 2026 | *Calibrated Scoping of Application-Layer DDoS Mitigation with a Session-Centric Knowledge Graph* | entra a calibração e o piso |
| 27 set 2026 | *TLS-Fingerprint Scoping of Application-Layer DDoS Mitigation: Calibration Floors and Collateral on a CDN Operator's Endpoints* | o título diz o que é medido, e o grafo vira especificação |

**O que saiu e o que ficou:**

| Saiu do artigo (ou virou detalhe) | Ficou |
|---|---|
| "O grafo detecta melhor" | A estrutura entre sessões, medida, com seus limites |
| A regra lógica como detector | Ω como regra de referência do protocolo |
| A explicação pela derivação | A cadeia de evidência exportada (JSON-LD, STIX 2.1) |
| Os seis pesos como achado | Os pesos definidos na ontologia, com a calibração no Apêndice B |
| O modelo aprendido como contribuição | O modelo aprendido como comparação justa |
| — | **Novo:** escopo calibrado, dano colateral, piso, limite da razão, gatilho, dia novo |

Depois da mudança, as revisões simuladas foram de *weak reject* para *borderline* e
chegaram a *weak accept*. Na última, o artigo ficou à frente de 70% a 80% dos
submetidos, sem nenhum problema bloqueante.

---

## 4. O que ficou do grafo de conhecimento

O grafo não foi jogado fora. Ele mudou de papel, da **casa** para a **planta da casa**.

- **A ontologia é a especificação.** Ela define as sessões, as relações que se contam e
  a unidade de contagem (origens). **Dela se compila a consulta SQL** que o armazenamento
  de logs da operadora executa. Essa consulta reproduziu as contagens exportadas da Azion
  em 1.152 de 1.152 janelas em cada um de dois dias. Um sinal novo entra com quatro
  triplas da ontologia (quatro "frases" do tipo sujeito, propriedade e valor) e nenhuma
  linha de código.
- **A cadeia de evidência é exportada** em JSON-LD e STIX 2.1. Foi exportando que
  descobrimos a terceira contribuição, a **lacuna de troca**: os padrões que as
  ferramentas usam para trocar informações de ameaça e pedidos de bloqueio (STIX, DOTS,
  Flowspec, OCSF) não têm uma forma padrão de dizer "bloqueie esta impressão JA4". O
  importador do MISP, por exemplo, descartou as 26 impressões dos escopos exportados.
- **Ω continua** como a regra base, a referência fixada no protocolo do dia novo.

---

## 5. Três frases prontas para a apresentação

1. "Começamos achando que o grafo detectava melhor. Os dados mostraram que a vantagem
   vinha de contagens que qualquer tabela faz, e que perceber o ataque é fácil quando se
   contam os visitantes."
2. "O problema difícil e novo é decidir quem bloquear sem machucar os usuários. É isso
   que o artigo mede, em tráfego real de uma CDN."
3. "A ontologia ficou como especificação: dela sai a consulta que roda no log e o
   formato do escopo exportado, e foi assim que achamos a lacuna nos padrões de troca."

---

## 6. Perguntas que podem surgir

**"Então o grafo foi tempo perdido?"**
Não. Foi construindo o grafo que medimos o que ele acrescenta e o que não acrescenta. E
ele continua no artigo como especificação: a consulta compilada e a exportação saem
dele.

**"Por que não manter *knowledge graph* no título?"**
Porque o título tem que dizer o que o artigo mede. Com *knowledge graph* no título, o
revisor espera que o grafo melhore a detecção, e os dados não mostram isso.

**"A mudança foi para agradar os revisores?"**
Ela seguiu os dados. As revisões só confirmaram o que os experimentos já mostravam: a
vantagem do grafo não se sustentava fora do tráfego gerado, e a decisão de escopo não
estava medida em lugar nenhum.

**"O que um grafo ainda poderia trazer no futuro?"**
Relações que não são "igualdades", como impressões TLS quase iguais ou padrões de tempo
parecidos, precisam de ligações entre pares e não cabem numa contagem de classes. Elas
estão especificadas na ontologia, mas não foram exercitadas.

---

*Fontes no repositório:*
- *o histórico do Git (títulos e resumos de cada versão);*
- *`experiments/sprint-6-noms/README.md`, seções 6, 10, 14 e 19;*
- *`docs/concepts.md`, seção 7;*
- *os Apêndices B, C e D do artigo.*
