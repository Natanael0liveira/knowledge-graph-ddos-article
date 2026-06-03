# Paper: Sessão como Entidade Semântica para Detecção de DDoS HTTP

**Status:** ativo (escopo principal de desenvolvimento)
**Idioma:** português
**Veículo-alvo provisório:** Computers & Security (Elsevier, Qualis A2)

## Foco

Detecção e explicação de ataques DDoS de Camada 7 sobre HTTP (HTTP Flood, Login Flood, abuso de API) tratando a **sessão HTTP como entidade semântica de primeira classe** em um grafo de conhecimento, e não como vetor de *features* agregadas.

A novidade está na capacidade de **raciocínio entre sessões**: ligar múltiplas sessões pela identidade compartilhada do cliente (cookie, *token*, *fingerprint* TLS, prefixo de IP) para detectar campanhas distribuídas que ficam sub-limiares em qualquer sessão isolada — *credential stuffing*, *scraping* orquestrado, abuso de API por frota de *tokens*.

## Citação curta da contribuição

> A sessão HTTP, tratada como entidade ontológica de primeira classe ligada por relações tipadas a identidade, *endpoint* e comportamento, habilita raciocínio entre sessões que detectores baseados em *features* agregadas de sessão estruturalmente não conseguem realizar.

## Como compilar

```bash
export LC_ALL=C
pdflatex -interaction=nonstopmode article.tex
bibtex article
pdflatex -interaction=nonstopmode article.tex
pdflatex -interaction=nonstopmode article.tex
```

O arquivo `references.bib` neste diretório é uma **cópia** de `../../shared/references.bib` (bibliografia compartilhada entre os dois papers). A cópia existe porque o Overleaf não importa repositórios com *symlinks*. Para sincronizar após editar o `shared/references.bib`, rode `./scripts/sync-bib.sh` na raiz do repositório.

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `article.tex` | Fonte LaTeX completa (Abstract, Introdução em pleno texto; demais seções como esqueletos a desenvolver) |
| `references.bib` | Cópia da bibliografia compartilhada (sync via `scripts/sync-bib.sh`) |
| `article.pdf` | Saída de compilação (gerada) |

## Estado das seções

- **§1 Introdução** — escrita completa (Contexto, Definição do Problema, QPs, Contribuições, Organização)
- **§2-6 + Apêndice** — esqueletos em português marcados com `\textit{[Esqueleto.]}` indicando o que cada subseção vai conter
