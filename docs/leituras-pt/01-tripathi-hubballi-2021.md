# Ataques de Negação de Serviço na Camada de Aplicação e Mecanismos de Defesa: Um Survey

> **Tradução integral em português** de *"Application Layer Denial-of-Service Attacks and Defense Mechanisms: A Survey"*, Tripathi e Hubballi (2021), ACM Computing Surveys 54(4), Artigo 86.
>
> **PDF original:** [`docs/pdfs/3448291.pdf`](../pdfs/3448291.pdf) — 33 páginas
> **DOI:** 10.1145/3448291
> **Status:** ✅ Tradução completa
> **Tier:** 1 (Leitura obrigatória — survey ACM CSUR canônico de Layer 7 DoS; fonte do "292.000 req/s por 13 dias" do nosso Abstract)

---

## Autores

**Nikhil Tripathi** — Fraunhofer Institute for Secure Information Technology, Darmstadt, Alemanha
**Neminath Hubballi** — Indian Institute of Technology Indore, Índia

---

## Resumo

Ataques de Negação de Serviço (DoS, do inglês *Denial-of-Service*) na camada de aplicação são gerados explorando vulnerabilidades da implementação do protocolo ou de seu *design*. Diferentemente de ataques DoS volumétricos, esses são furtivos por natureza e visam uma aplicação específica executando na vítima. Há vários ataques descobertos contra protocolos populares de camada de aplicação nos últimos anos. Neste artigo, fornecemos um *survey* estruturado e abrangente dos ataques DoS na camada de aplicação existentes e mecanismos de defesa. Classificamos os ataques existentes e mecanismos de defesa em diferentes categorias, descrevemos seu funcionamento e os comparamos com base em parâmetros relevantes. Concluímos o artigo com direções para pesquisa futura.

## Palavras-chave

DoS específicos de protocolo e genéricos, ataques DoS distribuídos, mecanismos de defesa.

---

## 1. Introdução

Ataques DoS e sua variante, Ataques de Negação de Serviço Distribuída (DDoS), têm sido motivo de séria preocupação para administradores de rede nas últimas duas décadas. Esses ataques visam exaurir os recursos (memória, ciclos de CPU e largura de banda da rede) e torná-los indisponíveis para usuários benignos, violando assim um dos principais componentes da cibersegurança — **Disponibilidade**. Lançar um ataque DoS tipicamente requer menos largura de banda da perspectiva do cliente malicioso e assim pode ser lançado usando um número muito pequeno de dispositivos. No entanto, lançar um ataque DDoS requer enviar uma inundação de pacotes para a vítima. Um cliente malicioso pode lançar um ataque DDoS usando dois métodos. No primeiro método, o cliente malicioso envia a inundação de pacotes usando endereços IP falsificados (por exemplo, ataques de amplificação/reflexão). No segundo método, o cliente malicioso controla um grande número de *bots* que são comprometidos usando *malware* e comanda esses *bots* a enviar a inundação de pacotes para a vítima.

Grupos de *hacking* têm vários motivos por trás do lançamento desses ataques. Esses variam de simplesmente obter reconhecimento nas comunidades *underground* aos incentivos dados por organizações para lançar esses ataques contra seus potenciais concorrentes no mercado. Os bem conhecidos ataques DDoS de camada de rede/transporte visam equipamento e infraestrutura de rede para perturbar a conectividade da vítima.

Recentemente, uma nova classe de ataques DoS conhecida como **ataques DoS na camada de aplicação** começou a ganhar popularidade. Esses ataques exploram potenciais falhas e vulnerabilidades presentes nos protocolos de camada de aplicação. Essas vulnerabilidades são frequentemente consequências de esforços inadequados por designers e desenvolvedores em direção ao desenvolvimento seguro de protocolos. Projetar protocolos seguros nem sempre é considerado igualmente importante comparado à funcionalidade (por exemplo, HTTP 2.0 vs 1.1). Isso deixa para trás uma grande superfície de ataque que é então usada por adversários para lançar ataques DoS na camada de aplicação. **Esses ataques podem derrubar um servidor com enorme poder computacional e largura de banda de rede usando recursos muito limitados.** A maioria dos ataques DoS na camada de aplicação tipicamente requer apenas um computador para criar um cenário DoS no lado da vítima. Assim, esses ataques são geralmente considerados como pertencentes à categoria DoS (em vez da categoria DDoS) a menos que declarado de outra forma. Os ataques DoS na camada de aplicação visam serviços específicos na vítima com implicação minimal em recursos de rede. Esses ataques visam impedir ou um servidor de servir clientes legítimos ou os clientes individuais de acessar um recurso disponível em um servidor.

Os ataques DoS na camada de aplicação são conhecidos por gerar menos tráfego em comparação com ataques DDoS de camada de rede/transporte, e assim são mais furtivos. Mitigar esses ataques modificando a operação de um protocolo não é viável, pois requer modificações nos RFCs correspondentes, o que é um processo trabalhoso e precisa de deliberações e discussões entre as partes interessadas.

**Tendências e incidentes recentes.** De acordo com o *2019 Global DDoS Threat Landscape Report* da Imperva, **o maior ataque DoS na camada de aplicação na história foi registrado em 2019. Este ataque durou 13 dias e atingiu pico de 292.000 requisições por segundo.** Além disso, conforme outro relatório, **o número de ataques DoS/DDoS na camada de aplicação está dobrando após cada trimestre de um ano**, embora o número de assaltos na camada de rede no quarto trimestre de 2017 tenha diminuído em uma margem enorme de 50% do terceiro trimestre de 2017.

A popularidade de ataques DoS na camada de aplicação é refletida de outro fato: há vários incidentes onde esses ataques foram encontrados. Além de tais incidentes reportados, há vários incidentes desses ataques devido a ameaças internas que não são reportadas pelas organizações vítimas temendo publicidade negativa. **De acordo com um relatório de Ameaça Interna de 2018, 53% das organizações confirmaram ataques internos contra elas apenas no ano passado.**

### Tabela 1: Incidentes de Ataque DDoS na Camada de Aplicação

| Ano | Alvo | Escala | Ataque | Impacto |
|---|---|---|---|---|
| 2020 | Site de registro de eleitor estadual | ≈200.000 requisições DNS | DNS flood | Não divulgado |
| 2019 | Cliente Imperva (nome não divulgado) | **292.000 requisições por segundo** | Não divulgado | Não divulgado |
| 2019 | Site da National Union of Journalists das Filipinas | 76 Gbps | HTTP flood | Site ficou offline |
| 2018 | Três bancos: ABN AMRO, ING e Rabobank | Não divulgado | Não divulgado | Disrupção de serviços bancários móveis |
| 2017 | Site Bitcoin gold | 10M requisições por minuto | HTTP flood | O site caiu |
| 2017 | Sites do governo espanhol | Não divulgado | HTTP flood | Sites do tribunal constitucional ficaram offline |
| 2017 | Serviços de transporte suecos | Não divulgado | HTTP flood | Atraso de trens e disrupção de viagens |
| 2016 | Sistemas de aquecimento da Finlândia | Não divulgado | DNS flood | Sistemas de aquecimento pararam |
| 2016 | Site do banco HSBC | Não divulgado | HTTP flood | Ataque mitigado com sucesso |
| 2016 | Sites dos Jogos Olímpicos do Rio | Não divulgado | HTTP flood | Vários sites negaram acesso |
| 2016 | Infraestrutura DNS da DYN | Não divulgado | DNS flood | Etsy, GitHub, Spotify, Twitter sofreram interrupções |
| 2016 | Infraestrutura de Internet da Libéria | Não divulgado | Não divulgado | Internet no país caiu |
| 2015 | Site do GitHub | Não divulgado | HTTP flood | GitHub conseguiu superar o ataque |
| 2014 | Site de mídia de Hong Kong | 250M requisições DNS/seg | DNS flood | Campanha por sistema democrático afetada |
| 2012 | Infraestrutura web de vários bancos | 63,3 Gbps | HTTP flood | Acesso a banking online e móvel afetado |
| 2009 | Campanha eleitoral presidencial iraniana | Não divulgado | Slowloris | Não divulgado |

### Contribuições deste Survey

(1) Apresentamos um *survey* abrangente de ataques DoS na camada de aplicação e classificamos eles dependendo se são efetivos contra um protocolo específico ou um grande número de protocolos.

(2) Discutimos o funcionamento de ataques e os comparamos com base em diferentes parâmetros. Também descrevemos ferramentas/utilitários/bibliotecas que podem ser usadas para lançar os ataques.

(3) Revisamos vários mecanismos de defesa conhecidos para combater diferentes ataques DoS na camada de aplicação e os classificamos com base em seu princípio de funcionamento. Também descrevemos as forças e fraquezas de cada mecanismo de defesa.

(4) Comparamos vários produtos populares comerciais de mitigação DoS com base em sua habilidade de combater diferentes ataques.

(5) Em direção ao fim do artigo, fornecemos várias direções para pesquisa futura neste domínio.

### 📌 Figura 1: Categorização de Ataques DoS na Camada de Aplicação

> **Descrição:** Diagrama hierárquico mostrando dois grandes ramos: **(A) Ataques específicos de protocolo** (DHCP starvation attacks → Classical/Induced; NTP timeshifting/timesticking → Deja Vu/On-Path Timeshifting/Off-Path DoS/Off-Path Timeshifting; Slow HTTP DoS → Slow Header/Slow Message Body/Slow Read/HTTP PRAGMA) e **(B) Ataques genéricos** (Slow Rate Generic DoS → SlowReq/Slowcomm/Slow Next/SlowDrop; Request Flood → HTTP Flood/SIP Flood/DNS Flood).
>
> 📌 *Ver Figura 1 na página 4 do PDF original.*

---

## 2. Surveys Anteriores

Ataques DoS, em geral, têm sido conhecidos pela comunidade por bastante tempo, e portanto várias obras incluindo *surveys* foram publicadas na literatura. Há poucos trabalhos de *survey* onde os autores apresentaram uma taxonomia de diferentes tipos de ataques DoS. Zargar et al. apresentou uma análise abrangente de vários mecanismos de defesa para combater diferentes ataques como ataques de inundação HTTP e ataques Slowloris. Alguns dos *surveys* discutiram ataques DoS na camada de aplicação contra SIP. Em dois outros estudos recentes, os autores tentaram discutir os ataques DoS na camada de aplicação contra HTTP e outros protocolos relacionados a web. **Nosso survey difere dos surveys anteriores cobrindo aspectos de ataques não-volumétricos, cobrindo recentes ataques DoS na camada de aplicação e mecanismos de defesa, e tomando vários protocolos de camada de aplicação em conta.**

### Tabela 2: Comparação com Surveys Existentes

| Referências | Starvation | Timeshifting/Timesticking | Slow HTTP | Slow Rate | Request Flood | Mecanismos de Defesa Correspondentes |
|---|---|---|---|---|---|---|
| Praseed e Thilagam | ✗ | ✗ | ✓ | ✗ | ✓ | ✓ |
| Singh et al. | ✗ | ✗ | ✓ | ✗ | ✓ | ✓ |
| Keromytis | ✗ | ✗ | ✗ | ✗ | ✓ | ✓ |
| Zargar et al. | ✗ | ✗ | ✓ | ✗ | ✓ | ✓ |
| Geneiatakis et al. | ✗ | ✗ | ✗ | ✗ | ✓ | ✗ |
| Ehlert et al. | ✗ | ✗ | ✗ | ✗ | ✓ | ✓ |
| **Este Survey** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

---

## 3. Ataques DoS Específicos de Protocolo

Um ataque DoS específico de protocolo é efetivo apenas contra um protocolo de camada de aplicação particular. Exemplos de ataques específicos de protocolo são ataques de inanição DHCP, ataques DoS de *timeshifting*/*timesticking* NTP e ataques DoS HTTP Lentos.

### 3.1. Ataques de Inanição DHCP

DHCP é usado para automatizar as alocações de endereço IP aos clientes em uma rede. Um cliente, ao se juntar à rede, troca quatro mensagens DHCP, a saber *Discover*, *Offer*, *Request* e *Acknowledgment* com o servidor DHCP para obter um endereço IP. DHCP é conhecido por ser vulnerável a ataques de inanição DHCP devido à ausência de qualquer esquema de autenticação embutido.

**3.1.1. Ataque Clássico de Inanição DHCP:** Este ataque envolve enviar requisições falsas repetidamente (usando endereços MAC aleatórios falsificados) para consumir o *pool* de endereços IP. Uma vez consumido o *pool*, o servidor DHCP é incapaz de oferecer endereços IP aos novos clientes.

**3.1.2. Ataque Induzido de Inanição DHCP:** Este ataque explora esquemas de detecção de conflito IP presentes no lado do servidor e cliente. Para impedir o cliente de obter o endereço IP, um cliente malicioso simplesmente injeta uma resposta de sonda falsificada. Como resultado, conflito IP é detectado na rede.

**Ferramentas:** Os mais populares são Gobbler e DHCpig. Para o ataque induzido, ferramentas de *crafting* de pacotes como Scapy podem ser usadas.

#### 3.1.3. Mecanismos de Defesa

- **Técnicas Criptográficas:** impõem autenticação em DHCP, mas têm alta complexidade de implantação.
- **Recursos de Segurança em Switches:** *port security* e *Dynamic ARP Inspection* (DAI).
- **Usando DHCP Relay Agent:** o relé põe o ID e porta do switch nas mensagens DHCP.
- **Perfilamento de Tráfego DHCP:** Hubballi e Tripathi propuseram detecção comparando perfis de tráfego DHCP normal com perfis de teste usando Distância de Hellinger (HD).
- **Baseado em Aprendizado de Máquina:** algoritmos de classificação de uma classe.

### Tabela 3: Mecanismos de Defesa vs Ataques de Inanição DHCP

| Mecanismos de Defesa | Clássico | Induzido: 1ª Variante | Induzido: 2ª Variante | Induzido: 3ª Variante |
|---|---|---|---|---|
| Técnicas Criptográficas | ✓ | ✓ | ✓ | ✓ |
| Port Security | ✗ | ✗ | ✗ | ✗ |
| DAI | ✓ | ✗ | ✗ | ✗ |
| Usando DHCP Relay Agent | ✓ | ✗ | ✗ | ✗ |
| Perfilamento de Tráfego DHCP | ✓ | ✓ | ✓ | ✗ |
| Baseado em Aprendizado de Máquina | ✗ | ✗ | ✗ | ✓ |

### 3.2. Ataques de Timeshifting/Timesticking DoS Contra NTP

NTP é um dos protocolos mais antigos atualmente em uso na Internet. Foi projetado para sincronizar relógios de diferentes sistemas de computador conectados à Internet. Malhotra et al. recentemente divulgaram ataques *timeshifting*/*timesticking* que visam o funcionamento do protocolo NTP. Um relógio incorretamente sincronizado pode levar a falha de vários serviços centrais da Internet como DNS e *Resource Public Key Infrastructure*, resultando em DoS em larga escala.

**3.2.1. Deja Vu (On-Path Timesticking Attack):** Um cliente malicioso Man-in-the-Middle (MitM) entre um servidor *broadcast* NTP e um cliente vítima primeiro captura uma sequência contígua de pacotes *broadcast* e então a reproduz em intervalos regulares.

**3.2.2. On-Path Timeshifting Attack:** Um cliente malicioso envia mudanças de tempo pequenas e falsas, então quando pronto, envia uma grande mudança de tempo.

**3.2.3. Ataques DoS Off-Path:**
- **DoS por Kiss-o'-Death Falsificado:** atacante envia um KoD falsificado pelo cliente para cada servidor NTP pré-configurado.
- **DoS por Má Autenticação:** envia ao cliente vítima um pacote *broadcast* NTP mal autenticado falsificado.
- **Ataque Interleaved-Pivot:** cliente malicioso envia um único pacote falsificado para fazer o cliente vítima crer que o servidor está em modo *interleaved*.

**3.2.4. Ataques Off-Path Timeshifting:** Pinning to Bad Timekeepers e DoS usando IP Fragmentation.

#### 3.2.5. Mecanismos de Defesa

- **Técnicas Criptográficas:** desenvolvimento de NTPsec.
- **Redundância de Caminho:** múltiplos caminhos na Internet entre clientes e servidores NTP.
- **Redundância de Servidor:** Chronos — Deutsch et al. propuseram um novo cliente NTP que sincroniza com *pools* grandes de servidores.

### 3.3. Ataques DoS HTTP Lentos

HTTP é considerado um dos protocolos de camada de aplicação mais estudados contra ataques DoS. **Ataques DoS HTTP Lentos envolvem enviar requisições web especialmente criadas que interagem com o servidor muito lentamente.** A menos que uma requisição web seja completamente servida, o servidor mantém ela em uma fila de conexão com espaço limitado. Uma vez que essa fila esteja preenchida com requisições não-servidas, o servidor não atende mais requisições, resultando em ataque DoS.

**3.3.1. Slow Header ou Ataque Slowloris:** Um adversário envia requisições HTTP GET incompletas a um servidor web para exaurir o espaço da fila de conexão. Tripathi et al. avaliaram este ataque contra 100 sites ao vivo e mostraram que vários são vulneráveis.

**3.3.2. Slow Message Body Attack:** Requer enviar um cabeçalho completo de requisição POST mas um corpo de mensagem incompleto.

**3.3.3. Slow Read Attack:** Um adversário envia inicialmente uma requisição GET benigna e depois envia um pacote TCP anunciando tamanho de janela de zero *bytes*.

**3.3.4. HTTP PRAGMA Attack:** Explora um campo chamado PRAGMA no cabeçalho HTTP, que é usado por navegadores para solicitar ao servidor web enviar um recurso contra o qual o cliente já requisitou antes.

**Ferramentas:** Slowloris e SlowHTTPTest geram Slow Header. RUDY lança Slow Message Body.

#### 3.3.5. Mecanismos de Defesa

- **Módulos de Implementação:** Core, Antiloris, Limitipconn e mod_reqtimeout para Apache.
- **Comparando Perfis de Tráfego:** Tripathi et al. propuseram comparar perfil HTTP normal vs teste usando HD.
- **Monitorando Características de Tráfego:** Dantas et al. monitoram número de *bytes* enviados e recebidos por requisição.

### Tabela 7: Mecanismos de Defesa vs Ataques DoS HTTP Lentos

| Mecanismos | Slow Header | Slow Message Body | Slow Read | HTTP PRAGMA |
|---|---|---|---|---|
| Core | ✓ | ✓ | ✗ | ✗ |
| Antiloris | ✓ | ✓ | ✓ | ✓ |
| Limitipconn | ✓ | ✓ | ✓ | ✓ |
| mod_reqtimeout | ✓ | ✓ | ✗ | ✗ |
| Comparando Perfis | ✓ | ✓ | ✗ | ✗ |
| Monitorando Features | ✓ | ✓ | ✓ | ✓ |

---

## 4. Ataques DoS Genéricos

Diferentemente de ataques específicos de protocolo, esta classe de ataques DoS na camada de aplicação é efetiva contra um grande número de protocolos de camada de aplicação. Exemplos: **Slow Rate Generic** e **Request Flood**, que são efetivos contra HTTP, SMTP, FTP, SIP e DNS.

### 4.1. Ataques DoS Slow Rate Genéricos

Há quatro ataques DoS genéricos independentes de protocolo:

- **SlowReq/SlowDroid:** Aiello et al. propuseram que se pequenos pedaços de uma requisição (e.g., um *byte* cada) são enviados continuamente em intervalos regulares, o servidor alvo continua reiniciando o contador de *timeout* da conexão. Para Apache, isso força o servidor a manter a requisição na fila de conexão por ≈990 segundos. **Slowdroid** é uma variante para *smartphones*.
- **Slowcomm:** explora o conhecimento do *Retransmission Time Out timer* do TCP. Pode detectar fechamentos de conexão e estabelecê-las imediatamente novamente.
- **Slow Next:** usa características de conexão persistente de protocolos como HTTP, SMTP, FTP e SSH. O adversário estabelece várias conexões persistentes com o servidor e envia requisições benignas de cada conexão periodicamente.
- **SlowDrop:** primeiro requisita um grande recurso ao servidor e depois descarta os pacotes recebidos comportando-se como cliente não confiável.

#### Mecanismos de Defesa

- **Monitorando Características de Tráfego:** Mongelli et al. e Aiello et al. detectam contando o número de pacotes recebidos pelo servidor em um intervalo. Shtern et al. monitora a taxa de requisições enviadas por um cliente.

### 4.2. Ataques de Request Flood

Outra categoria de ataques DoS genéricos na camada de aplicação são ataques de Inundação de Requisição. Nesses ataques, um adversário envia uma inundação de requisições para um servidor vítima.

**HTTP Flood:** Tipo mais popular de ataque de inundação. Inclui HTTP GET e HTTP POST. **Repeated One Shot** ou **Asymmetric Workload Attack** envolve enviar uma pequena requisição especialmente criada de cada conexão estabelecida que causa o servidor web realizar tarefas intensivas em CPU.

**SIP Flood:** Caracterizado por enviar uma inundação de mensagens SIP para uma entidade SIP. Pode ser lançado enviando várias mensagens REGISTER, BYE ou INVITE.

**DNS Flood:** Um adversário envia uma inundação de consultas DNS para um servidor DNS para impedi-lo de processar e servir consultas de clientes benignos.

**Ferramentas:** HULK e LOIC para HTTP Flood; StarTrinity SIP Tester e inviteflood para SIP; DNS-flood-ng para DNS.

### 📌 Figura 3: Mecanismos de Defesa contra Ataques de Request Flood

> **Descrição:** Diagrama mostrando 4 categorias de defesa para HTTP Flood (Web Browsing Behavior, Monitoring Request Attributes, Entropy Evaluation, Challenge-based), 5 para SIP Flood (Cryptographic Techniques, Malformed Message Detection, Statistical Abnormality Measurement, Machine Learning, SIP Connection Modeling), e 3 para DNS Flood (Mapping DNS Requests/Responses, Extension to DNS, Changing Default Caching).
>
> 📌 *Ver Figura 3 na página 15 do PDF original.*

#### 4.2.1. Mecanismos de Defesa para HTTP Flood

**Analisando Comportamento de Navegação Web:** A maioria dos mecanismos de defesa para HTTP Flood cai nesta categoria. Modelam comportamento de navegação web normal usando diferentes características como **taxa de requisição, número de endereços IP de origem únicos encontrados em um intervalo de tempo, tamanho de pacote e sequência de acesso a página**. Ranjan et al. analisa Tempo de Chegada de Sessão, Tempo entre Chegadas de Sessão, e Tempo entre Chegadas de Requisição. Xie e Yu propuseram um Modelo Hidden semi-Markov (HsMM) estendido.

**Monitorando Atributos de Requisição:** Chwalinski et al. agrupa usuários em diferentes *clusters* usando K-means com base na contagem de requisição por recurso. Jazi et al. identifica mudanças no número de pacotes de requisição HTTP.

**Avaliação de Entropia:** Singh et al. usa Perceptron Multilayer com Algoritmo Genético de Aprendizado de Máquina (MLP-GA). Características: Variância de Entropia por Endereço IP, Entropia de Contagem de Requisição HTTP GET por Conexão.

**Baseado em Desafio:** CAPTCHA, AYAH. Ndibwile et al. usa três servidores web: real, isca e *decoy*. Zhang et al. usa banda de uplink do lado do cliente como desafio.

#### 4.2.2. Mecanismos de Defesa para SIP Flood

5 categorias: Técnicas Criptográficas, Detecção de Mensagem Malformada, Medidas Estatísticas de Anomalia, Aprendizado de Máquina, Modelagem de Conexão SIP.

#### 4.2.3. Mecanismos de Defesa para DNS Flood

3 categorias: Mapeamento de Requisições e Respostas DNS, Extensão ao DNS, Mudança de Comportamento Padrão de Cache de Registros DNS.

---

## 5. Comparando Diferentes Ataques DoS na Camada de Aplicação e Mecanismos de Defesa

Parâmetros para comparar ataques: complexidade de execução, alvo, sobrecarga de tráfego, furtividade, relevância (LAN ou Internet), spoofing, incidentes reais, tipo de ataque (DoS ou DDoS), DDoS-for-hire aplicável.

### Tabela 14: Comparação de Ataques DoS na Camada de Aplicação (resumo)

| Categoria | Ataque | Complex. | Alvo | Sobrecarga | Furtividade | Relevância | Spoofing? | Inc. Reais? | Tipo |
|---|---|---|---|---|---|---|---|---|---|
| DHCP | Induced Starvation | Baixa | Servidor | Baixa | Alta | LAN | Sim | Sim | DoS |
| DHCP | Classical Starvation | Alta | Servidor | Alta | Rel. Baixa | LAN | Sim | Sim | DoS |
| NTP | Deja Vu | Alta | Clientes | Alta | Baixa | Internet | Sim | Não | DoS |
| NTP | On-Path Timeshifting | Alta | Clientes | Mínima | Muito Alta | Internet | Sim | Não | DoS |
| NTP | DoS por KoD Spoofed | Baixa | Clientes | Mínima | Muito Alta | Internet | Sim | Não | DoS |
| Slow HTTP | Slow Header | Baixa | Servidor | Baixa | Alta | Internet | Não | Sim | DoS |
| Slow HTTP | Slow Message Body | Baixa | Servidor | Baixa | Alta | Internet | Não | Sim | DoS |
| Slow HTTP | Slow Read | Baixa | Servidor | Baixa | Alta | Internet | Não | Sim | DoS |
| Slow HTTP | HTTP PRAGMA | Baixa | Servidor | Baixa | Alta | Internet | Não | Sim | DoS |
| Slow Rate | SlowReq | Baixa | Servidor | Baixa | Alta | Internet | Não | Não | DoS |
| Slow Rate | Slowcomm | Baixa | Servidor | Baixa | Alta | Internet | Não | Não | DoS |
| Slow Rate | Slow Next | Baixa | Servidor | Baixa | Muito Alta | Internet | Não | Não | DoS |
| Slow Rate | SlowDrop | Baixa | Servidor | Baixa | Muito Alta | Internet | Não | Não | DoS |
| Request Flood | HTTP Flood | Alta | Servidor | Muito Alta | Alta | Internet | Não | Sim | **DDoS** |
| Request Flood | SIP Flood | Alta | Servidor | Muito Alta | Alta | Internet | Não | Sim | **DDoS** |
| Request Flood | DNS Flood | Alta | Servidor | Muito Alta | Alta | Internet | Não | Sim | **DDoS** |

**Observações chave:**

1. A complexidade do ataque clássico de inanição DHCP é alta. A complexidade de ataques contra NTP como Deja Vu é alta por requerer posição MitM. A complexidade de ataques de Request Flood é alta por exigir grande número de requisições.
2. Lançar ataque de inanição DHCP induzido envolve enviar apenas sondas falsificadas e portanto requer menos sobrecarga.
3. Apenas ataques de inanição DHCP são limitados a redes locais. Todos os outros são relevantes pela Internet.
4. Incidentes de ataques Slow HTTP DoS e HTTP Flood na Internet foram reportados no passado.
5. Como ataques de Request Flood requerem enviar grande número de requisições, um adversário pode usar serviços como *booters* para enviar a inundação de um grande número de dispositivos.

### 5.2. Comparação de Mecanismos de Defesa

Parâmetros: Proativo ou reativo? Defesa holística? Complexidade de implementação. Escalabilidade.

**Observações:**

A. Mecanismos de defesa de Técnicas Criptográficas envolvem alta complexidade de implementação. Servidor Redundância e Defesa Baseada em Desafio (HTTP Flood) também envolvem alta complexidade.

B. A escalabilidade de mecanismos baseados em Desafio é baixa.

---

## 6. Produtos Comerciais de Segurança para Combater Ataques DoS na Camada de Aplicação

### Tabela 16: Comparação de Soluções Comerciais DoS

| Produto | Fornecedor | NTP Timeshifting/Timesticking | Slow HTTP DoS | Request Flood | Slow Rate |
|---|---|---|---|---|---|
| Imperva Incapsula | Imperva | ✓ | ✓ | ✓ | ✓ (só SlowReq) |
| DOSarrest | DOSarrest | ✗ | ✓ | ✓ | ✓ (só SlowReq) |
| F5 | F5 Networks | ✗ | ✓ | ✓ | ✓ (só SlowReq) |
| Kona Site Defender | Akamai | ✗ | ✓ | ✓ | ✓ (só SlowReq) |
| AppWall | Radware | ✗ | ✓ | ✓ | ✓ (só SlowReq) |
| Availability Protection System (APS) | Arbor Networks | ✓ | ✗ | ✓ | ✗ |
| Nexusguard | Nexusguard | ✓ | ✗ | ✓ | ✗ |
| Athena | Verisign | ✗ | ✗ | ✓ | ✗ |
| Cloudflare-rate limit | Cloudflare | ✗ | ✗ | ✓ | ✗ |
| SiteProtect NG | Neustar | ✗ | ✗ | ✓ | ✗ |
| Sucuri DDoS Protection | Sucuri | ✗ | ✓ | ✓ | ✓ (só SlowReq) |
| Azure DDoS Protection | Microsoft | ✗ | ✓ | ✓ | ✓ (só SlowReq) |
| Project Shield | Google | ✗ | ✗ | ✓ | ✗ |
| AWS Shield Advanced | Amazon | ✗ | ✓ | ✓ | ✓ (só SlowReq) |
| IBM Cloud DDoS | IBM | ✗ | ✓ | ✓ | ✓ (só SlowReq) |

**Observação:** quase todo produto de segurança pode mitigar ataques de Request Flood, mas muito poucos podem combater ataques de *timeshifting*/*timesticking* NTP.

---

## 7. Conclusão e Direções de Pesquisa Futura

Com este *survey*, apresentamos uma revisão estruturada e abrangente de ataques DoS na camada de aplicação e mecanismos de defesa. Discutimos o método de execução de diferentes ataques e ferramentas conhecidas para lançá-los e os comparamos com base em diferentes parâmetros. Também revisamos vários mecanismos de defesa do estado da arte e produtos comerciais de mitigação DoS.

**Direções futuras de pesquisa:**

- **Ataques DoS Slow Rate e Request Flood contra protocolos orientados a conexão:** seria interessante estudar contra FTP, SMTP, IMAP.
- **Ataques DoS na camada de aplicação no contexto de IoT:** análise de quanto o efeito de cada ataque pode ser amplificado se dispositivos IoT vulneráveis forem usados.
- **Análise de vulnerabilidade de diferentes implementações:** Apache e IIS comportam-se diferentemente quando recebem requisição GET incompleta.
- **Desenvolvimento de ferramentas automatizadas de lançamento de ataque:** há muitas para starvation DHCP clássico, Slow HTTP DoS e Request Flood mas não para induzido DHCP starvation, NTP DoS e Slow Rate Genérico.

---

## Referências

Lista completa de 171 referências no PDF original (páginas 27-33). Mais relevantes para o nosso paper:

- **[72]** Imperva. *2019 Global DDoS Threat Landscape Report* — fonte do "292.000 req/s, 13 dias"
- **[70]** Fonte do "dobrando por trimestre"
- **[157]** Tripathi et al. (2017) — Slow HTTP DoS avaliado em 100 sites
- **[155]** Tripathi e Hubballi (2018) — ataques DoS contra HTTP 2.0
- **[120]** Ranjan et al. — análise comportamental de browsing
- **[169]** Zargar et al. (2013) — *survey* anterior de defesa DDoS
- **[136]** Singh et al. — *survey* de Slow HTTP DoS e HTTP-GET flood
- **[119]** Praseed e Thilagam (2018) — DDoS na camada de aplicação para web

> Lista completa nas páginas 27-33 do [PDF original](../pdfs/3448291.pdf).

---

## Resumo dos pontos-chave para o nosso paper

### As citações que usamos no Abstract/Intro

| Citação | Fonte exata | Onde citamos |
|---|---|---|
| **"292.000 req/s por 13 dias"** | §1 Introdução, citando Imperva 2019 ref [72] | Abstract; §1.1 Contexto |
| **"dobrando por trimestre"** | §1, ref [70] | Abstract; §1.1 |
| **"network layer caiu 50% no Q4 2017"** | §1, mesma ref [70] | §1.1 (como contraste) |
| **53% organizações com ataques internos em 2018** | §1, ref [150] | Pode usar como evidência adicional de motivação |
| **Taxonomia HTTP/DNS/SIP/DHCP/NTP DoS Layer 7** | §3-4 (Figura 1) | §1.2 (quando argumentamos que ninguém cobre HTTP + DNS Layer 7) |

### Argumento secundário central

A Tabela 14 (Comparação de Ataques) **não tem coluna "KG" ou "Semantic Reasoning"** — os ataques são classificados por complexidade, alvo, sobrecarga, furtividade, relevância, *spoofing*, incidentes reais, tipo. **As defesas (Tabela 15) também não incluem categoria de raciocínio semântico.** Confirma a lacuna que nosso paper aborda.

### Onde o paper diferencia o nosso

- §3.3 (Slow HTTP DoS) e §4.2 (Request Flood) são as seções centrais para nós — descrevem os ataques HTTP que modelamos (HTTP Flood = §4.2.1, Slow Header/Body = §3.3.1-2). Mas **todas as defesas listadas são monoprotocolar e por sessão individual** — nenhuma faz raciocínio cross-session via grafo de conhecimento.
- §4.2.1 (Defesas para HTTP Flood) é a seção mais próxima ao nosso trabalho. Categorias: Análise de Comportamento de Navegação (KG não aparece), Monitoramento de Atributos de Requisição (KG não aparece), Avaliação de Entropia, Baseado em Desafio. **Nosso paper adiciona uma 5ª categoria implícita: Raciocínio Semântico via Grafo de Conhecimento Centrado em Sessão.**

### Onde citar no nosso artigo

- **Abstract:** já citado `\cite{tripathi2021application}` para "dobrando por trimestre e 292k req/s por 13 dias"
- **§1.1 Contexto:** já citado para mesmas estatísticas
- **§1.2 gap 1 (Sessão como agregado):** podemos usar a Tabela 14 e §4.2.1 como evidência de que a literatura monoprotocolar não modela sessão semanticamente
- **§2.2 (Detecção HTTP Camada 7):** este *survey* é a referência canônica que organiza todas as defesas HTTP existentes — nossa Related Work vai citá-lo extensivamente
- **§2.4 (Posicionamento):** podemos argumentar que somos "a 5ª categoria que faltava" na taxonomia de defesas para HTTP Flood
