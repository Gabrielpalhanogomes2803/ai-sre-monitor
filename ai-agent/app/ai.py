import json
import os

from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def analyze_incident(alert: dict, metrics: dict, logs: dict) -> dict:
    prompt = f"""
Você é um assistente de análise de incidentes SRE.

Analise o incidente estritamente com base nas evidências abaixo.

Regras:
- Responda em português do Brasil.
- Não invente fatos.
- Diferencie o estado atual do sistema do alerta que disparou a análise.
- Se as métricas atuais não confirmarem a condição do alerta, diga isso explicitamente.
- Resultados vazios do Loki significam apenas que não foram encontrados logs correspondentes na janela consultada.
- Não recomende ações destrutivas.
- Priorize ações seguras de diagnóstico.
- Seja direto e objetivo.
- O summary deve ter no máximo 2 frases curtas.
- probable_cause deve ter no máximo 2 frases curtas.
- Retorne no máximo 3 evidências.
- Retorne no máximo 3 ações recomendadas.
- Evite repetir informações entre summary, evidence e probable_cause.
- Não explique detalhes internos da regra como B=, C= ou expressões do Grafana, salvo se forem essenciais.
- Use horários no contexto local America/Sao_Paulo quando houver horário local disponível nas evidências.
- Retorne SOMENTE JSON válido.

Estrutura obrigatória:
{{
  "summary": "string",
  "probable_cause": "string",
  "evidence": ["string"],
  "recommended_actions": ["string"],
  "confidence": "low|medium|high"
}}

Alerta:
{json.dumps(alert, ensure_ascii=False, indent=2)}

Métricas atuais do Prometheus:
{json.dumps(metrics, ensure_ascii=False, indent=2)}

Logs recentes do Loki:
{json.dumps(logs, ensure_ascii=False, indent=2)}
"""

    response = client.responses.create(
        model="gpt-6-luna",
        input=prompt,
        max_output_tokens=1400,
    )

    raw = response.output_text.strip()

    # Alguns modelos podem envolver o JSON em markdown.
    cleaned = raw

    if cleaned.startswith("```"):
        lines = cleaned.splitlines()

        if lines and lines[0].strip().lower() in ("```json", "```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        cleaned = "\n".join(lines).strip()

    candidates = [cleaned]

    # Tenta também extrair somente o objeto JSON caso exista texto extra.
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")

    if first_brace != -1 and last_brace > first_brace:
        extracted = cleaned[first_brace:last_brace + 1]

        if extracted not in candidates:
            candidates.append(extracted)

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)

            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

    return {
        "summary": raw,
        "probable_cause": "A resposta da IA não veio em JSON válido.",
        "evidence": [],
        "recommended_actions": [],
        "confidence": "low",
    }
