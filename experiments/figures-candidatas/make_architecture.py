#!/usr/bin/env python3
"""Candidata: diagrama de arquitetura (fig:architecture) — 4 estágios do §3.
Gera PNG em experiments/figures-candidatas/. NÃO é referenciada no .tex (revisão)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

# Paleta: tons de cinza + navy blue só em partes estratégicas (título, setas, destaque).
NAVY = "#1f3a5f"
HEADER = "#4a4a4a"   # cinza escuro p/ cabeçalhos
BODY = "#f2f2f2"     # cinza claro p/ corpo
BORDER = "#8c8c8c"
TEXT = "#222222"

STAGES = [
    ("1. Ingestão", [
        "Tráfego HTTP / PCAP",
        "→ eventos por requisição:",
        "JA4, IP/origem, endpoint,",
        "identidade, tempo",
    ]),
    ("2. Grafo de Conhecimento\n(populado em runtime)", [
        "ApplicationSession como nó",
        "hasIdentity · targets ·",
        "exhibitsBehavior",
        "família relatedBy_* ponderada",
        "(TLS 1.0 · endpoint 0.6 · rede 0.3)",
    ]),
    ("3. Regras semânticas\n(SPARQL / SWRL)", [
        "coordinatedHTTPFlood",
        "Ω(S) = Σ wᵢ·|pares relatedBy_i|",
        "dispara se Ω(S) ≥ τ",
        "+ convergência de endpoint",
        "+ taxa agregada",
    ]),
    ("4. Veredito + Evidência\n+ Mitigação", [
        "veredito = derivação simbólica",
        "cadeia JSON-LD / STIX 2.1",
        "escopo cirúrgico derivado",
        "(fingerprint TLS, endpoint)",
        "→ baixo dano colateral",
    ]),
]


def main():
    fig, ax = plt.subplots(figsize=(13, 4.6))
    ax.set_xlim(0, 4 * 3.1); ax.set_ylim(0, 4.6); ax.axis("off")
    w, h, x0, y = 2.7, 3.0, 0.15, 0.7
    centers = []
    for i, (title, items) in enumerate(STAGES):
        x = x0 + i * 3.1
        # estágio 4 (contribuição) recebe o destaque navy; demais em cinza
        head = NAVY if i == 3 else HEADER
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.06,rounding_size=0.12",
                             linewidth=1.5, edgecolor=head, facecolor=BODY)
        ax.add_patch(box)
        ax.add_patch(FancyBboxPatch((x, y + h - 0.62), w, 0.62,
                     boxstyle="round,pad=0.06,rounding_size=0.12",
                     linewidth=0, facecolor=head))
        ax.text(x + w/2, y + h - 0.31, title, ha="center", va="center",
                color="white", fontsize=10.5, fontweight="bold")
        for j, it in enumerate(items):
            ax.text(x + 0.16, y + h - 0.95 - j*0.42, it, ha="left", va="center",
                    fontsize=8.6, color=TEXT)
        centers.append((x + w, y + h/2 - 0.3))
    # setas (navy estratégico)
    for i in range(3):
        x_end = centers[i][0]
        ax.add_patch(FancyArrowPatch((x_end + 0.02, 2.0), (x_end + 0.38, 2.0),
                     arrowstyle="-|>", mutation_scale=18, linewidth=2, color=NAVY))
    ax.text(4*3.1/2, 4.35, "Arcabouço de detecção e mitigação centrado na sessão HTTP",
            ha="center", fontsize=12, fontweight="bold", color=NAVY)
    ax.text(4*3.1/2, 0.28, "tudo em tempo de execução sobre o tráfego — a unidade de raciocínio é a SESSÃO, não o nó de rede",
            ha="center", fontsize=8.5, style="italic", color="#555")
    fig.tight_layout()
    out = "experiments/figures-candidatas/fig_architecture.png"
    fig.savefig(out, dpi=160, bbox_inches="tight"); print(f"OK: {out}")


if __name__ == "__main__":
    main()
