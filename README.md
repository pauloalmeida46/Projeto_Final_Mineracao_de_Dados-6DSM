# Analise de Padroes de Consumo Eletrico Residencial com Apoio de LLM

Projeto da disciplina de Mineracao de Dados. Dataset: [Individual Household
Electric Power Consumption](https://archive.ics.uci.edu/dataset/235/individual+household+electric+power+consumption)
(UCI Machine Learning Repository) - dados publicos e anonimos de uma unica
residencia na Franca, sem identificacao de pessoas.

## O que o pipeline faz

1. **`src/data_prep.py`** - le o arquivo bruto (medicoes por minuto), trata
   valores ausentes (interpolacao temporal), agrega para granularidade diaria
   e cria atributos de calendario (dia da semana, fim de semana, mes, estacao).
2. **`src/analysis.py`** - padroniza os atributos, detecta outliers (metodo
   IQR) e agrupa os dias por similaridade de padrao de consumo (K-Means em
   espaco padronizado = distancia euclidiana). Gera um resumo **agregado**
   (`outputs/resumo_agregado.json`) - nenhum dado bruto sai dessa etapa.
3. **`src/llm_interpret.py`** - envia **apenas o resumo agregado** para a API
   da Groq (modelo `openai/gpt-oss-120b`) e pede uma interpretacao em
   linguagem natural dos clusters e outliers encontrados.
4. **`src/charts.py`** - gera os graficos de apoio ao relatorio.
5. **`main.py`** - roda tudo em sequencia e monta `outputs/relatorio_final.md`.

## Resultado de exemplo

A pasta `outputs/` ja vem com o resultado de uma execucao completa (gerado com
o dataset real), para conferencia sem precisar rodar o pipeline:
[`outputs/relatorio_final.md`](outputs/relatorio_final.md).

## Como rodar

```bash
pip install -r requirements.txt
```

Baixe o dataset (arquivo grande, ~127 MB, nao fica no git) e coloque em
`data/household_power_consumption.txt`:

```bash
curl -L -o data/household_power_consumption.zip "https://archive.ics.uci.edu/static/public/235/individual+household+electric+power+consumption.zip"
unzip data/household_power_consumption.zip -d data/
```

Configure sua chave da API da Groq (necessaria so para a Etapa 3 - gratuita em
https://console.groq.com/keys):

```bash
cp .env.example .env
# edite .env e preencha GROQ_API_KEY=gsk_...
```

Rode o pipeline completo:

```bash
python main.py
```

Resultados em `outputs/`:
- `resumo_agregado.json` - o que foi minerado (clusters + outliers + stats)
- `interpretacao_llm.md` - a interpretacao gerada pela LLM
- `grafico_consumo_diario.png`, `grafico_perfil_clusters.png`
- `relatorio_final.md` - relatorio final juntando tudo

## Uso responsavel de dados

O dataset ja e publico e anonimo (nenhuma informacao de pessoas). Mesmo assim,
o projeto segue a regra da disciplina: a LLM so recebe resultados agregados
(medias por cluster, datas e desvio percentual de outliers) - nunca o CSV
bruto com as 2+ milhoes de leituras por minuto.
