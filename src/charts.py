"""
Graficos de apoio ao relatorio final (nao sao enviados a LLM).
Paleta fixa e categorica (ordem estavel por cluster), uma cor de destaque para outliers.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

OUT_DIR = Path(__file__).resolve().parent.parent / "outputs"

CLUSTER_COLORS = ["#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B2"]
OUTLIER_COLOR = "#C44E52"
BASE_COLOR = "#4C72B0"
MUTED_GRID = "#D9D9D9"


def grafico_consumo_diario(daily: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(daily.index, daily["active_energy_kwh"], color=BASE_COLOR, linewidth=1, label="Consumo diario")

    outliers = daily[daily["is_outlier"]]
    ax.scatter(outliers.index, outliers["active_energy_kwh"], color=OUTLIER_COLOR, s=18, zorder=3, label="Outlier (IQR)")

    ax.set_title("Consumo ativo diario de energia (kWh)")
    ax.set_ylabel("kWh/dia")
    ax.grid(True, color=MUTED_GRID, linewidth=0.6)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, loc="upper left")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "grafico_consumo_diario.png", dpi=150)
    plt.close(fig)


def grafico_perfil_clusters(daily: pd.DataFrame):
    cols = ["sub_metering_1_kwh", "sub_metering_2_kwh", "sub_metering_3_kwh", "other_energy_kwh"]
    labels = ["Cozinha", "Lavanderia", "Aquecedor/AC", "Outros"]
    perfil = daily.groupby("cluster")[cols].mean()

    fig, ax = plt.subplots(figsize=(8, 4.5))
    bottom = pd.Series(0, index=perfil.index, dtype=float)
    palette = ["#4C72B0", "#DD8452", "#55A868", "#8172B2"]
    for col, label, color in zip(cols, labels, palette):
        ax.bar(perfil.index.astype(str), perfil[col], bottom=bottom, label=label, color=color, width=0.6)
        bottom += perfil[col]

    ax.set_title("Perfil medio de consumo por cluster (kWh/dia)")
    ax.set_xlabel("Cluster")
    ax.set_ylabel("kWh/dia (medio)")
    ax.grid(True, axis="y", color=MUTED_GRID, linewidth=0.6)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, loc="upper right", fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "grafico_perfil_clusters.png", dpi=150)
    plt.close(fig)


def run(daily: pd.DataFrame):
    grafico_consumo_diario(daily)
    grafico_perfil_clusters(daily)
    print(f"[charts] graficos salvos em {OUT_DIR}")
