"""
Etapa 2 - Mineracao de dados
Tecnicas aplicadas: padronizacao, deteccao de outliers (IQR),
similaridade e distancia via clustering (K-Means em espaco padronizado).

Gera apenas resultados agregados (medias por cluster, outliers com data e
desvio) - nenhum dado bruto e enviado para a LLM nesta etapa.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "daily_consumption.csv"
OUT_DIR = Path(__file__).resolve().parent.parent / "outputs"
OUT_DIR.mkdir(exist_ok=True)

FEATURES = [
    "active_energy_kwh",
    "reactive_energy_kwh",
    "sub_metering_1_kwh",
    "sub_metering_2_kwh",
    "sub_metering_3_kwh",
    "other_energy_kwh",
    "avg_voltage",
    "avg_intensity",
]

N_CLUSTERS = 4
RANDOM_STATE = 42


def detectar_outliers_iqr(daily: pd.DataFrame, col: str = "active_energy_kwh") -> pd.DataFrame:
    q1, q3 = daily[col].quantile([0.25, 0.75])
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    daily = daily.copy()
    daily["is_outlier"] = ~daily[col].between(lower, upper)
    daily["outlier_deviation_pct"] = ((daily[col] - daily[col].mean()) / daily[col].mean() * 100).round(1)
    n_out = int(daily["is_outlier"].sum())
    print(f"[analysis] outliers detectados (IQR em {col}): {n_out} de {len(daily)} dias")
    return daily


def padronizar_e_agrupar(daily: pd.DataFrame, n_clusters: int = N_CLUSTERS):
    scaler = StandardScaler()
    X = scaler.fit_transform(daily[FEATURES])

    kmeans = KMeans(n_clusters=n_clusters, random_state=RANDOM_STATE, n_init=10)
    labels = kmeans.fit_predict(X)
    daily = daily.copy()
    daily["cluster"] = labels
    return daily, scaler, kmeans


def resumir_clusters(daily: pd.DataFrame) -> list[dict]:
    resumo = []
    for c in sorted(daily["cluster"].unique()):
        sub = daily[daily["cluster"] == c]
        perfil = {
            "cluster": int(c),
            "n_dias": int(len(sub)),
            "pct_dias": round(len(sub) / len(daily) * 100, 1),
            "active_energy_kwh_media": round(sub["active_energy_kwh"].mean(), 2),
            "sub_metering_1_kwh_media": round(sub["sub_metering_1_kwh"].mean(), 2),
            "sub_metering_2_kwh_media": round(sub["sub_metering_2_kwh"].mean(), 2),
            "sub_metering_3_kwh_media": round(sub["sub_metering_3_kwh"].mean(), 2),
            "pct_fim_de_semana": round(sub["is_weekend"].mean() * 100, 1),
            "estacao_predominante": sub["season"].mode().iloc[0],
            "mes_predominante": int(sub["month"].mode().iloc[0]),
        }
        resumo.append(perfil)
    # ordena por consumo medio para leitura mais facil (do mais baixo ao mais alto)
    resumo.sort(key=lambda d: d["active_energy_kwh_media"])
    return resumo


def resumir_outliers(daily: pd.DataFrame, top_n: int = 15) -> list[dict]:
    outliers = daily[daily["is_outlier"]].copy()
    outliers = outliers.reindex(outliers["outlier_deviation_pct"].abs().sort_values(ascending=False).index)
    outliers = outliers.head(top_n)
    registros = []
    for date, row in outliers.iterrows():
        registros.append({
            "data": str(date.date()) if hasattr(date, "date") else str(date),
            "active_energy_kwh": round(row["active_energy_kwh"], 2),
            "desvio_pct_da_media": row["outlier_deviation_pct"],
            "estacao": row["season"],
            "fim_de_semana": bool(row["is_weekend"]),
        })
    return registros


def run() -> dict:
    daily = pd.read_csv(DATA_PATH, index_col="date", parse_dates=True)
    daily = detectar_outliers_iqr(daily)
    daily, scaler, kmeans = padronizar_e_agrupar(daily)

    cluster_summary = resumir_clusters(daily)
    outlier_summary = resumir_outliers(daily)

    stats_gerais = {
        "periodo_inicio": str(daily.index.min().date()),
        "periodo_fim": str(daily.index.max().date()),
        "n_dias_total": int(len(daily)),
        "active_energy_kwh_media_geral": round(daily["active_energy_kwh"].mean(), 2),
        "active_energy_kwh_desvio_padrao": round(daily["active_energy_kwh"].std(), 2),
        "n_outliers": int(daily["is_outlier"].sum()),
    }

    resultado = {
        "stats_gerais": stats_gerais,
        "clusters": cluster_summary,
        "outliers": outlier_summary,
    }

    daily.to_csv(OUT_DIR / "daily_consumption_analisado.csv")
    with open(OUT_DIR / "resumo_agregado.json", "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    print(f"[analysis] resumo agregado salvo em {OUT_DIR / 'resumo_agregado.json'}")
    print(f"[analysis] CSV detalhado (uso interno, nao enviado a LLM) em {OUT_DIR / 'daily_consumption_analisado.csv'}")
    return resultado


if __name__ == "__main__":
    run()
