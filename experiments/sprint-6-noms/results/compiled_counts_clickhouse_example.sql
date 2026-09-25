-- Compiled from ddos_ontology.owl by compile_counts.py; do not edit.
-- plan: {"unit": "originatesFrom", "partition": {"relation": "relatedByEndpointConvergence", "key": "targets", "weight": 0.6}, "classes": [{"relation": "relatedByTLSFingerprint", "key": "tlsJa4", "weight": 1.0}, {"relation": "relatedByNetworkProximity", "key": "srcPrefix", "weight": 0.3}], "pairwise": ["relatedByPayloadSignature", "relatedByReusedIdentity", "relatedByTemporalPattern"]}

-- Omega per window and endpoint
WITH s AS (SELECT toStartOfInterval(ts, INTERVAL 5 MINUTE) AS w, host AS e, client_ip AS o, nullIf(ja4, '-') AS k0, if(position(client_ip, ':') > 0, cutIPv6(IPv6StringToNum(client_ip), 10, 0), arrayStringConcat(arraySlice(splitByChar('.', client_ip), 1, 3), '.')) AS k1 FROM access_log WHERE ts >= toDateTime('2026-09-23 00:00:00', 'UTC') AND ts < toDateTime('2026-09-24 00:00:00', 'UTC')),
     tot AS (SELECT w, e, COUNT(DISTINCT o) AS cnt FROM s GROUP BY w, e),
     c0 AS (SELECT w, e, k0 AS v, COUNT(DISTINCT o) AS cnt FROM s WHERE k0 IS NOT NULL GROUP BY w, e, k0),
     p0 AS (SELECT w, e, SUM(cnt * (cnt - 1) / 2) AS pairs FROM c0 GROUP BY w, e),
     c1 AS (SELECT w, e, k1 AS v, COUNT(DISTINCT o) AS cnt FROM s WHERE k1 IS NOT NULL GROUP BY w, e, k1),
     p1 AS (SELECT w, e, SUM(cnt * (cnt - 1) / 2) AS pairs FROM c1 GROUP BY w, e)
SELECT tot.w AS win, tot.e AS endpoint, tot.cnt AS origins,
       COALESCE(p0.pairs, 0) AS pairs_relatedByTLSFingerprint,
       COALESCE(p1.pairs, 0) AS pairs_relatedByNetworkProximity,
       0.6 * tot.cnt * (tot.cnt - 1) / 2
     + 1.0 * COALESCE(p0.pairs, 0)
     + 0.3 * COALESCE(p1.pairs, 0) AS omega
FROM tot LEFT JOIN p0 ON p0.w = tot.w AND p0.e = tot.e LEFT JOIN p1 ON p1.w = tot.w AND p1.e = tot.e
ORDER BY 1, 2;

-- class sizes of relatedByTLSFingerprint
WITH s AS (SELECT toStartOfInterval(ts, INTERVAL 5 MINUTE) AS w, host AS e, client_ip AS o, nullIf(ja4, '-') AS k0, if(position(client_ip, ':') > 0, cutIPv6(IPv6StringToNum(client_ip), 10, 0), arrayStringConcat(arraySlice(splitByChar('.', client_ip), 1, 3), '.')) AS k1 FROM access_log WHERE ts >= toDateTime('2026-09-23 00:00:00', 'UTC') AND ts < toDateTime('2026-09-24 00:00:00', 'UTC'))
SELECT w AS win, e AS endpoint, k0 AS value, COUNT(DISTINCT o) AS origins FROM s WHERE k0 IS NOT NULL GROUP BY w, e, k0;

-- class sizes of relatedByNetworkProximity
WITH s AS (SELECT toStartOfInterval(ts, INTERVAL 5 MINUTE) AS w, host AS e, client_ip AS o, nullIf(ja4, '-') AS k0, if(position(client_ip, ':') > 0, cutIPv6(IPv6StringToNum(client_ip), 10, 0), arrayStringConcat(arraySlice(splitByChar('.', client_ip), 1, 3), '.')) AS k1 FROM access_log WHERE ts >= toDateTime('2026-09-23 00:00:00', 'UTC') AND ts < toDateTime('2026-09-24 00:00:00', 'UTC'))
SELECT w AS win, e AS endpoint, k1 AS value, COUNT(DISTINCT o) AS origins FROM s WHERE k1 IS NOT NULL GROUP BY w, e, k1;
