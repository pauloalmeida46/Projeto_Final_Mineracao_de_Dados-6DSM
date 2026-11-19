"""
Etapa 1 - Preparacao dos dados
Dataset: Individual Household Electric Power Consumption (UCI)
https://archive.ics.uci.edu/dataset/235/individual+household+electric+power+consumption

Le o arquivo bruto (medicoes por minuto), trata valores ausentes, agrega para
granularidade diaria e cria atributos de calendario (engenharia de atributos).
"""
from pathlib import Path

import numpy as np
import pandas as pd

RAW_PATH = Path(__file__).resolve().parent.parent / "data" / "household_power_consumption.txt"
OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "daily_consumption.csv"

NUMERIC_COLS = [
    "Global_active_power",
    "Global_reactive_power",
    "Voltage",
    "Global_intensity",
    "Sub_metering_1",
    "Sub_metering_2",
    "Sub_metering_3",
]


def season_for_month(month: int) -> str:
    # Hemisferio norte (residencia localizada na Franca)
    if month in (12, 1, 2):
        return "inverno"
    if month in (3, 4, 5):
        return "primavera"
    if month in (6, 7, 8):
        return "verao"
    return "outono"


def load_raw(path: Path = RAW_PATH) -> pd.DataFrame:
    df = pd.read_csv(
        path,
        sep=";",
        na_values=["?"],
        low_memory=False,
    )
    df["datetime"] = pd.to_datetime(df["Date"] + " " + df["Time"], format="%d/%m/%Y %H:%M:%S")
    df = df.drop(columns=["Date", "Time"]).set_index("datetime").sort_index()
    for col in NUMERIC_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def tratar_valores_ausentes(df: pd.DataFrame) -> pd.DataFrame:
    missing_pct = df[NUMERIC_COLS].isna().mean().mean() * 100
    print(f"[prep] valores ausentes antes do tratamento: {missing_pct:.2f}%")
    # interpolacao temporal: preenche lacunas curtas (minutos faltantes) de forma
    # coerente com a serie temporal, em vez de usar media global ou remover linhas.
    df[NUMERIC_COLS] = df[NUMERIC_COLS].interpolate(method="time", limit_direction="both")
    print(f"[prep] valores ausentes depois do tratamento: {df[NUMERIC_COLS].isna().mean().mean() * 100:.4f}%")
    return df


def agregar_por_dia(df: pd.DataFrame) -> pd.DataFrame:
    daily = pd.DataFrame(index=df.resample("D").size().index)

    # Potencia em kW medida a cada 1 minuto -> energia (kWh) = soma(kW) / 60
    daily["active_energy_kwh"] = df["Global_active_power"].resample("D").sum() / 60
    daily["reactive_energy_kwh"] = df["Global_reactive_power"].resample("D").sum() / 60

    # Sub-medicoes ja estao em Wh por minuto -> soma diaria / 1000 = kWh
    daily["sub_metering_1_kwh"] = df["Sub_metering_1"].resample("D").sum() / 1000
    daily["sub_metering_2_kwh"] = df["Sub_metering_2"].resample("D").sum() / 1000
    daily["sub_metering_3_kwh"] = df["Sub_metering_3"].resample("D").sum() / 1000

    daily["avg_voltage"] = df["Voltage"].resample("D").mean()
    daily["avg_intensity"] = df["Global_intensity"].resample("D").mean()

    daily = daily.dropna()
    return daily


def engenharia_de_atributos(daily: pd.DataFrame) -> pd.DataFrame:
    daily = daily.copy()
    daily["day_of_week"] = daily.index.dayofweek  # 0 = segunda
    daily["is_weekend"] = daily["day_of_week"].isin([5, 6]).astype(int)
    daily["month"] = daily.index.month
    daily["season"] = daily["month"].apply(season_for_month)
    # energia nao contabilizada pelas 3 sub-medicoes (resto da casa: fogao, iluminacao etc.)
    daily["other_energy_kwh"] = (
        daily["active_energy_kwh"]
        - daily["sub_metering_1_kwh"]
        - daily["sub_metering_2_kwh"]
        - daily["sub_metering_3_kwh"]
    ).clip(lower=0)
    return daily


def run() -> pd.DataFrame:
    print("[prep] lendo arquivo bruto...")
    df = load_raw()
    df = tratar_valores_ausentes(df)
    print("[prep] agregando por dia...")
    daily = agregar_por_dia(df)
    daily = engenharia_de_atributos(daily)
    daily.to_csv(OUT_PATH, index_label="date")
    print(f"[prep] {len(daily)} dias processados -> {OUT_PATH}")
    return daily


if __name__ == "__main__":
    run()
