"""
Etapa 3 - Interpretacao com apoio de LLM (API da Groq)

Regra de uso responsavel: so enviamos o JSON agregado (medias por cluster,
outliers com data e desvio percentual, estatisticas gerais) - nunca o dataset
bruto. O dataset em si ja nao contem dado pessoal (residencia unica anonima),
mas mesmo assim mantemos o principio de so expor resultados ja minerados.

A LLM NAO faz mineracao: ela apenas interpreta/sintetiza o que a etapa
estatistica (src/analysis.py) ja calculou.
"""
import json
from pathlib import Path

from groq import APIStatusError, Groq

OUT_DIR = Path(__file__).resolve().parent.parent / "outputs"
RESUMO_PATH = OUT_DIR / "resumo_agregado.json"
REPORT_PATH = OUT_DIR / "interpretacao_llm.md"

MODEL = "openai/gpt-oss-120b"

SYSTEM_PROMPT = (
    "Voce e um assistente de apoio a um projeto academico de Mineracao de Dados. "
    "Voce recebe SOMENTE resultados agregados (ja minerados) de uma analise de "
    "consumo eletrico residencial - nunca dados brutos. Sua tarefa e interpretar "
    "e sintetizar esses resultados em linguagem natural, em portugues, sugerindo "
    "possiveis explicacoes comportamentais e sazonais plausiveis. Nao invente "
    "numeros que nao estejam no resumo fornecido."
)

USER_PROMPT_TEMPLATE = """\
Abaixo esta o resumo agregado de uma analise de consumo eletrico de uma unica \
residencia (dados publicos e anonimos, UCI Machine Learning Repository), apos \
tratamento de valores ausentes, padronizacao, deteccao de outliers (metodo IQR) \
e agrupamento (K-Means) por similaridade de padrao de consumo.

```json
{resumo_json}
```

Com base APENAS nesses dados agregados, escreva uma interpretacao em portugues \
contendo:
1. Uma descricao do que cada cluster parece representar (ex.: "consumo alto, \
concentrado no inverno, dias de semana").
2. Hipoteses plausiveis sobre os habitos domesticos que explicariam essas \
diferencas entre clusters.
3. Um comentario sobre os dias identificados como outliers - o que pode ter \
causado esses picos/quedas atipicos de consumo.
4. Uma conclusao curta (3-4 frases) sintetizando os principais achados.

Formate a resposta em Markdown com esses 4 topicos.
"""


def montar_prompt() -> str:
    with open(RESUMO_PATH, "r", encoding="utf-8") as f:
        resumo = json.load(f)
    resumo_json = json.dumps(resumo, ensure_ascii=False, indent=2)
    return USER_PROMPT_TEMPLATE.format(resumo_json=resumo_json)


def run() -> str:
    prompt = montar_prompt()

    try:
        client = Groq()  # le GROQ_API_KEY do ambiente
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=2000,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        texto = response.choices[0].message.content or ""

        with open(REPORT_PATH, "w", encoding="utf-8") as f:
            f.write("# Interpretacao da LLM sobre os padroes de consumo\n\n")
            f.write(texto)

        print(f"[llm] interpretacao salva em {REPORT_PATH}")
        return texto

    except APIStatusError as e:
        aviso = (
            f"[llm] Erro ao chamar a API da Groq ({e.status_code}): {e.message}. "
            "Verifique se GROQ_API_KEY esta configurada corretamente (copie "
            ".env.example para .env e preencha). O prompt que seria enviado foi "
            "salvo em outputs/prompt_llm.txt para conferencia."
        )
        print(aviso)
        with open(OUT_DIR / "prompt_llm.txt", "w", encoding="utf-8") as f:
            f.write(SYSTEM_PROMPT + "\n\n---\n\n" + prompt)
        return aviso
    except Exception as e:
        aviso = (
            f"[llm] Nao foi possivel chamar a API da Groq ({e}). Verifique se a "
            "variavel GROQ_API_KEY esta definida (copie .env.example para .env e "
            "preencha com sua chave em https://console.groq.com/keys). O prompt "
            "que seria enviado foi salvo em outputs/prompt_llm.txt para conferencia."
        )
        print(aviso)
        with open(OUT_DIR / "prompt_llm.txt", "w", encoding="utf-8") as f:
            f.write(SYSTEM_PROMPT + "\n\n---\n\n" + prompt)
        return aviso


if __name__ == "__main__":
    run()
