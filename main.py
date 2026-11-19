"""
Pipeline completo do projeto:
  1) preparar dados (tratamento de valores ausentes + agregacao diaria + features)
  2) minerar (padronizacao, outliers, clustering por similaridade/distancia)
  3) interpretar com apoio da LLM (Claude API) a partir do resumo agregado
  4) gerar graficos e o relatorio final em Markdown

Uso:
    python main.py
"""
import json
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from src import analysis, charts, data_prep, llm_interpret

load_dotenv()

APP_DIR = Path(__file__).resolve().parent
OUT_DIR = APP_DIR / "outputs"


def montar_relatorio(resumo: dict, interpretacao: str) -> str:
    linhas = ["# Relatorio Final - Analise de Padroes de Consumo Eletrico Residencial\n"]

    linhas.append("## 1. Estatisticas gerais\n")
    for k, v in resumo["stats_gerais"].items():
        linhas.append(f"- **{k}**: {v}")
    linhas.append("")

    linhas.append("## 2. Clusters de padrao de consumo (K-Means, similaridade/distancia)\n")
    for c in resumo["clusters"]:
        linhas.append(
            f"- **Cluster {c['cluster']}** ({c['n_dias']} dias, {c['pct_dias']}%): "
            f"consumo medio {c['active_energy_kwh_media']} kWh/dia, "
            f"{c['pct_fim_de_semana']}% em fins de semana, "
            f"estacao predominante: {c['estacao_predominante']}."
        )
    linhas.append("")
    linhas.append("![Perfil dos clusters](grafico_perfil_clusters.png)\n")

    linhas.append("## 3. Outliers detectados (metodo IQR)\n")
    for o in resumo["outliers"][:10]:
        linhas.append(
            f"- {o['data']}: {o['active_energy_kwh']} kWh "
            f"({o['desvio_pct_da_media']:+.1f}% da media), estacao {o['estacao']}"
        )
    linhas.append("")
    linhas.append("![Consumo diario com outliers](grafico_consumo_diario.png)\n")

    linhas.append("## 4. Interpretacao com apoio da LLM\n")
    linhas.append(interpretacao)

    return "\n".join(linhas)


def run():
    daily_path = APP_DIR / "data" / "daily_consumption.csv"
    if daily_path.exists():
        print("[main] dados diarios ja processados, pulando etapa 1 (apague o CSV para reprocessar)")
        daily_prep = pd.read_csv(daily_path, index_col="date", parse_dates=True)
    else:
        daily_prep = data_prep.run()

    resultado = analysis.run()

    daily_analisado = pd.read_csv(OUT_DIR / "daily_consumption_analisado.csv", index_col=0, parse_dates=True)
    charts.run(daily_analisado)

    interpretacao = llm_interpret.run()

    relatorio = montar_relatorio(resultado, interpretacao)
    with open(OUT_DIR / "relatorio_final.md", "w", encoding="utf-8") as f:
        f.write(relatorio)

    print(f"\n[main] pipeline concluido. Relatorio final em {OUT_DIR / 'relatorio_final.md'}")


if __name__ == "__main__":
    run()
