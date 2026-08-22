# Distribuição real de JA4 — tráfego de produção (CDN edge)

Medida em 2026-08-22 no log `stats` já existente de um nó de edge em produção
(`/var/log/nginx/global/access_content_delivery.log`, campo 56 =
`$parsed_botmanager_fingerprint`, que carrega o JA4 do TLS).

    requisições = 6.329.649
    distintos   = 495
    top-1       = 38,37%
    top-10      = 93,82%

Cabeça da distribuição (contagem | JA4):

    2428420  t13d1514h2_8daaf6152771_bc9a4605e104
    1069459  t13d1514h2_8daaf6152771_f87c85e88c23
     905932  t13d1312h2_f57a46bbacb6_ab7e3b40a677
     395458  t13d1513h2_8daaf6152771_352634941f3a
     366452  t13d1513h2_8daaf6152771_eca864cca44a
     264086  t13d1513h2_8daaf6152771_11eee41c8a31
     230253  t13d1313h2_f57a46bbacb6_7f0f34a4126d
     146574  t13d1713h2_5b57614c22b0_7f0f34a4126d
      67613  t13d1515h2_8daaf6152771_b68114bf320e
      64301  t13d1515h2_8daaf6152771_de2ff5557b0e

Aparecem também fingerprints QUIC/HTTP-3 (`q13d0309h3_...`), ou seja, população
real e moderna.

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

1. **Ponderação por requisição, não por sessão** — o log não traz identificador de
   conexão (`$sessionid` = `-`), então um cliente que busca muitos objetos pesa
   várias vezes. Isso, se algo, **superestima** a concentração; é conservador para
   nós.
2. **Uma janela, um PoP** — recorte contíguo do arquivo corrente (o `timeout 120`
   truncou a leitura dos 19,4 GB), não o período completo.
3. O agregado contém apenas fingerprints de *software cliente* e contagens — sem
   host, IP, URI, user agent ou JA4H. Uso em publicação depende de autorização
   formal do detentor do dado.

## Como reproduzir

    awk -F'\t' '$56!="-" {print $56}' access_content_delivery.log \
      | sort | uniq -c | sort -rn > ja4_hist.txt
