# Paper: Detecção Cross-Surface DNS↔HTTP de DDoS em CDNs

**Status:** engavetado para uso futuro (não é o foco ativo)
**Idioma:** português
**Veículo-alvo provisório:** Computers & Security (Elsevier, Qualis A2) ou alternativa específica para CDN/infrastructure security

## Foco

Detecção de ataques DDoS de Camada 7 coordenados que exploram a arquitetura CDN tocando **duas superfícies operacionais em correlação**: a superfície DNS (servidores autoritativos da CDN, acessados via Anycast) e a superfície HTTP (PoPs de borda). O ataque coordenado canônico modelado é a combinação **QName Randomization** (na superfície DNS) com **Cache-Busting via *query string*** (na superfície HTTP) do mesmo cliente — onde cada fase individualmente fica sub-limiar mas a campanha agregada degrada o serviço.

A novidade está em modelar `CrossSurfaceAttack` como classe ontológica unificada, ligando eventos das duas superfícies via identidade compartilhada do cliente (ASN, prefixo, *fingerprint* TLS).

## Por que está engavetado

O paper [http-session](../http-session/) foi escolhido como foco primário por escopo mais enxuto e contribuição A1 (sessão como entidade semântica) mais defensável para um primeiro paper Qualis A2. Este paper CDN cross-surface foi mantido como direção de pesquisa subsequente — provavelmente um segundo paper depois que o primeiro for submetido e o programa amadurecer.

## Como compilar (quando voltar a trabalhar)

```bash
export LC_ALL=C
pdflatex -interaction=nonstopmode article.tex
bibtex article
pdflatex -interaction=nonstopmode article.tex
pdflatex -interaction=nonstopmode article.tex
```

O arquivo `references.bib` neste diretório é um *symlink* para `../../shared/references.bib`.

## Estado das seções

- **§1 Introdução** — escrita completa (Contexto, Definição do Problema, QPs, Contribuições, Organização)
- **§2-6 + Apêndice** — esqueletos em português marcados com `\textit{[Esqueleto.]}` indicando o que cada subseção vai conter

## Aviso de Conflito de Interesse

Se um dos autores tiver vínculo profissional com operadora de CDN, isso deve ser declarado na seção "Declaration of Competing Interest" do paper. Veja a discussão correspondente nas notas de planejamento do projeto.
