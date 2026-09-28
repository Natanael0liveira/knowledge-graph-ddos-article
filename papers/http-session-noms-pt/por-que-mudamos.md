# Por que o artigo mudou: de "grafo de conhecimento" para "escopo por impressão TLS"

## A resposta curta

> O artigo prometia que um **grafo de conhecimento** detecta ataques melhor e explica o
> porquê. Os testes **não confirmaram** isso. Confirmaram outra coisa, que é nova: um
> jeito **calibrado** de decidir **quais clientes bloquear**, com o **custo** para os
> usuários reais medido e os **limites** de onde isso funciona. O artigo passou a
> prometer só o que os dados mostram, e o grafo ficou como a especificação do que
> contar.

Esta é a resposta de 30 segundos. O resto do texto explica cada parte dela.

---

## 1. Antes e depois, lado a lado

| | Antes (agosto de 2026) | Depois (setembro de 2026) |
|---|---|---|
| **A pergunta** | Como **detectar** o ataque? | **Quem bloquear**, sem bloquear os usuários? |
| **A ferramenta principal** | Um grafo de conhecimento e uma regra lógica | Um teste estatístico sobre a impressão TLS |
| **A promessa** | Detectar melhor e explicar o veredicto | Decidir o bloqueio, com custo e limites medidos |
| **Os dados** | Tráfego gerado e capturas de laboratório | Os mesmos, mais oito dias reais da Azion |
| **O papel do grafo** | O detector | A especificação, a "planta" do sistema |
| **O título** | *Session-Centric Knowledge Graphs for Explainable Detection and Scoped Mitigation of Application-Layer DDoS* | *TLS-Fingerprint Scoping of Application-Layer DDoS Mitigation: Calibration Floors and Collateral on a CDN Operator's Endpoints* |

---

## 2. Os três motivos da mudança

### Motivo 1. O grafo não detectava melhor do que uma planilha

**A analogia.** Duas pessoas querem saber quantos visitantes de um prédio falam com o
mesmo sotaque. Uma desenha um mapa, ligando cada visitante a todos os que falam igual. A
outra faz uma planilha e conta. As duas chegam ao mesmo número. Quem descobre o ataque é
a **contagem**, e o mapa é só um jeito caro de fazê-la.

**O que os testes mostraram:**
- A vantagem vinha de **contar** quantas conexões compartilham a mesma impressão TLS, o
  mesmo serviço ou a mesma vizinhança de rede. Uma tabela simples com essas contagens
  detecta tão bem quanto o grafo.
- Em ataques reais de laboratório, olhar **cada conexão sozinha** já bastava: nota de
  acerto 0,99, contra 0,98 usando as contagens entre conexões.
- A vantagem grande só aparecia no **nosso próprio tráfego gerado**, que foi construído de
  propósito para ser furtivo. Isso não prova que ela exista fora do laboratório.
- O modelo treinado sobre essas contagens **falhava quando a botnet mudava de forma**. A
  nota caía de 0,95 para 0,48 a 0,75, em alguns casos no nível de um chute.

**Conclusão:** não dava para escrever "o grafo detecta melhor".

### Motivo 2. Detectar era a parte fácil; o difícil era decidir quem bloquear

Quando chegaram os oito dias reais dos serviços da Azion, ficaram claras duas coisas.

**Perceber o ataque é simples.**
- Basta contar quantos visitantes **diferentes** chegaram nos últimos cinco minutos.
- Esse contador simples fez o mesmo trabalho da regra complexa do grafo, com **metade
  dos alarmes falsos**.
- A regra do grafo era quase só volume. Em multidões legítimas simuladas, como uma
  abertura de vendas, ela disparava em 80% a 100% das vezes. Era um alarme que tocava
  sempre que o saguão enchia, fosse invasão ou show.

**Decidir quem bloquear é o problema de verdade.**
- A escolha óbvia, bloquear o "sotaque" mais comum do momento, bloqueia 39% dos clientes
  e **nenhum** atacante.
- Grupos de clientes legítimos que chegam juntos, como robôs de monitoramento, parecem
  ataque para um teste ingênuo.
- **Ninguém na literatura media** quanto esse bloqueio custa aos usuários reais nem onde
  ele deixa de ser possível. Essa é a novidade que os dados sustentam.

**Conclusão:** a contribuição forte estava no **bloqueio**, e o artigo estava escondendo-a
atrás da detecção.

### Motivo 3. Um artigo só pode prometer o que os dados mostram

Das promessas da primeira versão, os dados sustentaram pouco:
- **"Detecta melhor":** não se confirmou fora do tráfego gerado (motivo 1).
- **"Explica o veredicto":** para afirmar isso seria preciso um estudo com operadores
  humanos, e esse estudo não foi feito.
- **"Os pesos de cada tipo de ligação":** só se confirmou que a impressão TLS pesa mais que
  as outras ligações. Os outros pesos ficaram sem apoio nos dados.

Nas revisões simuladas, que imitam o comitê do NOMS, o artigo ficou em **"rejeição
fraca"** por várias rodadas, mesmo com análises novas a cada rodada. Depois que ele passou
a prometer o que os dados mostram, foi para **"aceitação fraca"**, à frente de 70% a 80%
dos submetidos.

**A analogia.** É como anunciar um carro pela velocidade quando o que ele tem de único é o
consumo. Quem testa a velocidade se decepciona e nem chega a olhar o consumo.

---

## 3. O que o grafo virou

O grafo não foi jogado fora. Ele deixou de ser o **morador** da casa e virou a **planta**.

- **A ontologia é a especificação.** Ela diz o que contar: sessões, origens e as relações
  de "mesma impressão", "mesmo serviço" e "mesma vizinhança". Dela se gera
  automaticamente a consulta que roda nos logs da Azion, e essa consulta bateu com as
  contagens exportadas em **todas** as janelas de dois dias. Um sinal novo entra mudando
  quatro linhas da ontologia, sem mexer no código.
- **A exportação revelou a terceira contribuição.** Quisemos mandar o bloqueio para outras
  ferramentas nos formatos padrão (STIX, DOTS, Flowspec, OCSF) e descobrimos que **nenhum
  deles sabe dizer "bloqueie esta impressão TLS"**. O MISP, por exemplo, descartou todas as
  26 impressões exportadas.
- **A regra do grafo continua** como a regra de referência, com que a configuração
  recomendada é comparada.

---

## 4. Como a mudança aconteceu

| Data | O que aconteceu |
|---|---|
| abr–jun 2026 | Construímos o grafo, a regra lógica, o gerador de ataques e os testes contra aprendizado de máquina. |
| 22 ago 2026 | Primeira versão para o NOMS: "grafos de conhecimento para detecção explicável". |
| 24 set 2026 | Testamos a regra janela a janela: ela dispara com multidões legítimas. |
| 25 set 2026 | Entram os dados reais da Azion, e o título passa a falar em **mitigação com escopo**. |
| 26 set 2026 | Entram a calibração e o piso, e o título passa a falar em **escopo calibrado**. |
| 27 set 2026 | O título passa a dizer só o que se mede: **escopo por impressão TLS, pisos e dano colateral**. |
| 27–28 set 2026 | Revisões focadas no que o artigo promete; ele chega a "aceitação fraca". |

---

## 5. O que dizer na apresentação

1. "Começamos achando que o grafo detectava melhor. Os testes mostraram que a vantagem
   vinha de contagens que uma planilha faz, e que perceber o ataque é fácil quando se
   contam os visitantes."
2. "O problema difícil e novo é decidir quem bloquear sem machucar os usuários. É isso que
   o artigo mede, em tráfego real de uma CDN."
3. "O grafo virou a planta do sistema: dele sai a consulta que roda no log e o formato do
   bloqueio exportado, e foi assim que achamos a falha nos padrões de troca."

**Se perguntarem "então o grafo foi tempo perdido?":** não. Foi construindo o grafo que
medimos o que ele acrescenta e o que não acrescenta. E ele continua no artigo como
especificação.

**Se perguntarem "a mudança foi para agradar os revisores?":** ela seguiu os testes. As
revisões só confirmaram o que os experimentos já mostravam.

---

## Anexo: os números por trás de cada motivo

Para quem quiser a evidência. Uma "nota de acerto" vai de 0,5, que é chutar, a 1, que é
acertar tudo.

| Motivo | O que foi medido | Número | O que significa |
|---|---|---|---|
| 1 | Acerto olhando cada conexão sozinha, no tráfego gerado furtivo | 0,50 | chute, porque o gerador esconde o ataque em cada conexão |
| 1 | Acerto usando as contagens entre conexões, no mesmo tráfego | 0,98 | a vantagem que o artigo prometia |
| 1 | Em ataque real de laboratório (CIC-IoT2023): por conexão contra entre conexões | 0,99 contra 0,98 | no mundo real, a vantagem some |
| 1 | Modelo treinado com um formato de botnet e testado com outro | de 0,95 para 0,48–0,75 | o modelo decora e não generaliza |
| 2 | Parte da regra do grafo que é só volume | 91% | a regra mede quantidade de gente |
| 2 | Multidões legítimas simuladas em que a regra dispara | 80% a 100% | alarme falso em show |
| 2 | Contador de visitantes contra a regra, em dados reais | mesmo acerto, metade dos alarmes falsos | contar basta para perceber o ataque |
| 2 | Bloquear o sotaque mais comum, no tráfego gerado | 39% dos clientes, 0% dos atacantes | a escolha óbvia é a pior |
| 3 | Pesos das ligações confirmados pelos dados | só o da impressão TLS | a hierarquia de pesos não se sustenta |
| 3 | Revisões simuladas, antes e depois | de "rejeição fraca" para "aceitação fraca" | prometer o que se mede muda a avaliação |
| — | Tempo para guardar todas as ligações de 1.000 sessões | 52,8 s, contra 0,33 s contando | na prática, o grafo virou contagem |

*Fontes no repositório:*
- *o histórico do Git, com os títulos e resumos de cada versão;*
- *`experiments/sprint-6-noms/README.md`, seções 6, 10, 14 e 19;*
- *`docs/concepts.md`, seção 7;*
- *os Apêndices B, C, D e E do artigo.*
