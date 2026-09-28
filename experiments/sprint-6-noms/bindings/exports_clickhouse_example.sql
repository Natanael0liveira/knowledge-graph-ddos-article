-- The two exports the production evaluation reads (README.md, section 9), rebuilt from
-- their documented definitions for ClickHouse. Table and column names are placeholders:
--   access_log   the access-log table
--   event_time   the request timestamp (UTC)
--   host         the endpoint (one host per endpoint)
--   client_ip    the client address, IPv4 or IPv6, as a string
--   ja4          the request's JA4, '-' on plain HTTP
--   waf_blocked  a boolean expression: the WAF blocked this request
-- Set the time range (UTC, end exclusive) and the hosts of E1-E4 (roles.json) in both.
-- The output column names are the ones rule_detection_production.py reads.

-- E3: per host, 5-minute window and JA4, the distinct clients and those the WAF blocked
SELECT
    toStartOfInterval(event_time, INTERVAL 5 MINUTE) AS janela,
    host,
    ja4,
    uniqExact(client_ip)                AS clientes,
    uniqExactIf(client_ip, waf_blocked) AS clientes_bloqueados_waf
FROM access_log
WHERE event_time >= toDateTime('2026-09-26 00:00:00', 'UTC')
  AND event_time <  toDateTime('2026-10-01 00:00:00', 'UTC')
  AND host IN ('host-e1', 'host-e2', 'host-e3', 'host-e4')
GROUP BY janela, host, ja4
ORDER BY janela, host, ja4;

-- E4: per host and 5-minute window, the pairs of distinct clients that share a /24 (a /48
-- in IPv6), over the requests the WAF did not block, and the window's distinct clients
WITH s AS (
    SELECT
        toStartOfInterval(event_time, INTERVAL 5 MINUTE) AS janela,
        host,
        client_ip,
        if(position(client_ip, ':') > 0,
           cutIPv6(IPv6StringToNum(client_ip), 10, 0),
           arrayStringConcat(arraySlice(splitByChar('.', client_ip), 1, 3), '.')) AS prefixo,
        waf_blocked AS bloqueada
    FROM access_log
    WHERE event_time >= toDateTime('2026-09-26 00:00:00', 'UTC')
      AND event_time <  toDateTime('2026-10-01 00:00:00', 'UTC')
      AND host IN ('host-e1', 'host-e2', 'host-e3', 'host-e4')
),
por_prefixo AS (
    SELECT janela, host, prefixo, uniqExact(client_ip) AS k
    FROM s
    WHERE NOT bloqueada
    GROUP BY janela, host, prefixo
),
pares AS (
    SELECT janela, host, sum(k * (k - 1) / 2) AS pares_mesmo_prefixo
    FROM por_prefixo
    GROUP BY janela, host
),
tot AS (
    SELECT janela, host, uniqExact(client_ip) AS clientes
    FROM s
    GROUP BY janela, host
)
SELECT tot.janela AS janela, tot.host AS host, tot.clientes AS clientes,
       coalesce(pares.pares_mesmo_prefixo, 0) AS pares_mesmo_prefixo
FROM tot
LEFT JOIN pares ON pares.janela = tot.janela AND pares.host = tot.host
ORDER BY janela, host;
