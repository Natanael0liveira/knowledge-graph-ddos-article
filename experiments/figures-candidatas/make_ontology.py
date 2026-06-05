#!/usr/bin/env python3
"""Figura da ontologia interligada (fig:ontology) — sessão como entidade de 1ª classe.

ApplicationSession central com relações primárias (hasIdentity, targets, exhibitsBehavior,
originatesFrom) para entidades-satélite; a família relatedTo PONDERADA entre sessões (o
coração da contribuição) com as 6 sub-propriedades e pesos por tier; hierarquia de ataque;
e o acoplamento regra→veredito→mitigação. Paleta cinza + navy. Fiel a ontology/ddos_ontology.owl.
NÃO está no .tex (revisão).
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

NAVY = "#1f3a5f"
NAVY2 = "#34618c"
GRAY = "#ececec"
GRAYB = "#9a9a9a"
TXT = "#222222"

fig, ax = plt.subplots(figsize=(14, 9.5))
ax.set_xlim(0, 14); ax.set_ylim(0, 10); ax.axis("off")


def box(x, y, w, h, label, fc=GRAY, ec=GRAYB, tc=TXT, fs=9.5, bold=False, lw=1.3):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.04,rounding_size=0.10",
                                linewidth=lw, edgecolor=ec, facecolor=fc, zorder=3))
    ax.text(x + w/2, y + h/2, label, ha="center", va="center", fontsize=fs,
            color=tc, fontweight="bold" if bold else "normal", zorder=4)


def arrow(p1, p2, color=GRAYB, lw=1.4, rad=0.0, style="-|>"):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle=style, mutation_scale=14, linewidth=lw,
                 color=color, connectionstyle=f"arc3,rad={rad}", zorder=2))


def plabel(x, y, t, color="#555", fs=8.2):
    ax.text(x, y, t, ha="center", va="center", fontsize=fs, color=color, style="italic",
            zorder=5, bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.9))


ax.text(7, 9.7, "Ontologia centrada na sessão HTTP — entidade de 1ª classe e família relatedTo ponderada",
        ha="center", fontsize=12.5, fontweight="bold", color=NAVY)

# ---- sessões ----
box(3.5, 6.0, 2.9, 1.15, "ApplicationSession\n($S_i$)", fc=NAVY, ec=NAVY, tc="white", fs=11.5, bold=True)
box(9.4, 6.0, 2.9, 1.15, "ApplicationSession\n($S_j$)", fc=NAVY2, ec=NAVY, tc="white", fs=11.5, bold=True)
ax.text(10.85, 5.78, "(mesmas relações primárias de $S_i$)", ha="center", fontsize=7.8,
        style="italic", color="#777")

# ---- relatedTo entre as sessões (arco superior) ----
ax.add_patch(FancyArrowPatch((5.6, 7.15), (10.2, 7.15), arrowstyle="<|-|>", mutation_scale=17,
             linewidth=2.8, color=NAVY, connectionstyle="arc3,rad=-0.32", zorder=2))
ax.text(7.9, 8.7, "relatedTo  (entre sessões)", ha="center", fontsize=11,
        fontweight="bold", color=NAVY, zorder=6,
        bbox=dict(boxstyle="round,pad=0.22", fc="white", ec=NAVY, lw=1.3))

# ---- satélites de S_i (coluna esquerda) ----
sat = [
    (7.55, "Identity\n(Cookie / Token / JA4)", "hasIdentity"),
    (6.45, "IPAddress / Host", "originatesFrom"),
    (5.35, "Endpoint\n(API / Login / Checkout)", "targets"),
    (4.25, "Behavior\n(BotBehavior, …)", "exhibitsBehavior"),
]
for yc, lab, prop in sat:
    box(0.2, yc - 0.38, 2.5, 0.78, lab, fs=8.6)
    arrow((2.7, yc), (3.5, 6.55), rad=0.0)
    plabel(3.05, yc + 0.12 + (yc - 6.55) * 0.0, prop, fs=7.8)

# ---- caixa da família ponderada ----
ax.add_patch(FancyBboxPatch((4.0, 2.35), 9.7, 2.25, boxstyle="round,pad=0.06,rounding_size=0.08",
             linewidth=1.5, edgecolor=NAVY, facecolor="#f4f7fb", zorder=3))
ax.text(4.3, 4.42, "família relatedTo — 6 sub-propriedades ponderadas  (peso = custo de evasão p/ o atacante)",
        ha="left", va="top", fontsize=9.6, fontweight="bold", color=NAVY)
rows = [
    ("alto",  "relatedByTLSFingerprint",      "1,0"),
    ("alto",  "relatedByReusedIdentity",      "1,0"),
    ("alto",  "relatedByTemporalPattern",     "0,9"),
    ("médio", "relatedByEndpointConvergence", "0,6"),
    ("médio", "relatedByPayloadSignature",    "0,6"),
    ("baixo", "relatedByNetworkProximity",    "0,3"),
]
tier_c = {"alto": NAVY, "médio": "#6b6b6b", "baixo": "#a5a5a5"}
for i, (tier, name, w) in enumerate(rows):
    yy = 4.02 - i * 0.27
    ax.text(4.45, yy, "●", fontsize=9, color=tier_c[tier], va="center")
    ax.text(4.75, yy, f"{tier:<6}", fontsize=8.6, family="monospace", color=tier_c[tier], va="center")
    ax.text(5.85, yy, f"{name:<30}", fontsize=8.6, family="monospace", color=TXT, va="center")
    ax.text(11.7, yy, f"w = {w}", fontsize=8.6, family="monospace",
            color=tier_c[tier], va="center", fontweight="bold")
# conector arco→família
arrow((7.9, 7.0), (8.0, 4.6), color=NAVY, lw=1.3, rad=0.12)

# ---- hierarquia de ataque (inferior esquerdo) ----
ax.add_patch(FancyBboxPatch((0.2, 0.35), 5.35, 1.55, boxstyle="round,pad=0.05,rounding_size=0.08",
             linewidth=1.2, edgecolor=GRAYB, facecolor="white", zorder=3))
ax.text(0.45, 1.72, "Hierarquia de ataque (subclasses)", ha="left", fontsize=9, fontweight="bold", color="#444")
hier = ("DDoSAttack ▸ ApplicationLayerAttack ▸\n"
        "  SlowRequestAttack ▸ {Slowloris, SlowRead, SlowBody}\n"
        "  HTTPFlood ▸ CoordinatedHTTPFlood\n"
        "  CredentialStuffing, CoordinatedAPIAbuse")
ax.text(0.45, 1.42, hier, ha="left", va="top", fontsize=7.9, color=TXT, family="monospace")

# ---- regra → mitigação (inferior direito) ----
box(5.85, 0.55, 3.25, 1.15,
    "DetectionRule\nCoordinatedHTTPFlood\n$\\Omega(S)=\\sum_i w_i\\!\\cdot$pares ; dispara se $\\Omega\\!\\geq\\!\\tau$",
    fc=GRAY, ec=NAVY, fs=8.0, lw=1.4)
box(9.45, 0.55, 4.25, 1.15,
    "CourseOfAction\nmitigação cirúrgica\n(escopo do subconjunto coordenado)",
    fc=NAVY, ec=NAVY, tc="white", fs=8.2, lw=1.4)
arrow((9.1, 1.12), (9.45, 1.12), color=NAVY, lw=1.7)
plabel(9.28, 1.42, "mitigatedBy", color=NAVY, fs=7.8)
# behavior alimenta a regra
arrow((1.45, 4.0), (6.4, 1.7), color=GRAYB, lw=1.2, rad=-0.18)
plabel(3.0, 2.55, "exhibitsBehavior ⇒ regra sobre $\\Omega$", fs=7.6)

ax.text(7, 0.12, "Ontologia OWL alinhada a STIX 2.1 (indicator + course-of-action ligados por mitigates) e MITRE ATT&CK",
        ha="center", fontsize=8.6, style="italic", color="#666")

fig.tight_layout()
fig.savefig("experiments/figures-candidatas/fig_ontology.png", dpi=160, bbox_inches="tight")
print("OK: fig_ontology (v2)")
