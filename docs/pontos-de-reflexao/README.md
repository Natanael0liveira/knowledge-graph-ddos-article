# Pontos de Reflexão

Pasta com **questões abertas** e **verificações de prior art** para o paper [`papers/http-session`](../../papers/http-session/) que precisam ser revistas antes de fechar a defesa do argumento.

Diferente de [`docs/leituras-pt/`](../leituras-pt/) — que contém resumos em PT-BR de papers já lidos — esta pasta é sobre **decisões ainda em aberto**: claims que precisam ser validados, papers que precisam ser lidos com cuidado antes da submissão, e revisões de framing que dependem dessa leitura.

## Estrutura

| Arquivo | Conteúdo |
|---|---|
| [`01-mitigacao-cirurgica-prior-art.md`](01-mitigacao-cirurgica-prior-art.md) | Análise de *prior art* para o argumento de **mitigação cirúrgica via cadeia de evidência + escopo derivado do *cluster***. Veredicto por componente da contribuição. Reformulação proposta do *abstract*. |
| [`02-leituras-e-links.md`](02-leituras-e-links.md) | Lista plana de links a acessar — papers prioritários, blogs técnicos da indústria, documentação de produtos. Cada entrada com **prioridade**, **por que ler** e **o que verificar**. |

## Como usar esta pasta

1. **Antes de escrever §1 (Introdução) ou §3 (Abordagem)**: ler [`01-mitigacao-cirurgica-prior-art.md`](01-mitigacao-cirurgica-prior-art.md) para confirmar/refutar o framing da contribuição.
2. **Antes da submissão**: percorrer [`02-leituras-e-links.md`](02-leituras-e-links.md) — todo item marcado **CRÍTICO** precisa estar checado ou citado.
3. **Quando ler um dos papers prioritários**: produzir resumo em [`docs/leituras-pt/`](../leituras-pt/) e atualizar a entrada correspondente aqui marcando como ✅ lido.

## Origem

Este conjunto de reflexões surgiu da varredura de *prior art* feita em **2026-05-18** após o argumento de "mitigação cirúrgica como contribuição central" emergir na conversa. A varredura cobriu:

- Indústria: Cloudflare, Akamai, DataDome, Castle, Auth0, A10, AWS, Imperva.
- Academia recente: KnowGraph (CCS '24), KGs+LLM para detecção de ameaça (ScienceDirect 2025), explainable DoS via SHAP (arxiv 2511.04114).
- Padrões: STIX 2.1, OWASP, MITRE ATT&CK.

Resultado: três componentes da nossa contribuição genuinamente novos em literatura acadêmica revisada, dois componentes vizinhos a indústria proprietária que precisam de framing cuidadoso. Detalhamento em [`01-mitigacao-cirurgica-prior-art.md`](01-mitigacao-cirurgica-prior-art.md).
