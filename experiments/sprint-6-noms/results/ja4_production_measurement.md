# Distribuição real de JA4 — tráfego de produção (CDN edge)

> **Estado da autorização.** Estes agregados vêm de tráfego de produção de
> terceiros operado pela Azion Technologies. A autorização formal para uso em
> publicação **está pendente**. Até que ela saia, este arquivo mantém apenas as
> estatísticas que o artigo de fato cita. Caminho do log, nome de variável de
> configuração, lista de fingerprints e volume do ponto de presença foram
> removidos: nada disso é usado pelo artigo e a exposição não tem contrapartida.

Medida em 2026-08-22 sobre um log de acesso que a plataforma já coleta, num nó
de edge em produção. O extrato contém apenas fingerprints de **software
cliente** e suas frequências — sem endereço, host, URI, cabeçalho, user agent,
JA4H ou identificador de sessão.

    distintos   = 495
    top-1       = 38,37%
    top-10      = 93,82%

A cauda inclui fingerprints QUIC/HTTP-3, ou seja, população real e moderna.

## Comparação com o que o artigo assumia

| fonte | distintos | top-1 | top-10 |
|---|---|---|---|
| CICIDS2017 (laboratório) | 39 | 52,7% | 98,4% |
| **produção (CDN edge)** | **495** | **38,37%** | **93,82%** |
| gerador, alpha=1,5 (canônico) | — | 38,95% | 77,7% |
| gerador, alpha=2,0 | — | 60,81% | 94,2% |

**O canônico acerta a cabeça quase na vírgula** (38,95% contra 38,37% medido). A
curva real não é Zipf puro: a cabeça bate com alpha=1,5 e o top-10 com alpha=2,0,
então o sweep que já fazíamos **contém** a distribuição real. E o testbed de
laboratório é *mais* concentrado que a produção (52,7% contra 38,4%), confirmando
que a forma medida em lab exagera a concentração.

## Ressalvas declaradas no artigo

1. **Ponderação por requisição, não por sessão** — o log não traz identificador
   de conexão, então um cliente que busca muitos objetos pesa várias vezes. Isso,
   se algo, **superestima** a concentração; é conservador para nós.
2. **Uma janela, um ponto de presença** — recorte contíguo do arquivo corrente,
   não o período completo.
3. Uso em publicação depende de autorização formal do detentor do dado.

## Reprodução

O procedimento é um histograma do campo de fingerprint TLS do log de acesso. Os
detalhes de caminho e configuração ficam com o detentor do dado e serão
acrescentados aqui se e quando a autorização permitir.
