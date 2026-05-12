# Por Uma Definição de Grafos de Conhecimento

> **Tradução integral em português** de *"Towards a Definition of Knowledge Graphs"*, Ehrlinger e Wöß (2016), SEMANTiCS 2016 — Posters and Demos Track, Leipzig, Alemanha, 13-14 de setembro de 2016.
>
> **PDF original:** [`docs/pdfs/paper4.pdf`](../pdfs/paper4.pdf) — 4 páginas
> **Status:** ✅ Tradução completa
> **Tier:** 2 (Importante — definição canônica de KG, leitura rápida)

---

## Autores

Lisa Ehrlinger e Wolfram Wöß
Institute for Application Oriented Knowledge Processing
Johannes Kepler University Linz, Áustria
{lisa.ehrlinger | wolfram.woess}@jku.at

---

## Resumo

Recentemente, o termo *grafo de conhecimento* (do inglês *knowledge graph*) tem sido usado frequentemente em pesquisa e nos negócios, geralmente em estreita associação com tecnologias da Web Semântica, *linked data*, análise de dados em larga escala e computação em nuvem. Sua popularidade é claramente influenciada pela introdução do Knowledge Graph da Google em 2012, e desde então o termo tem sido amplamente utilizado sem uma definição precisa. Uma grande variedade de interpretações tem dificultado a evolução de um entendimento comum sobre grafos de conhecimento. Numerosos trabalhos de pesquisa referenciam o Knowledge Graph da Google, embora não exista documentação oficial sobre os métodos empregados. O pré-requisito para uma adoção acadêmica e comercial generalizada de um conceito ou tecnologia é um entendimento comum, baseado idealmente em uma definição livre de ambiguidade. Atacamos esse problema discutindo e definindo o termo *grafo de conhecimento*, considerando sua história e diversidade em interpretações e usos. Nosso objetivo é propor uma definição de grafos de conhecimento que sirva como base para discussões sobre o tema e contribua para uma visão comum.

## Conceitos CCS

- Sistemas de informação → Sistemas de gerenciamento de dados; Aplicações de sistemas de informação.

## Palavras-chave

Grafos de Conhecimento, Bases de Conhecimento, Ontologias, Representação de Conhecimento, Web Semântica.

---

## 1. Introdução

Considerável pesquisa em grafos de conhecimento (KGs, do inglês *knowledge graphs*) tem sido realizada nos últimos anos, especialmente na comunidade da Web Semântica, e como consequência uma variedade de definições e descrições parcialmente contraditórias emergiu. A frequentemente citada entrada de *blog* da Google [18] basicamente descreve um aprimoramento do seu motor de busca com semântica. E também a Wikipedia, a enciclopédia mais abrangente da *web*, não fornece informação sobre grafos de conhecimento em geral, mas refere-se à implementação da Google sem mencionar a existência de outros grafos de conhecimento. Embora a Wikipedia não seja uma fonte de referência científica, ela contribui para um entendimento comum através de seu papel como fonte primária de informação para várias aplicações proeminentes de representação de conhecimento. Outras definições podem levar à suposição de que *grafo de conhecimento* é sinônimo para qualquer representação de conhecimento baseada em grafo (cf. [12, 16]). Argumentamos que essa definição não é suficiente para uma aplicação adequada de grafos de conhecimento, pois não impõe um conjunto mínimo de requisitos que um KG deva cumprir. Assim, mesmo um vocabulário simples baseado em grafo poderia ser publicado como grafo de conhecimento. Adicionalmente, tal definição cria uma barreira de entrada para pessoas que não estão familiarizadas com grafos de conhecimento e querem se aprofundar no tópico ou pretendem construir um KG por conta própria. Uma definição clara propaga um entendimento compartilhado dos benefícios, melhorias ou desvantagens que podem ser esperados quando alguém constrói um grafo de conhecimento. Assim, oferecemos uma discussão sobre grafos de conhecimento e motivamos uma definição para apoiar um entendimento comum.

Este artigo está organizado da seguinte forma: a Seção 2 apresenta pesquisa relacionada de estado da arte e tentativas existentes de definir grafos de conhecimento. A Seção 3 fornece uma visão geral curta de aplicações históricas e atuais de grafos de conhecimento. A Seção 4 delimita e diferencia o termo *grafo de conhecimento* de termos similares e introduz nossa definição.

---

## 2. Definições Selecionadas

Grafos de conhecimento têm estado no foco da pesquisa desde 2012, resultando em uma ampla variedade de descrições e definições publicadas. A Tabela 1 lista definições representativas e demonstra a falta de um núcleo comum, fato que também é apontado por Paulheim [16] em 2015. Paulheim listou em seu *survey* sobre refinamento de grafos de conhecimento o conjunto mínimo de características que devem estar presentes para distinguir grafos de conhecimento de outras coleções de conhecimento (cf. primeira definição na Tabela 1), o que basicamente restringe o termo a qualquer representação de conhecimento baseada em grafo. No processo de revisão *online* de *"Knowledge Graph Refinement: A Survey of Approaches and Evaluation Methods"* [16], Noy [^1] concordou que uma definição mais precisa era difícil de encontrar naquele momento. Essa declaração aponta para a demanda por investigação mais próxima e reflexão mais profunda nessa área.

[^1]: http://www.semantic-web-journal.net/content/knowledge-graph-refinement-survey-approaches-and-evaluation-methods [Agosto de 2016]

Descrições vagas de grafos de conhecimento foram publicadas no anúncio de uma edição especial sobre grafos de conhecimento pelo *Journal of Web Semantics* e pela *Semantic Web Company* (cf. segunda e terceira definições na Tabela 1). Ambas as definições poderiam igualmente bem descrever uma ontologia ou — mais geralmente — qualquer tipo de representação semântica de conhecimento, e nem sequer impõem uma estrutura de grafo. Adicionalmente, o tamanho é destacado como característica essencial, refletido em frases como *"grandes redes"* ou *"vastas redes"* [11], embora permaneça pouco claro o que *"grande"* significa nesse contexto. Färber et al. definiram um grafo de conhecimento como um grafo *Resource Description Framework* (RDF) e afirmaram que o termo KG foi cunhado pela Google para descrever qualquer base de conhecimento (KB, do inglês *knowledge base*) baseada em grafo [7]. Embora essa definição seja a única formal, contradiz definições mais gerais ao requerer explicitamente o modelo de dados RDF. Pujara et al. não forneceram uma definição concisa, mas descreveram as características de grafos de conhecimento. Diferentemente das outras definições, que focam exclusivamente na estrutura interna do KG, eles destacaram a importância de um sistema de extração automática. No prefácio do *13th International Semantic Web Conference Proceedings* (2014), a seguinte afirmação foi publicada:

> *Significativamente, grandes empresas, como Google, Yahoo, Microsoft e Facebook, criaram seus próprios "grafos de conhecimento" que viabilizam buscas semânticas e permitem processamento e entrega mais inteligentes de dados: O uso desses grafos de conhecimento é agora a norma, em vez da exceção.* [14]

Mais uma vez, isso destaca a demanda por uma definição comum, pois é necessário definir e diferenciar KGs de outros conceitos para fazer afirmações valiosas e precisas sobre a introdução e disseminação de grafos de conhecimento. Além disso, esta declaração da ISWC proclama o uso de grafos de conhecimento como a norma em geral, em vez de restringir o escopo, domínio ou área de aplicação onde KGs podem ser usados beneficamente e eficientemente. Apesar de sua falta de clareza, essa declaração parece ter inspirado muitos pesquisadores a submeter artigos sobre grafos de conhecimento na conferência seguinte em 2015[^2].

[^2]: http://iswc2015.semanticweb.org/program/accepted-papers [Agosto de 2016]

### Tabela 1: Definições Selecionadas de Grafo de Conhecimento

| Definição | Fonte |
|---|---|
| *"Um grafo de conhecimento (i) descreve principalmente entidades do mundo real e suas inter-relações, organizadas em um grafo, (ii) define classes possíveis e relações de entidades em um esquema, (iii) permite inter-relacionar potencialmente entidades arbitrárias entre si e (iv) abrange diversos domínios temáticos."* | Paulheim [16] |
| *"Grafos de conhecimento são grandes redes de entidades, seus tipos semânticos, propriedades e relacionamentos entre entidades."* | Journal of Web Semantics [12] |
| *"Grafos de conhecimento podem ser concebidos como uma rede de todo tipo de coisas que são relevantes para um domínio específico ou para uma organização. Eles não estão limitados a conceitos abstratos e relações, mas podem também conter instâncias de coisas como documentos e conjuntos de dados."* | Semantic Web Company [3] |
| *"Definimos um Grafo de Conhecimento como um grafo RDF. Um grafo RDF consiste em um conjunto de triplas RDF, onde cada tripla RDF (s, p, o) é um conjunto ordenado dos seguintes termos RDF: um sujeito s ∈ U ∪ B, um predicado p ∈ U, e um objeto U ∪ B ∪ L. Um termo RDF é ou uma URI u ∈ U, ou um nó em branco b ∈ B, ou um literal l ∈ L."* | Färber et al. [7] |
| *"[...] sistemas existem [...] que usam uma variedade de técnicas para extrair novo conhecimento, na forma de fatos, da web. Esses fatos são inter-relacionados e, portanto, recentemente esse conhecimento extraído tem sido referido como grafo de conhecimento."* | Pujara et al. [17] |

---

## 3. Aplicações de Grafos de Conhecimento

Nos anos 1980, pesquisadores da Universidade de Groningen e da Universidade de Twente nos Países Baixos introduziram inicialmente o termo *grafo de conhecimento* para descrever formalmente seu sistema baseado em conhecimento que integra conhecimento de diferentes fontes para representar linguagem natural [10, 15]. Os autores propuseram KGs com um conjunto limitado de relações e foco em modelagem qualitativa incluindo interação humana, o que claramente contrasta com a ideia de KGs amplamente discutida nos últimos anos.

Em 2012, a Google introduziu o *Knowledge Graph* como uma melhoria semântica da função de busca da Google que não casa *strings*, mas permite buscar por *"coisas"*, em outras palavras, objetos do mundo real [18]. Embora o *post* de *blog* não forneça detalhes de implementação, ele foi citado mais de 100 vezes segundo o Google Scholar[^3]. Desde 2012, o termo *grafo de conhecimento* também é usado para descrever uma família de aplicações. Implementações frequentemente mencionadas são DBPedia, YAGO (*Yet Another Great Ontology*), Freebase, Wikidata, a ferramenta de assistência de busca semântica Spark do Yahoo, o Knowledge Vault da Google, o Satori da Microsoft e o grafo de entidades do Facebook [7, 14, 16, 11]. Essas aplicações diferem em suas características, como arquitetura, propósito operacional e tecnologia usada, o que dificulta encontrar um consenso e criar uma definição de grafo de conhecimento. O menor denominador comum das aplicações de código aberto listadas é seu uso de *Linked Data*, enquanto dificilmente alguma informação comprovada está disponível sobre o Satori e o grafo de entidades.

[^3]: https://scholar.google.at/scholar?q=Introducing+the+Knowledge+Graph%3A+things%2C+not+strings&btnG=&hl=en&as_sdt=0%2C5 [Agosto de 2016]

Adicionalmente, o termo mais específico *grafo de conhecimento empresarial* (do inglês *enterprise knowledge graph*) é usado por algumas empresas menores, por exemplo, SindiceTech[^4] e Semantic Web Company [3]. Ambas as empresas buscam descrever um modelo similar que extrai e armazena diversos dados empresariais em um *triple store* e os analisa usando técnicas de aprendizado de máquina para adquirir novo conhecimento dos dados e reutilizá-lo em outras aplicações.

[^4]: http://www.sindicetech.com/overview.html [Agosto de 2016]

---

## 4. Análise Terminológica e Definição

Ao analisar trabalho de pesquisa atual que define ou aborda grafos de conhecimento, dois problemas fundamentais podem ser identificados: (a) a entrada de *blog* da Google sobre seu Knowledge Graph é citada como se fornecesse uma explicação apropriada para constituir um grafo de conhecimento (cf. [17, 19]), e (b) os termos *grafo de conhecimento* e *base de conhecimento* são usados intercambiavelmente (cf. [5, 7, 8, 13, 16, 20]). O segundo problema leva à suposição enganosa de que o termo *grafo de conhecimento* é sinônimo de *base de conhecimento*, que em si é frequentemente usado como sinônimo de *ontologia*. Um exemplo dessa confusão é que tanto o Knowledge Vault quanto o Knowledge Graph da Google foram chamados de bases de conhecimento de larga escala por seus respectivos criadores [5]. Outro exemplo é o YAGO, que — de acordo com seu nome — é uma ontologia, mas é referenciado tanto como base de conhecimento (cf. [5, 16]) quanto como grafo de conhecimento (cf. [8, 21]). Similarmente, funcionários do Yahoo [2] não distinguem claramente entre base de conhecimento, grafo de conhecimento e ontologia. Eles afirmam que constroem sua base de conhecimento alinhando novas entidades, relações e informações com sua ontologia comum. Portanto, informação incompleta, inconsistente e possivelmente imprecisa é transformada em um grafo de conhecimento rico, unificado e desambiguado. Com base nessa informação, o entendimento deles de um grafo de conhecimento é a base de conhecimento limpa, que é a população (por exemplo, instâncias) de sua ontologia.

Para distinguir entre os termos, eles devem ser esclarecidos explicitamente. De acordo com Akerkar e Sajja [1], um sistema baseado em conhecimento usa inteligência artificial para resolver problemas, e consiste em duas partes: uma base de conhecimento e um motor de inferência. A base de conhecimento é um conjunto de dados com semântica formal que pode conter diferentes tipos de conhecimento, por exemplo, regras, fatos, axiomas, definições, declarações e primitivos [4]. Assim, o Knowledge Vault não pode ser classificado como uma verdadeira base de conhecimento, pois estende a ideia de um armazenamento semântico puro com capacidades de raciocínio e, portanto, guarda maior semelhança com um sistema baseado em conhecimento.

Uma ontologia é uma especificação formal e explícita de uma conceitualização compartilhada que é caracterizada por alta expressividade semântica requerida para complexidade aumentada [9]. Representações ontológicas permitem modelagem semântica do conhecimento e, portanto, são comumente usadas como bases de conhecimento em aplicações de inteligência artificial (IA), por exemplo, no contexto de sistemas baseados em conhecimento. A aplicação de uma ontologia como base de conhecimento facilita a validação de relacionamentos semânticos e a derivação de conclusões a partir de fatos conhecidos para inferência (isto é, raciocínio) [9]. Enfatizamos explicitamente que uma ontologia não difere de uma base de conhecimento, embora ontologias sejam às vezes erroneamente classificadas como estando no mesmo nível de esquemas de banco de dados [6]. De fato, uma ontologia consiste não apenas em classes e propriedades (por exemplo, `owl:ObjectProperty` e `owl:DatatypeProperty`), mas pode também conter instâncias (isto é, a população da ontologia).

Por um lado, o tamanho é frequentemente mencionado como uma característica essencial de grafos de conhecimento, portanto um KG poderia ser descrito como uma ontologia muito grande. No entanto, outros contribuidores apontaram que grafos de conhecimento são de alguma forma superiores às ontologias [3] e fornecem características adicionais. Assim, a diferença entre um grafo de conhecimento e uma ontologia poderia ser interpretada ou como uma questão de quantidade (por exemplo, uma ontologia grande), ou de requisitos estendidos (por exemplo, um *reasoner* embutido que permite derivar novo conhecimento). A segunda interpretação leva à suposição de que um grafo de conhecimento é um sistema baseado em conhecimento que contém uma base de conhecimento e um motor de raciocínio. Focando em *"grafos de conhecimento"* gerados automaticamente existentes, podemos identificar outra característica essencial: coleta, extração e integração de informação de fontes externas estende um sistema puro baseado em conhecimento com o conceito de sistemas de integração. A maioria das aplicações de código aberto listadas na Seção 3 implementa o aspecto de integração com *Linked Data*.

### 📌 Figura 1: Arquitetura de um Grafo de Conhecimento

> **Descrição em prosa:** A figura mostra uma caixa retangular maior rotulada como **"Sistema baseado em conhecimento"** contendo dois componentes internos lado a lado:
> 1. À esquerda, uma caixa rotulada **"Base de conhecimento (e.g., ontologia)"**
> 2. À direita, uma caixa rotulada **"Motor de raciocínio"** (*Reasoning engine*)
>
> Fora dessa caixa maior, à esquerda, há fontes de dados externas listadas verticalmente: **"Fonte 1"**, **"Fonte 2"**, **"..."** — todas com setas apontando para a Base de Conhecimento dentro do sistema.
>
> A figura ilustra que um grafo de conhecimento é uma arquitetura combinando: (a) integração de múltiplas fontes externas em uma base de conhecimento (geralmente ontologia), e (b) um motor de raciocínio que opera sobre essa base.
>
> 📌 *Para ver a figura original, consulte página 3 do PDF [`docs/pdfs/paper4.pdf`](../pdfs/paper4.pdf).*

A Figura 1 ilustra a combinação dessas suposições, o que resulta em uma arquitetura abstrata de grafo de conhecimento. Com base nessa arquitetura e derivada da análise terminológica, definimos um grafo de conhecimento da seguinte forma:

> **Um grafo de conhecimento adquire e integra informação em uma ontologia e aplica um *reasoner* para derivar novo conhecimento.**

Essa definição alinha-se com a suposição de que um grafo de conhecimento é de alguma forma superior e mais complexo do que uma base de conhecimento (por exemplo, uma ontologia), pois aplica um motor de raciocínio para gerar novo conhecimento e integra uma ou mais fontes de informação. Consequentemente, um grafo de conhecimento criado manualmente que não suporta aspectos de integração é uma base de conhecimento simples, ou um sistema baseado em conhecimento, caso forneça capacidades de raciocínio. A definição não leva em conta o aspecto de quantidade (tamanho), especialmente com relação a uma grande ABox da ontologia, pois não é claro o que pode ser considerado *"grande"*. Em vez disso, as capacidades de raciocínio são destacadas como característica essencial para derivar novo conhecimento e diferenciar um KG de bases de conhecimento.

Adicionalmente, surge a questão sobre o que constitui a diferença entre a Web Semântica e grafos de conhecimento. KGs menores, por exemplo, grafos de conhecimento empresariais, podem ser claramente diferenciados da Web Semântica devido ao seu domínio restrito. O objetivo dos grandes motores de busca é rastrear e processar toda informação disponível na *web*, o que leva a um interesse aumentado na implementação generalizada de tecnologia semântica. Dificilmente alguma informação está disponível sobre as tecnologias aplicadas no Knowledge Graph da Google e no Satori da Microsoft, mas o Spark do Yahoo e o Knowledge Vault aparentemente usam padrões da Web Semântica como RDF. Considerando as camadas da Web Semântica, um grafo de conhecimento, em comparação, implanta ou exatamente a mesma tecnologia para cada camada ou uma similar que oferece as mesmas características. Por exemplo, empresas podem usar identificadores proprietários no lugar de URIs e JSON-LD[^5] como formato de serialização substituindo XML e RDF. No entanto, essas tecnologias são apenas exemplos, e particularmente na camada de sintaxe, XML é frequentemente substituído por formatos mais leves e mais fáceis de ler como Turtle, N-Triples ou N-Quads na comunidade da Web Semântica. Em conclusão, a Web Semântica poderia ser interpretada como o grafo de conhecimento mais abrangente, ou — inversamente — um grafo de conhecimento que rastreia a *web* inteira poderia ser interpretado como uma Web Semântica autocontida.

[^5]: http://json-ld.org [Agosto de 2016]

---

## 5. Conclusão

A representação de conhecimento baseada em grafo tem sido pesquisada por décadas, e o termo *grafo de conhecimento* não constitui uma nova tecnologia. Em vez disso, é uma *buzzword* reinventada pela Google e adotada por outras empresas e pela academia para descrever diferentes aplicações de representação de conhecimento. Propusemos uma definição de grafo de conhecimento para promover uma discussão e uma visão comum para trabalhos futuros nessa área. Existem diferenças essenciais na maneira como aplicações de representação de conhecimento (cf. Seção 3) são construídas, variando de bases de conhecimento totalmente construídas à mão até grafos de conhecimento extraídos e processados automaticamente. Consequentemente, o termo *grafo de conhecimento* não é adequado para descrever todas essas aplicações e deveria ser usado com mais cuidado. Várias aplicações não precisam ser chamadas de grafos de conhecimento, pois os termos *base de conhecimento* e *ontologia* as descrevem suficientemente e com mais precisão. Levando em conta as aplicações diversas, um KG guarda maior semelhança com um *framework* abstrato do que com uma estrutura matemática. Nossa pesquisa em andamento foca em uma análise aprofundada de nossa definição em relação a implementações existentes de KGs, bem como a avaliação da qualidade dos dados em grafos de conhecimento e suas fontes acessadas.

---

## 6. Referências

[1] R. Akerkar e P. Sajja. *Knowledge-Based Systems*. Jones and Bartlett Publishers, USA, 1ª edição, 2009.

[2] R. Blanco, B. B. Cambazoglu, P. Mika e N. Torzec. *Entity Recommendations in Web Search*. In Proceedings of the 12th International Semantic Web Conference - Part II, ISWC '13, p. 33-48, New York, USA, 2013. Springer.

[3] A. Blumauer. *From Taxonomies over Ontologies to Knowledge Graphs*, julho de 2014. https://blog.semantic-web.at/2014/07/15/from-taxonomies-over-ontologies-to-knowledge-graphs [Agosto de 2016].

[4] J. Davies, R. Studer e P. Warren. *Semantic Web Technologies: Trends and Research in Ontology-based Systems*. John Wiley & Sons, 2006.

[5] X. Dong, E. Gabrilovich, G. Heitz, W. Horn, N. Lao, K. Murphy, T. Strohmann, S. Sun e W. Zhang. *Knowledge Vault: A Web-scale Approach to Probabilistic Knowledge Fusion*. In Proceedings of the 20th ACM SIGKDD International Conference on Knowledge Discovery and Data Mining, KDD '14, p. 601-610, New York, USA, 2014. ACM.

[6] J. Euzenat e P. Shvaiko. *Ontology Matching*. Springer, Secaucus, NJ, USA, 2007.

[7] M. Färber, B. Ell, C. Menne, A. Rettinger e F. Bartscherer. *Linked Data Quality of DBpedia, Freebase, OpenCyc, Wikidata, and YAGO*. Semantic Web Journal, 2016.

[8] M. Färber e A. Rettinger. *A Statistical Comparison of Current Knowledge Bases*. In Joint Proceedings of the Posters and Demos Track of 11th International Conference on Semantic Systems - SEMANTiCS2015 and 1st Workshop on Data Science: Methods, Technology and Applications (DSci15), p. 18-21. CEUR Workshop Proceedings, 2015.

[9] C. Feilmayr e W. Wöß. *An Analysis of Ontologies and their Success Factors for Application to Business*. Data & Knowledge Engineering, 101:1-23, 2016.

[10] P. James. *Knowledge Graphs*. In Linguistic Instruments in Knowledge Engineering, p. 97-117. Elsevier Science Publishers B.V., 1992.

[11] S. Krause, L. Hennig, A. Moro, D. Weißenborn, F. Xu, H. Uszkoreit e R. Navigli. *Sar-graphs: A Language Resource Connecting Linguistic Knowledge with Semantic Relations from Knowledge Graphs*. Journal of Web Semantics, Edição Especial sobre Grafos de Conhecimento(C):112-131, março de 2016.

[12] M. Kroetsch e G. Weikum. *Journal of Web Semantics: Special Issue on Knowledge Graphs*. http://www.websemanticsjournal.org/index.php/ps/announcement/view/19 [Agosto de 2016].

[13] Y. Ma, P. A. Crook, R. Sarikaya e E. Fosler-Lussier. *Knowledge Graph Inference for Spoken Dialog Systems*. In Proceedings of 40th IEEE International Conference on Acoustics, Speech and Signal Processing (ICASSP) 2015. IEEE, abril de 2015.

[14] P. Mika, T. Tudorache, A. Bernstein, C. Welty, C. A. Knoblock, D. Vrandečić, P. T. Groth, N. F. Noy, K. Janowicz e C. A. Goble, editores. *The Semantic Web - ISWC 2014 - 13th International Semantic Web Conference, Riva del Garda, Italy, October 19-23, 2014. Proceedings, Part I*, volume 8796 de Lecture Notes in Computer Science. Springer, 2014.

[15] S. Nurdiati e C. Hoede. *25 Years Development of Knowledge Graph Theory: The Results and the Challenge*, setembro de 2008.

[16] H. Paulheim. *Knowledge Graph Refinement: A Survey of Approaches and Evaluation Methods*. Semantic Web Journal, (Preprint):1-20, 2016.

[17] J. Pujara, H. Miao, L. Getoor e W. Cohen. *Knowledge Graph Identification*. In Proceedings of the 12th International Semantic Web Conference - Part I, ISWC '13, p. 542-557, New York, USA, 2013. Springer.

[18] A. Singhal. *Introducing the Knowledge Graph: Things, not Strings*, maio de 2012. https://googleblog.blogspot.co.at/2012/05/introducing-knowledge-graph-things-not.html [Agosto de 2016].

[19] T. Steiner, R. Verborgh, R. Troncy, J. Gabarró Vallés e R. Van de Walle. *Adding Realtime Coverage to the Google Knowledge Graph*. In Poster and Demo Proceedings of the 11th International Semantic Web Conference, novembro de 2012.

[20] F. M. Suchanek e G. Weikum. *Knowledge Bases in the Age of Big Data Analytics*. Proceedings of the VLDB Endowment, 7(13):1713-1714, agosto de 2014.

[21] A. Tonon, M. Catasta, R. Prokofyev, G. Demartini, K. Aberer e P. Cudré-Mauroux. *Contextualized Ranking of Entity Types Based on Knowledge Graphs*. Journal of Web Semantics, Edição Especial sobre Grafos de Conhecimento(C):170-183, março de 2016.

---

## Resumo dos pontos-chave para o nosso paper

> Esta seção é **anotação minha**, não faz parte do paper original. É um guia rápido do que extrair desta leitura para o artigo `papers/http-session/article.tex`.

**Citação primária a usar:** A definição da Seção 4:
> *"Um grafo de conhecimento adquire e integra informação em uma ontologia e aplica um reasoner para derivar novo conhecimento."*

Esta é a citação canônica que legitima a escolha de OWL + motor de regras como arquitetura do nosso arcabouço. Aparece em quase todos os papers de KG-em-cibersegurança.

**Argumento secundário útil:** Os autores explicitamente distinguem KG de base de conhecimento estática: KG requer **(i) integração de fontes** e **(ii) motor de raciocínio para derivar novo conhecimento**. Nosso arcabouço atende ambos (eventos de tráfego como fontes integradas, regras semânticas como motor de raciocínio em tempo de execução), enquanto Jia 2018 e Bonagiri 2024 só atendem (i) sobre texto, sem (ii) em runtime.

**Onde citar no nosso artigo:**
- Seção 2.1 (Grafos de Conhecimento em Cibersegurança) — para fundamentar o termo
- Seção 3.2 (Ontologia Centrada em Sessão) — para legitimar a arquitetura
