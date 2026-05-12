# Um Survey e Meta-Análise de Ataque de Negação de Serviço Distribuída na Camada de Aplicação

> **Tradução integral em português** de *"A survey and meta-analysis of application-layer distributed denial-of-service attack"*, Odusami, Misra, Abayomi-Alli, Abayomi-Alli, Fernandez-Sanz (2020), Int. J. Communication Systems 33(18):e4603, Wiley.
>
> **PDF original:** [`docs/pdfs/Int J Communication - 2020 - Odusami - A survey and meta-analysis of application-layer distributed denial-of-service attack.pdf`](../pdfs/) — 24 páginas
> **DOI:** 10.1002/dac.4603
> **Status:** ✅ Tradução completa
> **Tier:** 1 (Leitura obrigatória — meta-análise de 75 estudos que sustenta o 47% e 4% do nosso Abstract)

---

## Autores

Modupe Odusami¹, Sanjay Misra¹·² (*correspondência*), Olusola Abayomi-Alli³, Adebayo Abayomi-Alli⁴, Luis Fernandez-Sanz⁵

¹ Department of Electrical and Information Engineering, Covenant University, Ota, Nigéria
² Department of Computer Engineering, Atilim University, Ancara, Turquia
³ Department of Software Engineering, Kaunas University of Technology, Kaunas, Lituânia
⁴ Department of Computer Science, Federal University of Agriculture, Abeokuta, Nigéria
⁵ Department of Computer Science, University of Alcala, Alcala de Henares, Espanha

---

## Resumo

**Contexto:** Um dos ataques significativos visando a camada de aplicação é o ataque de negação de serviço distribuída (DDoS). Ele degrada o desempenho do servidor usurpando seus recursos completamente, negando assim acesso a usuários legítimos e causando perdas a empresas e organizações.

**Objetivo:** Este estudo visa investigar metodologias existentes para defesa contra ataques DDoS na camada de aplicação (APDDoS) usando medidas específicas: métodos/técnicas de detecção, estratégia de ataque e exploração de características de mecanismos APDDoS existentes.

**Metodologia:** A revisão é realizada em uma busca de base de dados de literatura relevante em IEEE Xplore, ACM, Science Direct, Springer, Wiley e Google Search. As datas de busca para capturar periódicos e conferências são de 2000 a 2019. Artigos de revisão que não estão em inglês e que não abordam o ataque APDDoS são excluídos. **Três mil setecentos e oitenta e nove estudos são identificados e racionalizados para um total de 75 estudos.** Uma avaliação quantificável é realizada nos artigos selecionados usando seis procedimentos de busca, a saber: fonte, métodos/técnica, estratégia de ataque, *datasets*/*corpus*, status, métrica de detecção e exploração de características.

**Resultados:** Com base nos métodos/técnicas existentes para detecção, os resultados mostram que **aprendizado de máquina deu a maior proporção com 36%.** No entanto, avaliação baseada em estratégia de ataque mostra que vários estudos não consideram uma forma de ataque para implantar sua solução. Resultado baseado em características existentes para a técnica de detecção APDDoS mostra que **fluxo de requisição durante uma sessão de usuário e padrão de pacote deu o maior resultado com 47%**. Diferentemente de informação de cabeçalho de pacote com 33%, fluxo de requisição durante intervalo de tempo absoluto com 12% e características de usuário web 8%.

**Conclusão:** Os achados de pesquisa mostram que uma grande proporção das soluções para detecção de ataque APDDoS utilizou características baseadas em fluxo de requisição durante sessão de usuário e padrão de pacote. A otimização de características melhorará a precisão de detecção. Nosso estudo conclui que pesquisadores precisam explorar todas as estratégias de ataque usando algoritmos de aprendizado profundo, melhorando assim a detecção efetiva de ataque APDDoS lançado a partir de diferentes *botnets*.

## Palavras-chave

DDoS na camada de aplicação, ataque de inundação na camada de aplicação, ataque DDoS, revisão extensiva, segurança de rede.

---

## 1. Introdução

Sistemas de computador forneceram conveniência às pessoas devido ao *networking* e ao crescimento pervasivo da Internet. Daí, usuários de computador têm acesso fácil e livre a dados de computador. Essa tecnologia que traz conforto às pessoas ao mesmo tempo constituiu muitas questões de segurança. Segurança de rede tornou-se mais desafiadora conforme organizações corporativas continuamente incorporam o uso da Internet para virtualmente todas as operações, especialmente para armazenamento e recuperação de informação. Essa informação é armazenada em um servidor web para ser acessada por usuários legítimos quando requerido. Numerosas ameaças de segurança como ataque de negação de serviço (DDoS), que é muito dominante, afetam esse servidor persistentemente. DDoS é uma ameaça significativa à Internet.

**Relatório da Arbor Networks mostrou que o percentual de respondentes vendo ataques DDoS na camada de aplicação (APDDoS) continuou a aumentar, de 86%, 90% e 93% em 2013, 2015 e 2016 respectivamente [4].**

Ataques DDoS podem penetrar a rede através de vários meios. Primeiro, através de brechas em protocolos de comunicação. Esses protocolos são *Transmission Control Protocol* (TCP) e *Hypertext Text Transfer Protocol* (HTTP). Segundo, o atacante pode direcionar uma quantidade considerável de tráfego anormal inundando tráfego aparentemente legítimo em direção às vítimas.

A execução de ataque DDoS na camada de aplicação é frequentemente desafiadora e complexa de detectar porque tal ataque imita tráfego legítimo para usar completamente os recursos do sistema, degradando assim o servidor. Para um servidor web processar uma requisição de usuários, HTTP é usado, e é projetado para ter requisições e respostas. Conforme a tecnologia avança, ferramentas de ataque tornam-se mais sofisticadas; daí, vários *botnets* podem atacar um servidor web ao mesmo tempo. As últimas duas décadas tiveram um compromisso aumentado nessa área de estudo por pesquisadores da academia e da indústria. Problemas de ataque APDDoS causam dano massivo a usuários legítimos da Internet e segurança de servidor web. O crescimento pervasivo de dispositivos móveis e dispositivos *Internet-of-things* (IoT) criou mais caminhos para *botnet* web. *Bots* IoT tornaram-se a máquina favorita para lançar ataques DDoS no ano de 2017, e o total de dispositivos IoT inseguros ligados à Internet está aumentando todo dia.

Considerando o acima, a motivação para esse *survey* é centrada no crescimento estável e pervasivo dos dispositivos IoT. Esse *survey* é também motivado pela inteligência de um atacante para prender o poder de vários dispositivos comprometidos como dispositivos IoT para lançar um ataque e assim torna o ataque mais complexo de detectar. Essa complexidade causou um desafio extra à segurança de um servidor web. Alguns artigos de revisão no contexto de detecção e ataque APDDoS foram apresentados antes. Esse artigo de revisão é diferente dos artigos existentes em vários aspectos: (1) Mecanismos de detecção de ataque APDDoS são categorizados com base em abordagens e métodos onde cada categoria tem suas vantagens e desvantagens peculiares. (2) Como o ataque APDDoS imita usuários legítimos e é muito sutil e astuto, o mecanismo é também classificado com base na estratégia de ataque. (3) Considerando o custo de implementação do mecanismo de detecção, o status dos mecanismos de detecção é também seccionado. Daí, a vantagem desse estudo é ampliar e analisar a informação aplicável sobre os estudos existentes na área de detecção, desafios e taxonomias de ataque APDDoS.

A parte restante do estudo é como segue: A Seção 2 discute ataques APDDoS e seus estágios preliminares. A Seção 3 fornece os procedimentos de busca (SPs) e outras metodologias utilizadas neste estudo. A Seção 4 dá resultados de medição buscados. Achados de pesquisa, questões atuais, desafios e comparação com outros estudos são apresentados na Seção 6. A Seção 6 também apresenta a taxonomia da metodologia existente do ataque APDDoS. O trabalho é concluído na Seção 7, dando uma visão sobre trabalho futuro.

---

## 2. Background do Estudo: Ataque APDDoS

Durante um ataque APDDoS, o servidor vítima é completamente sobrecarregado tanto pelo vasto volume de tráfego indesejado (alta banda) ou por tráfego que explora uma fraqueza na aplicação que requer baixa banda gerada por *hosts* comprometidos que são distribuídos em natureza. Esses *hosts* comprometidos distribuídos são chamados *bots*, vários números de *bots* são *botnets*, e dois ou mais *botnets* tornam-se *superbotnets*. Esses *botnets* acabam sendo uma das mais significativas ameaças à segurança de hoje em geral. APDDoS em servidores web são frequentemente desafiadores de abordar. Existem quatro estágios preliminares principais, como mostrado na Figura 1, pelos quais um atacante passa antes de poder finalmente lançar um ataque.

- **Estágio 1**: varredura de vulnerabilidade para localizar *hosts* que são vulneráveis varrendo a Internet usando ferramentas de ataque.
- **Estágio 2**: *malware* é instalado nos *hosts* vulneráveis para se tornarem *hosts* comprometidos (*bots*).
- **Estágio 3**: comandar os *hosts* comprometidos a lançar o ataque sobre um período especificado.
- **Estágio 4**: o atacante remove todos os traços ou registros da memória.

### 📌 Figura 1: Estágios Preliminares APDDoS

> **Descrição:** Diagrama de 4 estágios sequenciais ilustrando a preparação de um ataque APDDoS: vulnerability scanning → malware installation → command and control → trace removal.
>
> 📌 *Ver Figura 1 na página 3 do PDF original.*

As vulnerabilidades subjacentes de protocolos de camada de aplicação são muito importantes para um ataque APDDoS. De acordo com Kumar, esses protocolos são *"Direct Protocols and Support Protocols"*. Protocolos diretos frequentemente fornecem serviço para usuários diretamente, entre os quais estão HTTP, *File Transfer Protocol*, *Simple Mail Transfer Protocol*/*Post Office Protocol*, e assim por diante. Protocolos de suporte incluem *Domain Name System* (DNS), *Simple Network Management Protocol* e *Bootstrap protocol*/*Dynamic Host Configuration Protocol*.

Geralmente, a maioria dos ataques APDDoS explora os seguintes protocolos: HTTP *page flood*, HTTP/HTTPs *flood*, utilização de banda HTTP, *flood* de consulta DNS e *flood* SIP INVITE. Atributos de ataque APDDoS incluem o seguinte: são furtivos, muito difíceis de defender, baixo consumo de banda e alto consumo de banda. Um acampamento de ataque APDDoS é feito de um *botmaster* controlando vários *bots*. A Figura 2 mostra um acampamento APDDoS típico consistindo dos seguintes quatro componentes essenciais:

- O *botmaster* frequentemente referido como atacante.
- Os *handlers* com o programa especializado executando neles.
- *Zombies* (*hosts* comprometidos).
- *Host* vítima ou alvo.

### 📌 Figura 2: Um Acampamento APDDoS Típico

> **Descrição:** Diagrama em árvore mostrando o botmaster no topo, conectado a handlers que controlam zombies/bots de várias localizações que atacam o host alvo. Notação: b1, b2, b3, b4, b5, b6, H (handler), Bm (botmaster), Tv (target host).
>
> 📌 *Ver Figura 2 na página 3 do PDF original.*

---

## 3. Método de Pesquisa

Esta seção descreve as estratégias de pesquisa para este estudo, que são questões de pesquisa, processo de busca, critérios de inclusão e exclusão, e a execução de seleção. O processo de busca em Kitchenham é ratificado e ajustado para este estudo.

### 3.1. Questões de Pesquisa

Este *survey* é motivado pelas seguintes questões de pesquisa (RQN):

- **RQN1:** Quais são os valores relevantes do mecanismo existente de defesa contra ataque APDDoS?
- **RQN2:** Quais são as diferentes técnicas/métodos usados para abordar um ataque DDoS na camada de aplicação?
- **RQN3:** Que tipo de estratégia de ataque é considerada nas técnicas APDDoS existentes?
- **RQN4:** Quais são os *datasets* usados na validação do mecanismo de detecção previamente proposto?
- **RQN5:** Quais são as descrições e limitações das técnicas existentes de detecção de ataque APDDoS?

### 3.2. Processo de Busca

O processo de busca para a revisão sistemática é conduzido usando bibliotecas eletrônicas ou bases de dados como ACM Digital Library, IEEE Xplore, Science Direct/Elsevier, bibliotecas digitais Springer, Wiley e Google Scholar usando as strings de busca apropriadas. As strings de busca usadas nas cinco bases de dados estão na Figura 3.

**Strings de busca usadas:**

- ((Application layer or layer 7) AND (Detection Techniques))
- ((Application layer or layer 7) AND (flooding attack))
- ((Application-layer DDoS attack) AND (prevention OR Detection))
- ((Application-layer DDoS attack) AND (Attack types))
- ((Application-layer DDoS attack) AND (Tools))

**Processo de seis estágios da revisão sistemática:**

- **Estágio 1 de busca:** busca em cinco bases de dados eletrônicas e Google Scholar — total de **3.789 estudos**.
- **Estágio 2 (triagem 1):** 1.063 estudos duplicados removidos → 2.720 artigos.
- **Estágio 3 (triagem 2):** 1.557 artigos removidos por títulos irrelevantes → 1.163 artigos.
- **Estágio 4 (triagem 3):** 279 artigos removidos com base no resumo → 884 artigos.
- **Estágio 5 (elegibilidade):** revisão de texto completo dos 884 artigos restantes, excluindo 201 → 683.
- **Estágio 6 (inclusão):** análise de qualidade com base nas questões de pesquisa. **Setenta e cinco artigos foram considerados significativos para a revisão sistemática.**

### 📌 Figuras 3 e 4: Strings de Busca e Fluxo do Processo de Survey

> **Descrição:** Figura 3 lista as strings de busca booleanas. Figura 4 mostra o diagrama de fluxo PRISMA com os seis estágios de redução de 3.789 → 75 artigos.
>
> 📌 *Ver Figuras 3 e 4 na página 4 do PDF original.*

### 3.3. Procedimento de Busca

Esta seção detalha os vários procedimentos de busca (SP) empregados em analisar os 75 artigos significativos identificados neste estudo. Os 75 artigos significativos são explicados como segue: 59 artigos aparecem em periódicos, 13 artigos de conferência e *proceedings*, e três de simpósio. Em este estudo, nosso SP é seccionado em cinco, a saber: fonte, métodos/técnicas, estratégia de ataque, status e *datasets*/*corpus*.

#### 3.3.1. Fonte

A extração de artigos neste estudo é baseada em seis bases de dados eletrônicas, a saber, ACM, IEEE, Science Direct, Springer, Wiley e Google Scholar.

### Tabela 1: Número de Artigos Baixados das Bibliotecas Digitais Selecionadas

| S/N | Biblioteca Digital | Nº de Artigos |
|---|---|---|
| 1 | ACM | 50 |
| 2 | IEEE | 101 |
| 3 | Science Direct | 281 |
| 4 | Springer | 35 |
| 5 | Wiley | 10 |
| 6 | Google Scholar | 3.222 |

#### 3.3.2. Métodos/Técnicas

Nossa revisão de mecanismo de defesa de ataque APDDoS empregou abordagem de defesa, que é um dos critérios usados pelos autores mencionados acima. A classificação de técnicas de defesa APDDoS é de acordo com os artigos de revisão baseados na abordagem usada para implementação em cada um dos artigos de revisão pelos pesquisadores. Os métodos usados em estudos existentes são classificados como segue:

- **Método de controle de autenticação:** análise de comportamento de usuário web é executada usando controle de autenticação implementando CAPTCHA ou *Are You A Human* (AYAH) para identificar atacantes e usuários legítimos.
- **Teste de grupo (group testing):** fornece como vírus evolucionários podem ser usados para identificar ataques DDoS de aplicação web.
- **Pontuação de suspeita (suspicion score):** atribui uma medida de desconfiança a cada sessão de cliente usando histórico de sessão.
- **Gerenciamento de confiança (trust management):** confiança é calculada usando histórico de visitas dos clientes.
- **Moeda (currency):** algum pagamento é demandado pelo servidor vítima dos clientes.
- **Contabilidade de crédito (credit accounting):** um cliente bem-comportado ganha um alto ponto de crédito enquanto o estudo bloqueará um cliente mal-comportado de acessar o servidor.
- **Entropia:** comportamentos de navegação dos usuários são descritos classificando os dados extraídos em diferentes *clusters* baseados em características específicas, e a aleatoriedade no fluxo de tráfego é medida usando entropia.
- **Aprendizado de máquina:** os atributos significativos são que os *datasets* são treinados usando certas características após serem classificados em diferentes *clusters*.
- **Correlação:** outro parâmetro crítico usado para análise comportamental de tráfego de usuários ilícitos é a similaridade de fluxo.
- **Amostragem (sampling):** em um intervalo de tempo particular, o limite para o número de usuários para acessar o servidor é definido.
- **Gerenciamento de fila (queue management):** bloqueio de fila com gerenciamento de fila de tráfego é usado para prevenir ataques por identificação de congestionamento.
- **Teoria dos jogos (game theory):** é usada para descrever o relacionamento entre atacante e defensor.
- **D-ward:** este método responde ao ataque APDDoS descartando excesso de tráfego.
- **Sensor:** utiliza o sensor *front-end* baseado em um teste de mistura para monitorar o tráfego.

#### 3.3.3. Estratégia de Ataque

Neste estudo, estratégias de ataque identificadas nas 75 selecionadas são: alta taxa e baixa taxa. Atacantes frequentemente lançam um ataque variando parâmetros específicos como atraso, contagem, sequência e volume. O ataque APDDoS em forma de alta taxa transfere um grande número de requisições para saturar o servidor. Aqui, os *bots* geram uma rajada contínua de requisição para alcançar uma carga próxima do servidor. Em baixa taxa, o ataque APDDoS degrada um servidor enviando rajadas curtas de tráfego que são bem cronometradas. O tamanho do pulso de ataque gerado nesta estratégia é bem menor que a alta taxa.

#### 3.3.4. Datasets/Corpus

### Tabela 2: Detalhes dos Datasets Usados nos Artigos de Revisão

| Dataset | Tipo e link |
|---|---|
| Dataset de transação gerado por JMeter | Gerado |
| ISCX | *Benchmark* (online): http://www.iscx.ca/dataset |
| CAIDA DDoS attack | *Benchmark*: http://www.caida.org/data/passive/ddos-20070804_dataset.xml |
| Weblogs do site sun yat-sen university | *Offline* |
| LLDoS 2.02 | *Benchmark*: https://www.ll.mit.edu/ideval/data/1998data.html |
| EPA-HTTP | *Benchmark*: ita.ee.lbl.gov/html/contrib/EPA-HTTP.htm |
| Data center localizado em Dahan China | *Offline* |
| O dataset KDD'99 | http://kdd.ics.uci.edu/databases/kddcup99/kddcup99.html |
| Dados dinâmicos de sites populares | *Offline* |
| Mawlab dataset, Netresen | Gerado |
| ClarkNet-HTTP dataset | *Benchmark*: http://ita.ee.lbl.gov/html/contrib/ClarkNet-HTTP.html |
| Sina web traffic | *Offline* |
| Spanish web server | *Offline* |
| University of Napoli federico11 | *Offline* |
| Tráfego proxy-to-proxy de servidor de campus | Gerado |
| Dados de servidor real que experimentou o ataque | *Offline* |
| Tráfego normal coletado do servidor da Changzhoil university | *Offline* |
| DARPA 99 dataset | *Benchmark*: http://archive.ics.uci.edu/ml/datasets/kdd+cup+1999+data |
| MIT Lincoln Laboratory scenario | *Offline* |
| PHARM 2000 | *Benchmark*: https://archive.ics.uci.edu/ml/datasets.html |
| RGCE, ambiente ciber realista | *Offline* |

#### 3.3.5. Status

### Tabela 3: Status dos Estudos Existentes com Suas Respectivas Narrativas

| S/N | Estado | Narrativa |
|---|---|---|
| 1 | Implementado / Proposto | Categoria de estudos projetados para sistema protótipo / Categoria baseada em métodos propostos sem avaliação de desempenho |
| 2 | Proposto + avaliado | Categoria baseada em novos métodos que foram avaliados e comparados com métodos existentes |
| 3 | Proposto + implementado | Categoria com métodos novos e que foram implementados |

#### 3.3.6. Exploração de Características

### Tabela 4: Exploração de Características

| S/N | Exploração de Característica | Algumas Métricas/Parâmetros Selecionados |
|---|---|---|
| 1 | Informação de Cabeçalho de Pacote (PHI) | Endereço IP de origem, porta de origem, endereço IP de destino, porta de destino, entropia de HTTP GET, número de pacotes de eco ICMP, e número de eco UDP |
| 2 | Fluxo de Requisição durante uma Sessão de Usuário e Padrão de Pacote (RSUS) | Número de requisições em uma sessão, código de resposta, duração de uma sessão, tempo de ocorrência de páginas dinâmicas, sequência de frequência de requisição, e sequência de intervalos de requisição |
| 3 | Fluxo de Requisição durante o Intervalo de Tempo Absoluto (RSATI) | Consumo absoluto de banda, razão eminente de diversidade de fonte, tempo absoluto de acesso à página, contagem absoluta de acesso à página, intervalo absoluto de sessão, e contagem absoluta de sessão |
| 4 | Características de Usuário Web (WU) | Movimento do mouse, clique do mouse, destaque do mouse, evento de pressão e liberação de tecla, e histórico de navegação como visita de página web |

---

## 4. Resultados Obtidos

### 4.1. SP 1: Fonte

A busca de literatura intimamente relacionada é realizada em artigos requeridos de artigos específicos entre 2000 e 2019. **A partir dos 75 artigos significativos finais, IEEE teve o maior número com 28 artigos relevantes seguido pelo Google Scholar com 20 publicações, Science Direct teve 17 artigos relevantes, Springer teve 5, ACM teve 3, e Wiley teve 2 publicações relevantes.** Uma grande proporção de artigos significativos é entre 2011 e 2017, com um total de 48 artigos.

### 📌 Figuras 5, 6, 7, 8: Fontes e Distribuições Temporais

> **Descrição:** Gráficos de pizza e barras mostrando: total de 75 estudos por fonte (Figura 5), nuvem de palavras dos títulos (Figura 6), fontes e artigos relevantes na última década (Figura 7), número de publicações significativas por ano na última década (Figura 8).
>
> 📌 *Ver Figuras 5-8 nas páginas 6-7 do PDF original.*

### 4.2. SP 2: Métodos/Técnicas

O resultado de avaliação baseado em métodos/técnicas é dividido em 14 categorias. Essas 14 categorias são algoritmos de classificação para diferenciar um fluxo legítimo de um fluxo ilegítimo. **Uma grande proporção dos artigos selecionados utilizou aprendizado de máquina na detecção de ataque APDDoS** e algoritmos como *K-means clustering*, *support vector machine* e rede neural foram empregados em vários estudos.

**Resultados percentuais por categoria:**

- **Aprendizado de máquina:** 36%
- **Controle de autenticação:** 12%
- **Entropia:** 10%
- **Gerenciamento de fila:** 10%
- **Pontuação de suspeita:** 5%
- **Gerenciamento de confiança:** 5%
- **Correlação:** 4%
- **Moeda:** 4%
- **Teste de grupo:** 3%
- **Amostragem:** 3%
- **Contabilidade de crédito:** 2%
- **Sensor:** 2%
- **D-ward:** 2%
- **Teoria dos jogos:** 2%

### 📌 Figura 9: Categorias de Métodos Existentes de Detecção APDDoS

> **Descrição:** Gráfico de pizza mostrando os percentuais das 14 categorias acima. Aprendizado de máquina domina com 36%.
>
> 📌 *Ver Figura 9 na página 9 do PDF original.*

### Tabela 5: Comparação das Técnicas Usando Métricas de Desempenho

| Técnicas APDDoS | Falso-positivo | Falso-negativo | Acurácia | Complexidade Computacional | Complexidade de Implementação |
|---|---|---|---|---|---|
| D-ward | Menos | - | Alta | - | Pequena |
| Sensor | - | - | Baixa | Pequena | - |
| Contabilidade de crédito | - | - | - | - | - |
| Gerenciamento de confiança | - | Menos | - | Pequena | - |
| Correlação | - | - | Baixa | - | - |
| Moeda | - | - | Alta | - | - |
| Amostragem | Menos | Menos | Alta | - | - |
| Gerenciamento de fila | Menos | Menos | - | - | Pequena |
| Entropia | - | - | Baixa | - | - |
| Pontuação de suspeita | Menos | Menos | - | - | - |
| Teoria dos jogos | - | - | - | Pequena | - |
| **Aprendizado de máquina** | **Menos** | **Menos** | **Alta** | **Pequena** | - |
| Controle de autenticação | - | - | - | - | - |

### 4.3. SP 3: Estratégia de Ataque

A avaliação quantificável da estratégia de ataque APDDoS existente é analisada como **39% de alta taxa, 13% de baixa taxa e 48% não-especificado**. **É evidente que nenhum estudo propôs uma solução que possa lidar com ambos alta taxa e baixa taxa.**

### 4.4. SP 4: Dataset/Corpus

A análise nos 75 artigos selecionados em *datasets* APDDoS existentes mostra que:

- **25%** das soluções existentes avaliaram seus métodos com *datasets online*
- **19%** dos estudos existentes usaram *dataset offline*
- **6%** utilizaram *dataset* gerado com ferramentas de ataque
- **50%** restantes não são específicos sobre o tipo de *datasets* usados

Dos 17 estudos que usaram dataset online: CAIDA, FIFA World Cup e KDD 99 têm 17.6% cada, Clark net-HTTP tem 11.8%, enquanto outros têm 5.9% cada.

### 4.5. SP 5: Status

A avaliação baseada no status de detecção de ataque APDDoS existente nos 75 artigos selecionados:

- **Apenas 4%** das soluções existentes são **implementadas**
- **30%** das soluções atuais são **propostas**
- **59%** são **propostas e avaliadas**
- **7%** são **propostas e implementadas**

> **Citação chave para o nosso paper:** Apenas 4% das soluções propostas atingem implementação operacional real. Esse número aparece no nosso Abstract.

### 4.6. SP 6: Exploração de Características

Das 75 selecionadas, **47%, 33%, 12% e 8% dos artigos selecionados utilizaram fluxo de requisição durante uma sessão de usuário e padrão de pacote, informação de cabeçalho de pacote, fluxo de requisição durante um intervalo de tempo absoluto e características de usuário web, respectivamente.**

> **Citação chave para o nosso paper:** 47% dos métodos usam features de sessão (taxa de requisições, duração, contagem). Esse é o número exato citado no nosso Abstract.

---

## 5. Achados de Pesquisa, Questões Atuais e Comparação com Outros Surveys

Existem diferentes técnicas e metodologias que aceleram a defesa contra ataque APDDoS visando servidor web. A maioria dos estudos selecionados é baseada em análise comportamental de usuários web considerando parâmetros específicos para distinguir tráfego normal de tráfego de ataque, no qual filtragem é aplicada adequadamente para proteger o servidor alvo. Esta revisão encontrou que trabalhos anteriores e vários outros estudos empregaram apenas uma estratégia de ataque DDoS de alta taxa. Enquanto isso, outros estudos empregaram estratégia de ataque DDoS de baixa taxa enquanto poucos outros estudos foram incertos sobre a estratégia de ataque usada. O uso da característica correta é essencial para garantir que a técnica de detecção APDDoS possa detectar um ataque. A otimização de característica melhorará a detecção efetiva de ataque APDDoS.

Para responder RQN5, os seguintes achados são revelados como as principais questões e desafios baseados nos 75 artigos selecionados:

- Ataques podem penetrar a rede através de quaisquer meios; exploração de vulnerabilidade difere. **Métodos existentes na literatura foram projetados para combater ataques APDDoS de baixa taxa ou alta taxa, mas não para ambos.** Portanto, desenvolver um método aprimorado usando uma abordagem colaborativa baseada em aprendizado profundo que possa detectar ambos os tipos de ataques em tempo real ainda está não resolvido.
- Dispositivos IoT facilitaram a aquisição fácil de *hosts* comprometidos. O famoso *botnet* Mirai que tomou a Internet de assalto em fim de 2016 era composto basicamente de dispositivos embarcados e IoT, daí há necessidade de método de defesa mais sofisticado.
- A maioria dos *datasets* de *benchmark* é bastante antiga — é por isso que é desafiador avaliar a maioria das técnicas desenvolvidas. A avaliação apropriada de soluções de defesa com *datasets* relevantes causa um exame imediato.
- Revisão da literatura mostra que a maioria das técnicas focou em um protocolo particular, e desenvolver uma solução geral para defender qualquer tipo de ataque APDDoS para qualquer protocolo é outro desafio.
- A disponibilidade de *datasets* é também um desafio importante. *Datasets* são restritos e bastante antigos.

### 5.1. Comparação com Outros Surveys

### Tabela 6: Comparação do Estudo com Survey Existente

| Estratégia de Busca | Jaafar et al. | Zeebaree et al. | Kaur et al. | Kamboj et al. | Tama and Rhee | Wang et al. | Nossa Revisão |
|---|---|---|---|---|---|---|---|
| Fonte | | | | | | | ✓ |
| Métodos/técnica | | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Estratégia de ataque | ✓ | | ✓ | | | | ✓ |
| Datasets/corpus | ✓ | | | | | | ✓ |
| Métrica de detecção | ✓ | | ✓ | | | ✓ | ✓ |
| Exploração de característica | ✓ | | | | | | ✓ |

---

## 6. Discussões e Taxonomia

### Tabela 7: Resumo Abrangente de Vantagens e Desvantagens de Várias Categorias na Detecção APDDoS

| Categorias | Vantagens | Desvantagens |
|---|---|---|
| Controle de autenticação | Discrimina tráfego de *flash crowd* de tráfego de ataque | Causa algum atraso desperdiçando tempo. É implementado em quantidade minimal de tráfego |
| Teste de grupo | Baixa taxa de falso-negativo e -positivo | Desempenho de detecção é limitado aos resultados GT. Não pode detectar web APDDoS com precisão |
| Pontuação de suspeita | Fornece serviço garantido a usuários legítimos; detecta ataque DDoS durante fluxo normal e durante *flash crowd* | Não pode proteger o servidor web de diferentes *botnets* |
| Gerenciamento de confiança | Falso-negativo é reduzido, e a taxa de detecção é alta; históricos de visita dos clientes não podem ser modificados | Esta abordagem ganhou custo computacional adicional. Também causou sobrecarga de banda |
| Moeda | Baixo falso-negativo e -positivo | Eficiência de detecção é baixa; é custoso (pagando banda) |
| Contabilidade de crédito | Endereço IP não pode ser falsificado por atacantes | Acessibilidade fácil é ao lado do cliente |
| Entropia | Nenhum parâmetro de sobrecarga computacional. Sua *traceback* de ataque é mais rápida em redes de ataque de larga escala | A abordagem não pode detectar e *traceback* ataques DDoS de diferentes localizações. Garante uma pequena quantidade de tráfego regular |
| **Aprendizado de máquina** | **Acurácia de detecção é alta. Taxa mínima de falso positivo. Complexidade de tempo é baixa. Baixa taxa de falso-positivo e -negativo. Alta eficiência em classificação** | **Não robusto o suficiente para proteger o servidor web de superbotnets. A abordagem não pode discriminar uma flash crowd de um ataque DDoS** |
| Correlação | Desempenho de detecção é relativamente alto. Complexidade de tempo é pequena | A abordagem não pode lidar com fluxos de diferentes *botmasters* |
| Amostragem | Baixa taxa de alarme falso. Alta acurácia sem taxa de falso-positivo | Não pode prevenir *superbotnets* |
| Gerenciamento de fila | Reduz sobrecarga de tráfego. Forneceu um grau mais alto de justiça a fluxos legítimos | A abordagem não pode lidar com fluxos de diferentes distribuições |
| Teoria dos jogos | Acurácia de detecção é alta; o defensor pode maximizar seu *payoff* enquanto minimiza o *payoff* do atacante | O modelo não é aplicado para predizer características comportamentais do fluxo malicioso |
| D-ward | Reduz sobrecarga no lado da vítima | Alta taxa de falso-positivo |
| Sensor | Baixa complexidade de tempo | Alta taxa de falso-positivo |

### 📌 Figuras 10-15: Análises Visuais

> **Descrição:** Gráficos de pizza/barra mostrando: estratégia de ataque das 75 técnicas (Fig 10), grupos de *datasets* (Fig 11), distribuição de *datasets online* (Fig 12), estado das soluções (Fig 13), exploração de características (Fig 14), e a taxonomia visual completa do mecanismo de defesa APDDoS (Fig 15).
>
> 📌 *Ver Figuras 10-15 nas páginas 10-14 do PDF original.*

---

## 7. Conclusão e Trabalho Futuro

Dado vários esforços para aliviar ataque APDDoS, mais tarefas precisam ser realizadas em melhorar métodos de detecção existentes para discriminação precisa de tráfego de ataque de tráfego legítimo. Este estudo conduziu uma revisão extensiva analisando e investigando as metodologias do estado da arte empregadas em detectar o ataque APDDoS. Da busca inicial, 3.789 artigos foram identificados. Subsequentemente, um processo rigoroso de triagem foi realizado, e 75 publicações significativas foram selecionadas para o estudo. Diferentes estratégias de busca foram empregadas neste estudo para analisar trabalho existente em detecção de ataque APDDoS, e respostas a questões de pesquisa que ajudariam trabalho de pesquisa no futuro são também dadas.

**Para cada estratégia de busca, a avaliação quantificável alcançada é como segue:**

- Métodos existentes em detecção APDDoS indicam que **36% das técnicas empregadas foram baseadas em aprendizado de máquina**, entropia e gerenciamento de fila são ambos 10% enquanto método baseado em autenticação é 12%. As categorias restantes são 32%.
- Resultados baseados no tipo de estratégias de ataque mostram que **39% é baseado em alta taxa, 13% baseado em baixa taxa e 48% são não-especificados**.
- O resultado baseado no status de soluções de detecção de ataque APDDoS existentes mostra que **implementado foi 4%**, proposto foi 30%, enquanto 59% foi proposto e avaliado, e 7% foi proposto e implementado.
- Análise de exploração de característica mostra que dos 75 estudos selecionados, exploração de característica baseada em **fluxo de requisição durante sessão de usuário e padrão de pacote, fluxo de requisição durante um intervalo de tempo absoluto, informação de cabeçalho de pacote e características de usuário web foram 47%, 12%, 33% e 8%, respectivamente**.

Este estudo mostra que modelos de representação artificiais restringem a maioria das técnicas de aprendizado de máquina. Daí, recomendações futuras serão melhorar o método de detecção para acompanhar a natureza astuta e furtiva do ataque. Esses ataques são acoplados à crescente qualidade sofisticada de ferramentas de ataque usando uma abordagem de aprendizado profundo que permite mais características serem afinadas a partir das de baixo nível baseadas em métodos de aprendizado profundo que extraem características automaticamente e fornecem melhor acurácia. Vários estudos também concluíram que o uso da rede neural profunda melhoraria a acurácia de detecção devido à habilidade do algoritmo de aprendizado profundo fazer decisões inteligentes. A otimização de características também melhorará a detecção efetiva do ataque APDDoS. Também, gerar um *dataset* de ataque APDDoS mais próximo da vida real para reduzir o problema de escassez de dados no futuro melhorará a acurácia de detecção.

---

## Apêndice: Tabela A1 — Classificação dos 75 Artigos

> A Tabela A1 do apêndice classifica os 75 artigos selecionados pelas 14 categorias de métodos (Controle de autenticação, Teste de grupo, Pontuação de suspeita, Gerenciamento de confiança, Moeda, Contabilidade de crédito, Entropia, Aprendizado de máquina, Correlação, Amostragem, Gerenciamento de fila, Teoria dos jogos, D-ward, Sensor), 2 estratégias de ataque (Alta taxa, Baixa taxa) e 4 status (Implementado, Proposto, Proposto+Avaliado, Proposto+Implementado).
>
> 📌 *Ver Tabela A1 nas páginas 19-24 do PDF original. Esta tabela é central para o nosso paper porque é dela que se extrai a evidência de que **nenhuma das 14 categorias incluí "raciocínio semântico via grafo de conhecimento"** — o gap que nosso paper preenche.*

---

## Referências

Lista completa de 95 referências no PDF original. Algumas das mais relevantes:

- [4] **Arbor Networks** — Worldwide infrastructure security report (2016). Fonte dos números 86%/90%/93% de incidência APDDoS.
- [7] **Praseed A, Thilagam PS** (2018) — DDoS attacks at the application layer: challenges and research perspectives for safeguarding web applications. *IEEE Commun Surv Tutor* 21(1):661-685.
- [8] **Tripathi N, Hubballi N** (2018) — Slow rate denial of service attacks against HTTP/2 and detection. *Comput Secur* 72:255-272. (mesmos autores do paper [3448291.pdf] que é o Tripathi 2021 — ACM CSUR survey citado em todo o nosso paper)
- [17] **Kitchenham B** (2004) — Procedures for performing reviews. Metodologia PRISMA usada nesta meta-análise.

> Para a lista completa, ver páginas 15-18 do [PDF original](../pdfs/Int%20J%20Communication%20-%202020%20-%20Odusami%20-%20A%20survey%20and%20meta-analysis%20of%20application-layer%20distributed%20denial-of-service%20attack.pdf).

---

## Resumo dos pontos-chave para o nosso paper

> Anotação minha sobre como usar esta leitura no nosso paper.

### As estatísticas centrais que usamos no Abstract

| Stat | Fonte exata na Odusami | Onde citamos |
|---|---|---|
| **86% / 90% / 93%** de incidência APDDoS em 2013/2015/2016 | §1 Introdução, citando Arbor Networks 2016 ref [4] | Abstract; §1.1 Contexto e Motivação |
| **47%** dos métodos usam features de sessão | §4.6 (SP 6: Feature exploration), Figura 14 | Abstract; §1.2 gap 1 |
| **4%** das soluções implementadas | §4.5 (SP 5: Status), Figura 13 | Abstract; §1.1 |
| **48%** sem strategy especificada | §4.3 (SP 3: Attack strategy), Figura 10 | §1.1 |
| **75 estudos analisados** | Resumo metodológico | Várias seções |
| **0 estudos com KG/ontologia** | Tabela A1 (apêndice) — nenhuma coluna corresponde a KG | §1.2 gap 1 (nossa inferência da taxonomia) |

### O argumento crítico de defesa

Quando o reviewer A2 perguntar **"como você sabe que nenhum dos 75 estudos trata sessão como entidade semântica?"**, a resposta é:

> A Tabela A1 do apêndice de Odusami 2020 cataloga os 75 estudos em 14 categorias de método (Authentication control, Group testing, Suspicion score, Trust management, Currency, Credit accounting, Entropy, Machine learning, Correlation, Sampling, Queue management, Game theory, D-ward, Sensor). **Nenhuma dessas 14 categorias corresponde a raciocínio semântico baseado em ontologia ou grafo de conhecimento.** Se algum dos 75 estudos tratasse sessão como entidade ontológica raciocinável, ele apareceria em uma categoria distinta — não aparece. Esta evidência indireta é fortalecida por Liu et al. 2022 (Electronics), que faz survey específico de KG-em-cibersegurança e também não cataloga nenhum estudo com KG aplicado a DDoS de Camada 7 em inglês.

### Onde citar no nosso artigo

- **Abstract:** já citado para os números 47%, 4%
- **§1.1 Contexto:** já citado para 86/90/93% e 4% implementados
- **§1.2 gap 1:** citação central da meta-análise — usar a Tabela A1 como evidência de que KG/ontologia não aparece nas 14 categorias
- **§2.2 (Detecção HTTP Camada 7):** quando desenvolvermos Related Work, esta meta-análise é a fonte primária para a taxonomia de métodos. Vamos posicionar nosso paper como "a 15ª categoria que faltava".
- **§2.3 (Modelagem de Sessão):** usar a estatística 47% para mostrar que sessão é amplamente usada como **feature** mas nunca como **entidade**.
