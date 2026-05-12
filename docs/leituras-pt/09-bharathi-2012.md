# Um Framework Baseado em PCA para Detecção de Ataques DDoS na Camada de Aplicação

> **Tradução em português** de *"A PCA Based Framework for Detection of Application Layer DDoS Attacks"*, Bharathi e Sukanesh (2012), WSEAS Transactions on Information Science and Applications 9(12):389-398.
>
> **PDF original:** [`docs/pdfs/56-524.pdf`](../pdfs/56-524.pdf) — 10 páginas
> **Status:** ✅ Tradução resumida (apenas seções essenciais — Tier 3)
> **Tier:** 3 (Baseline — referência metodológica para perfilamento comportamental + k-means)

---

## Autores

- **R. Bharathi** (*correspondência*: bharathi_akce@yahoo.co.in) — AP/ECE Department, University College of Engg., Nagercoil, Índia
- **Prof. Dr. R. Sukanesh** — ECE Department, Thiagarajar College of Engineering, Madurai, Índia

---

## Resumo

*Hackers* usam *Distributed Denial of Service* (DDoS) e deixam centenas e milhares de *bots* para sobrecarregar a vítima em termos de banda e reduzir os serviços que estão sendo prestados aos usuários. Para iniciar um ataque contra a vítima, *hackers* usam a Internet como local. Para abordar essa ameaça vários métodos foram propostos, mas todo método anterior identifica o ataque DDoS que existe nas camadas IP e TCP. Atacantes, por outro lado, encontraram as vulnerabilidades na camada de aplicação (camada superior) para atacar a vítima usando DDoS conhecido como (**App-DDoS**) e tornam complexidade em encontrar e lidar com o ataque. Neste artigo, para detectar o ataque em estágio inicial que é direcionado para a camada de aplicação, propomos um *framework*. **Este *framework* usa o perfilamento de comportamento de navegação do usuário e tráfego de rede por independência de ordem de sequência e Análise de Componentes Principais (PCA) respectivamente. Esses perfis são agrupados (*clustered*), e um limiar é usado para verificar e determinar se uma requisição HTTP de um usuário é normal ou anormal.** Se a requisição do usuário à vítima é normal, então permite o acesso, caso contrário nega a requisição no estágio inicial.

## Palavras-chave

App-DDoS, detecção de anomalia, comportamento de navegação do usuário, tráfego de rede, PCA, independência de ordem de sequência, *clustering*.

---

## 1. Introdução

Organizações que dependem da Internet para seus negócios, como serviços financeiros, *online gaming*, e-commerce, etc., requerem resposta contínua e rápida à requisição de seus clientes. Internet e outros produtos que dependem dela estão sempre propensos a falha. Uma dessas falhas intencionais é o **DDoS** com a motivação de atacar o computador alvo (vítima) ou qualquer outro recurso que use Internet.

DDoS pode ser categorizado em dois tipos:

1. **Inundação de banda (*Bandwidth flooding*):** *hackers* inundam a rede com requisições massivas, criando assim tráfego indesejado.
2. **Inundação de recurso (*Resource flooding*):** recursos da vítima são engajados por atacantes.

### Desafios de Detectar App-DDoS

(1) **App-DDoS usa protocolos de camada superior como HTTP** para passar pelo sistema de detecção, que são projetados para camada inferior.

(2) Junto com inundação, App-DDoS também consome recursos do servidor vítima alvo. Atacantes ou rastreiam a taxa média de requisição do usuário legítimo e usam a mesma taxa para atacar o servidor, ou empregam *botnet* em larga escala para gerar fluxos de ataque de baixa taxa.

### O Framework Proposto

Detectam o ataque DDoS através do comportamento anônimo do usuário. Coletam detalhes do usuário e da rede e criam um arquivo de *log* contendo os atributos de todos os usuários como data, hora, detalhes do *site*, detalhes de *hyperlink*, endereço IP, etc.

Usando o arquivo de *log* criam uma matriz chamada **matriz de comportamento** usando independência de ordem de sequência. Para derivar os padrões de navegação de vários usuários, usam **PCA** para remover informação indesejada e reduzir a dimensão. Os padrões de navegação recuperados via PCA são agrupados usando algoritmo **k-means**. Um valor de limiar é definido a partir da matriz de dados e atua como fator decisor para se a requisição dada deve ser aceita ou negada.

### 📌 Figura 1 e 2: Ataque DDoS Típico e Fluxo do Framework Proposto

> **Descrição:** Figura 1 ilustra ataque DDoS típico com botmaster, bots e servidor vítima. Figura 2 mostra o pipeline: dados de log → matriz de comportamento (independência de ordem de sequência) → PCA → k-means clustering → limiar de aceitar/negar.
>
> 📌 *Ver Figuras 1 e 2 nas páginas 2-3 do PDF original.*

---

## 2. Trabalhos Relacionados

Discutem mecanismos de detecção usados anteriormente por diferentes autores. As abordagens incluem:

- **Entropia e distribuições ordenadas por frequência** de atributos de pacote.
- **Análise de correlação multivariada** e modelo de covariância para detectar DDoS via SYN flood.
- **Método estatístico + filtragem** (filtro Kalman) usando matriz de tráfego.
- **Mecanismo de defesa colaborativo** com janela de detecção dupla.
- **Algoritmo baseado em perfil** para anomalias curtas e longas com técnica de projeção aleatória.
- **Hidden Markov Models** para análise comportamental.
- **DefCOM** — *framework* colaborativo combinando métodos.
- **WSVM** (combinação de SVM e teoria de kernel wavelet).

---

## 3. Framework Proposto

### 3.1. Matriz de Comportamento (Sequência Independente da Ordem)

A partir dos *logs*, constroem uma matriz $M$ onde linhas representam usuários e colunas representam atributos de comportamento (data, hora, *site* visitado, *hyperlinks* seguidos, endereço IP, etc.). A matriz é construída de forma que a **ordem das ações** não importa — apenas a frequência e composição.

### 3.2. PCA para Redução de Dimensão

Aplicam PCA à matriz de comportamento. Os componentes principais que retêm a maioria da variância são selecionados. Isso reduz a dimensionalidade do problema enquanto preserva os padrões discriminantes entre usuários.

### 3.3. K-means Clustering

Os usuários (em sua representação reduzida via PCA) são agrupados usando k-means. **Propriedades importantes do k-means:**

(1) **Não há sobreposição** entre *clusters*.
(2) Todos os membros de um *cluster* estão mais próximos dele que de outros *clusters*.

### 3.4. Limiar de Detecção

Uma matriz de dados é construída a partir do qual um valor de limiar é definido. Este limiar atua como fator decisor para uma requisição:

- Se a distância do *cluster* de um usuário está abaixo do limiar → **requisição normal** → permitir acesso.
- Se a distância está acima do limiar → **requisição anormal** → negar acesso.

---

## 4. Resultados Experimentais

### Configuração

Validação com diferentes tipos de ataques App-DDoS via:

- Coleta de tráfego com normal e anormal.
- Variação de número de usuários e taxas.
- Comparação de FPR (taxa de falso positivo) e FNR (taxa de falso negativo).

### Achados-Chave

- O *framework* detecta App-DDoS em estágio inicial, antes que a vítima seja sobrecarregada.
- Taxa de falsos positivos baixa quando o limiar é calibrado adequadamente.
- O *clustering* k-means é eficiente para diferenciar comportamento normal de anômalo.

### Métricas

| Métrica | Resultado Aproximado |
|---|---|
| TPR (taxa de detecção) | Alta |
| FPR (taxa falso positivo) | Baixa após calibração |
| Tempo de detecção | Estágio inicial (antes da sobrecarga) |

---

## 5. Conclusão

Este artigo propôs um *framework* baseado em PCA + k-means para detecção de ataques App-DDoS na camada de aplicação. **A inovação chave é o uso de perfilamento de comportamento de navegação do usuário** (não apenas estatísticas de tráfego de rede) para distinguir requisições normais de anormais.

**Vantagens:**
- Detecta App-DDoS antes da sobrecarga.
- Reduz dimensionalidade via PCA, simplificando análise.
- *Clustering* k-means permite ajuste flexível ao número de perfis.

**Limitações implícitas:**
- A representação é apenas de comportamento individual de usuário, sem semântica de sessão.
- Não considera correlação cross-session (campanhas coordenadas).
- Saída é binária (aceitar/negar), sem explicação ontológica.

---

## Referências

Lista de ~25 referências no [PDF original](../pdfs/56-524.pdf), focadas em métodos estatísticos de detecção DDoS.

---

## Resumo dos pontos-chave para o nosso paper

### Por que este paper importa para nós

Bharathi 2012 é o **baseline comportamental** no nosso §4.4. Representa a abordagem de **perfilamento de comportamento de navegação + PCA + k-means** para detecção de App-DDoS — uma das primeiras tentativas de detectar DDoS especificamente na camada de aplicação usando *features* de sessão.

### Como nosso paper se diferencia

| Dimensão | Bharathi 2012 | Nosso paper |
|---|---|---|
| **Representação do usuário** | Vetor de *features* (data, hora, site, hyperlinks, IP) | Sessão como entidade ontológica com identidade, *endpoint*, comportamento |
| **Redução de dimensão** | PCA — autovetores | Sem redução — preservamos estrutura |
| **Classificação** | K-means + limiar | Regras semânticas sobre grafo |
| **Cross-session** | Não modela | Núcleo da contribuição |
| **Explicação** | Binária (aceitar/negar) | Cadeia de evidência semântica |

### Argumentos para citação no nosso artigo

Já citado em `\cite{bharathi2012pca}`:

- **§1.1 Contexto:** lista clássica de detecção baseada em comportamento
- **§1.4 Contribuição 3:** "contrastando com detectores anteriores baseados em features agregadas"
- **§4.4 Baselines:** aproximação direta — matriz de comportamento + k-means é nosso segundo baseline

### Os dois desafios que Bharathi admite (citáveis)

Aparecem na §1 do artigo:

1. *"App-DDoS usa protocolos de camada superior como HTTP para passar pelo sistema de detecção, que são projetados para camada inferior."* — apoio para nossa motivação de Layer 7.
2. *"Atacantes rastreiam a taxa média de requisição do usuário legítimo e usam a mesma taxa para atacar o servidor"* — apoio para nosso argumento de que detecção monoprotocolar por sessão falha em campanhas coordenadas.
