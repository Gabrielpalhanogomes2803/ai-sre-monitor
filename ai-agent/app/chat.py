import json

from openai import OpenAI

from app.storage import get_recent_incidents

client = OpenAI()


def _parse_response(raw: str, incidents_used: int) -> dict:
    cleaned = raw.strip()

    # Remove bloco markdown ```json ... ```
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()

        if lines and lines[0].strip().lower() in ("```json", "```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        cleaned = "\n".join(lines).strip()

    candidates = [cleaned]

    # Tenta extrair apenas o objeto JSON caso venha texto antes/depois.
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
                answer = parsed.get("answer")

                if isinstance(answer, str) and answer.strip():
                    return {
                        "answer": answer.strip(),
                        "incidents_used": parsed.get(
                            "incidents_used",
                            incidents_used,
                        ),
                    }
        except json.JSONDecodeError:
            pass

    # Fallback limpo: nunca mostra um JSON quebrado como resposta.
    return {
        "answer": cleaned,
        "incidents_used": incidents_used,
    }


def answer_incident_question(question: str) -> dict:
    incidents = get_recent_incidents(limit=10)

    if not incidents:
        return {
            "answer": "Ainda não existem incidentes registrados no histórico.",
            "incidents_used": 0,
        }

    prompt = f"""
Você é o AI SRE Assistant, um copiloto de operações e investigação de incidentes.

Seu trabalho é conversar com o operador como um engenheiro SRE experiente:
explicar rapidamente o que aconteceu, separar causa de consequência e indicar
onde começar a investigação.

Responda sempre em português do Brasil.

REGRAS DE COMUNICAÇÃO:
- Fale como um assistente, não como um relatório automático.
- Comece pelo que aconteceu em linguagem simples.
- Explique o impacto antes de entrar em métricas.
- Seja curto por padrão.
- Use parágrafos curtos e linguagem natural.
- Evite jargão quando ele não for necessário.
- Traduza "firing" como "ativo" e "resolved" como "resolvido".
- Não mencione detalhes internos como B=1, C=0, ref_id, datasource_uid ou fingerprints.
- Evite escrever métricas como "loki_up=0" se puder dizer "o Loki estava indisponível".
- Só cite valores técnicos quando eles realmente ajudarem a investigação.
- Se vários alertas forem consequência do mesmo problema, agrupe-os em um único incidente.
- Diferencie o problema principal dos efeitos colaterais.
- Diferencie claramente o incidente histórico do estado atual.
- Não invente causa.
- Quando a causa não estiver confirmada, use linguagem como:
  "A hipótese mais provável é..." ou "O histórico sugere..."
- Se o usuário perguntar "o que faço agora", priorize passos de investigação.
- Se pedir detalhes técnicos, aí sim aprofunde métricas e logs.
- Nunca recomende ações destrutivas.
- Não repita o conteúdo bruto dos alertas.

FORMATO DA RESPOSTA:
Para perguntas gerais sobre um incidente, prefira:

"O que aconteceu:"
explicação curta em linguagem humana.

"Impacto:"
o que realmente foi afetado.

"Investigar primeiro:"
até 3 passos objetivos.

Não force esse formato se a pergunta pedir outra coisa.
Por exemplo:
- "Qual foi a causa?" -> responda causa + evidências.
- "O que faço agora?" -> responda passos.
- "Está resolvido?" -> responda estado atual.
- "Me explica tecnicamente" -> aprofunde.

IMPORTANTE:
- Responda somente com base no histórico fornecido.
- Se não houver evidência suficiente, diga isso claramente.
- Diferencie testes controlados de incidentes reais.
- Alertas relacionados devem ser explicados juntos quando fizer sentido.

Retorne SOMENTE JSON válido neste formato:
{{
  "answer": "resposta natural para o operador",
  "incidents_used": number
}}

Pergunta do operador:
{question}

Histórico recente:
{json.dumps(incidents, ensure_ascii=False, indent=2)}
"""

    response = client.responses.create(
        model="gpt-6-luna",
        input=prompt,
        max_output_tokens=1000,
    )

    raw = response.output_text.strip()

    return _parse_response(raw, len(incidents))
