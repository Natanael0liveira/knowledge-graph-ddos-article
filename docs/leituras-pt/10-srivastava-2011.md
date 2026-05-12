# Um Survey Recente sobre Ataques DDoS e Mecanismos de Defesa

> **Tradução em português** de *"A Recent Survey on DDoS Attacks and Defense Mechanisms"*, Srivastava, Gupta, Tyagi, Sharma, Mishra (2011), PDCTA 2011 (Springer LNCS / CCIS 203, pp. 570-580).
>
> **PDF original:** [`docs/pdfs/111.pdf`](../pdfs/111.pdf) — ~10 páginas
> **DOI:** 10.1007/978-3-642-24037-9_57
> **Status:** ✅ Tradução resumida (apenas seções essenciais — Tier 4)
> **Tier:** 4 (Opcional — survey antigo de DDoS geral; substituído por Tripathi 2021 para Layer 7)

---

## Autores

- **A. Srivastava** (*correspondência*), B. B. Gupta, A. Tyagi, A. Sharma, A. Mishra
- Department of Computer Science, Graphic Era University, Dehradun, Índia
- Department of Electronics and Computer Engineering, Indian Institute of Technology Roorkee, Índia

---

## Resumo

Ataque *Distributed Denial-of-service* (DDoS) é uma das ameaças mais perigosas que pode causar efeitos devastadores na Internet. DDoS começou principalmente em 1998, mas a influência dele foi percebida pelas pessoas apenas quando as grandes organizações e corporações foram atingidas por ataques DDoS em julho de 1999. Desde então várias ferramentas de ataque DDoS como **Trinoo, Shaft, Tribe Flood Network (TFN), TFN2K e Stacheldraht** foram identificadas e analisadas. Todas essas ferramentas podem lançar ataques DDoS de milhares de *hosts* comprometidos e derrubar virtualmente qualquer conexão, qualquer rede na Internet apenas com poucos comandos. Este *survey* trata da introdução a ataques DDoS, história e incidentes de DDoS, estratégia de ataque DDoS, ferramentas de ataque DDoS e classificação de vários mecanismos de ataque e defesa.

---

## 1. Introdução

Hoje, ataques DDoS tornaram-se uma ameaça comum a negócios *online*. **Com mais de 50.000 ataques distintos por semana**, ataques DDoS tornaram-se forma altamente visível e custosa de cibercrime. Tendências recentes mostram que o montante total dos ataques DDoS atingiu mais de 100 gigabit por segundo. Um estudo conduzido pela Arbor Networks mostra o aumento ano a ano do tráfego de ataque DDoS na Internet de 2001 a 2010.

Ataques de negação de serviço (DoS) negam serviços a usuários legítimos. Com o tempo, ataque DoS evoluiu para ataque de negação de serviço distribuída onde atacante compromete outras máquinas vulneráveis na Internet para coordenar ataque em um único instante de tempo na máquina vítima, multiplicando assim o efeito.

### 📌 Figuras 1 e 2: Aumento de Tráfego DDoS e Cenário sob Ataque DDoS

> **Descrição:** Figura 1 mostra crescimento da banda de DDoS de 2001-2011 (atingindo 100 Gbps em 2010). Figura 2 ilustra cenário típico: usuários legítimos com 3 Mbps vs. botnet gerando 3-100 Gbps.
>
> 📌 *Ver Figuras 1 e 2 nas páginas 1-2 do PDF original.*

---

## 2. História e Incidentes de Ataques DDoS

Havia apenas cerca de 1 milhão de *hosts* na Internet em janeiro de 1993, que aumentou para mais de 775 milhões em outubro de 2010.

**Primeiro grande ataque DDoS reportado** ocorreu em **agosto de 1999, contra a Universidade de Minnesota**. Este ataque desligou a rede da vítima por mais de dois dias.

Em **2000, um ataque DDoS parou vários sites comerciais principais**, incluindo Yahoo e CNN.

Moore et al. usaram análise *backscatter* em três conjuntos de dados de uma semana para avaliar o número, duração e foco de ataques DDoS. Encontraram que mais de 12.000 ataques ocorreram contra mais de 5.000 redes vítimas distintas em fevereiro de 2001.

O **ataque no Yahoo em 2000** empurrou o *site offline* por cerca de 3 horas, recebendo um nível sem precedentes de tráfego de cerca de 1 GB/sec.

---

## 3. Visão Geral de Ataques DDoS

Para criar um ataque DDoS efetivo, três passos são necessários:

1. **Scanning** — Atacante primeiro recruta as máquinas que têm alguma vulnerabilidade. Estratégias de varredura: *hit list scanning*, *topological scanning*, *permutation scanning*, *local subnet scanning*.

2. **Propagação** — Recruta outras máquinas com ajuda das já comprometidas. Três modelos principais: *Central source propagation*, *back-chaining*, *autonomous*.

3. **Comunicação** — Canal de comunicação importante para coordenar um ataque. Modelos: *Agent-Handler* (TCP/ICMP/UDP) ou *IRC*.

---

## 4. Componentes de um Ataque DDoS

- **Atacante** — máquina inicial controlada pelo *hacker*
- **Handlers / Masters** — máquinas intermediárias que coordenam *agents*
- **Agents / Zombies / Bots** — máquinas comprometidas que executam o ataque
- **Vítima** — alvo final

---

## 5. Classificação de Mecanismos de Ataque DDoS

Categorias principais:

- **Por grau de automação:** manual, semi-automatizado, automatizado
- **Por vulnerabilidade explorada:**
  - Ataques de inundação (*flooding*): UDP, ICMP, TCP SYN
  - Ataques de amplificação (Smurf, Fraggle)
  - Ataques de exploração de protocolo (Land, Teardrop)
- **Por taxa de ataque:** alta taxa contínua, taxa variável, pulsante
- **Por característica de pacote:** baseado em conteúdo, baseado em assinatura

---

## 6. Classificação de Mecanismos de Defesa DDoS

Quatro categorias principais:

1. **Prevenção (*Prevention*)** — endereçar vulnerabilidades antes do ataque
2. **Detecção (*Detection*)** — identificar ataques em andamento
3. **Resposta (*Response*)** — reagir aos ataques detectados
4. **Mitigação (*Mitigation*)** — reduzir impacto durante o ataque

### Métodos de Detecção

- Baseados em **assinatura**: efetivos apenas para ataques conhecidos
- Baseados em **anomalia**: podem detectar ataques novos mas podem resultar em altas taxas de alarme falso

### Métodos de Resposta

- Identificação e classificação de tráfego
- Rastreamento ao *handler* ou atacante
- Limitação de taxa

---

## 7. Desafios em Lidar com Ataques DDoS

- **Atribuição** — identificar o verdadeiro atacante por trás de *bots*
- **Falsos positivos** — distinguir tráfego legítimo (*flash crowd*) de ataque
- **Escala** — milhões de *bots* tornam mitigação difícil
- **Diversidade** — diferentes vetores de ataque requerem diferentes defesas
- **Velocidade** — ataques modernos podem alcançar 100 Gbps em segundos

---

## 8. Conclusão e Trabalho Futuro

Este *survey* discutiu o problema DDoS, sua história, classificação e mecanismos de defesa. Direções futuras incluem:

- Detecção em tempo real com baixa taxa de falsos positivos
- Mecanismos colaborativos entre ISPs
- Defesa contra *botnets* IoT emergentes
- Atribuição em ataques distribuídos

---

## Referências

Lista de ~20 referências focadas em DDoS volumétrico e *botnets* da era 1999-2010.

---

## Resumo dos pontos-chave para o nosso paper

### Por que este paper é Tier 4 (opcional)

Srivastava 2011 é um *survey* DDoS **genérico e antigo** focado em ataques volumétricos clássicos da era 1999-2010 (Trinoo, TFN, Stacheldraht). **Não cobre ataques de Camada 7 modernos** que são o foco do nosso paper.

### Para que serve

Como **referência histórica** quando precisarmos contextualizar a evolução de DDoS:

- *"DDoS começou em 1999..."*
- *"Botnet Mirai e similares evoluíram dos modelos Trinoo/TFN..."*
- *"Volume cresceu de 1 GB/sec (2000) para 100 Gbps (2010)..."*

### O que **NÃO** usar deste paper

- Estatísticas modernas (são desatualizadas — usar Tripathi 2021 e Odusami 2020)
- Defesas modernas (focam em camada 3/4, não Camada 7)
- Discussão de KG (não cobre)

### Citação no nosso artigo

**Não citamos atualmente.** Removemos a referência `\cite{srivastava2011recent}` da versão atual do nosso artigo porque Tripathi & Hubballi 2021 cobre o mesmo material com cobertura muito mais ampla e recente. Mantemos a entrada `.bib` por se precisarmos do número "50.000 ataques distintos por semana" como dado histórico em algum momento.
