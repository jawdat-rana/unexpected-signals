"""Draw the "Two doors in" scatter: FARA clients vs foreign-connected PAC giving.

Usage: python analysis/money/chart_two_doors.py PACS_BY_COUNTRY_CSV FARA_CSV OUT_PNG
"""

import csv
import sys

import matplotlib.pyplot as plt

# FARA spells some countries differently from the parent-company list.
FARA_NAMES = {"South Korea": "Korea, South"}

INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#898781", "#e1e0d9"
COMPANIES, AGENTS, BOTH, OTHER = "#2a78d6", "#eb6834", "#1baf7a", "#c3c2b7"


# Label offsets in points; countries not listed stay unlabelled.
LABELS = {
    "Switzerland": (7, 4, "left"),
    "Germany": (7, 4, "left"),
    "United Kingdom": (7, 4, "left"),
    "Japan": (0, 10, "center"),
    "Canada": (7, 4, "left"),
    "Netherlands": (7, 4, "left"),
    "France": (7, 4, "left"),
    "South Korea": (7, 4, "left"),
    "Qatar": (0, 10, "center"),
    "United Arab Emirates": (0, 10, "center"),
    "Ukraine": (-2, 10, "right"),
    "Saudi Arabia": (2, 10, "left"),
}


def door(fara: int, pac_m: float) -> str:
    if pac_m >= 1.5 and fara >= 14:
        return BOTH
    if pac_m >= 0.3 and fara <= 10:
        return COMPANIES
    if pac_m < 0.25 and fara >= 20:
        return AGENTS
    return OTHER


def main(pac_csv: str, fara_csv: str, out: str) -> int:
    pacs = {r["country"]: float(r["to_committees"]) / 1e6 for r in csv.DictReader(open(pac_csv))}
    fara = {r["country"]: int(r["fara_clients"]) for r in csv.DictReader(open(fara_csv))}
    skip = {"International", *FARA_NAMES.values()}
    names = set(pacs) | {c for c, n in fara.items() if n >= 20 and c not in skip}
    pts = [(c, fara.get(FARA_NAMES.get(c, c), 0), pacs.get(c, 0.0)) for c in names]

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})
    fig, ax = plt.subplots(figsize=(8, 6.4), dpi=200)
    fig.patch.set_facecolor("#fcfcfb")
    ax.set_facecolor("#fcfcfb")
    for c, f, p in pts:
        col = door(f, p)
        ax.scatter(f, p, s=70, color=col, edgecolor="#fcfcfb", linewidth=2, zorder=3)
        if c in LABELS:
            name = c.replace("United Arab Emirates", "UAE").replace("United Kingdom", "UK")
            ax.annotate(
                name,
                (f, p),
                xytext=LABELS[c][:2],
                textcoords="offset points",
                fontsize=9.5,
                color=INK2,
                zorder=4,
                ha=LABELS[c][2],
            )
    ax.annotate(
        "Denmark, Belgium,\nSpain, Sweden",
        (3, 0.3),
        xytext=(30, -2),
        textcoords="offset points",
        ha="left",
        va="center",
        fontsize=8.5,
        color=MUTED,
    )
    ax.annotate(
        "Iraq, Turkey, China, Taiwan,\nIsrael, Venezuela, DR Congo …",
        (23.5, 0.05),
        xytext=(0, 48),
        textcoords="offset points",
        ha="center",
        fontsize=8.5,
        color=MUTED,
        arrowprops={"arrowstyle": "-", "color": MUTED, "lw": 0.8},
    )

    ax.set_xlim(-2, 70)
    ax.set_ylim(-0.25, 6.2)
    ax.grid(color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#c3c2b7")
    ax.tick_params(colors=MUTED, length=0)
    ax.yaxis.set_major_formatter(lambda v, _: f"${v:.0f}M")
    ax.set_xlabel("Foreign clients with registered U.S. agents (FARA), 2023–24", color=INK2)
    ax.set_ylabel("Given by U.S. PACs of foreign-owned firms, 2024 cycle", color=INK2)

    for txt, col in (
        ("Mostly through companies", COMPANIES),
        ("Mostly through hired agents", AGENTS),
        ("Both doors", BOTH),
    ):
        ax.scatter([], [], s=70, color=col, label=txt)
    ax.legend(frameon=False, loc="upper right", fontsize=9.5, labelcolor=INK2)

    fig.suptitle(
        "Two doors into Washington", x=0.07, ha="left", fontsize=16, color=INK, fontweight="bold"
    )
    fig.text(
        0.07,
        0.905,
        "How countries reach U.S. politics: through their companies' PACs, "
        "or through registered foreign agents",
        fontsize=10,
        color=INK2,
    )
    fig.text(
        0.07,
        0.02,
        "PAC money comes from U.S. employees, not foreign treasuries. "
        "Firms only legally domiciled abroad (e.g. Medtronic, Accenture) excluded.\n"
        "Sources: FEC bulk data, DOJ FARA eFile. Method and parent-company list: "
        "github.com/jawdat-rana/unexpected-signals",
        fontsize=7.5,
        color=MUTED,
    )
    fig.subplots_adjust(left=0.1, right=0.97, top=0.87, bottom=0.15)
    fig.savefig(out, facecolor=fig.get_facecolor())
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:4]))
