# Real JA4 distribution — production traffic (CDN edge)

> **Authorization status.** These aggregates come from third-party production
> traffic operated by Azion Technologies. This file keeps only the statistics the
> paper actually cites. The log path, configuration variable name, fingerprint
> list and point-of-presence volume were removed: none is used by the paper, and
> exposing them buys nothing.
>
> ⚠️ **Check before camera-ready.** This file was written while formal
> authorization was pending. The paper now carries an acknowledgment stating that
> Azion Technologies authorized the measurement. Confirm which is current and
> align the two.

Measured on 2026-08-22 from an access log the platform already collects, at a
production edge node. The extract holds only **client-software** fingerprints and
their frequencies: no address, host, URI, header, user agent, JA4H or session
identifier.

    distinct  = 495
    top-1     = 38.37%
    top-10    = 93.82%

The tail includes QUIC/HTTP-3 fingerprints, so the population is real and modern.

## Against what the paper assumed

| Source | Distinct | Top-1 | Top-10 |
|---|---|---|---|
| CICIDS2017 (laboratory) | 39 | 52.7% | 98.4% |
| **Production (CDN edge)** | **495** | **38.37%** | **93.82%** |
| Generator, α = 1.5 (canonical) | — | 38.95% | 77.7% |
| Generator, α = 2.0 | — | 60.81% | 94.2% |

**The canonical setting hits the head almost exactly** (38.95% against 38.37%
measured). The real curve is not pure Zipf: its head matches α = 1.5 and its
top-10 matches α = 2.0, so the sweep we already ran **brackets** the real
distribution. The laboratory testbed is *more* concentrated than production
(52.7% against 38.4%), confirming that lab-measured shape overstates
concentration.

## Caveats, all stated in the paper

1. **Weighted per request, not per session.** The log carries no connection
   identifier, so a client fetching many objects counts several times. If
   anything this **overstates** concentration, which is conservative for us.
2. **One window, one point of presence.** A contiguous slice of the current file,
   not the full period.
3. Publication use depends on formal authorization from the data owner.

## Reproduction

The procedure is a histogram over the access log's TLS fingerprint field. Path
and configuration details stay with the data owner and will be added here if and
when authorization permits.
