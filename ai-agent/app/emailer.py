import os
import smtplib
from email.message import EmailMessage

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.environ["SMTP_USER"]
SMTP_PASSWORD = os.environ["SMTP_PASSWORD"]
SMTP_TO = os.getenv("SMTP_TO", SMTP_USER)


def send_incident_email(alert: dict, analysis: dict):
    msg = EmailMessage()

    alert_name = (
        alert.get("commonLabels", {}).get("alertname")
        or alert.get("alert")
        or "Incidente SRE"
    )

    status = (
        alert.get("status")
        or alert.get("state")
        or "unknown"
    ).lower()

    actions = analysis.get("recommended_actions", [])
    next_action = actions[0] if actions else "Verificar o serviço e os logs recentes."

    if status == "firing":
        subject = f"🔥 [AI SRE] {alert_name}"
        status_label = "ATIVO"
    else:
        subject = f"✅ [AI SRE] {alert_name}"
        status_label = "RESOLVIDO"

    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = SMTP_TO

    body = f"""AI SRE — {alert_name}

Status: {status_label}

Situação:
{analysis.get("summary", "Sem resumo disponível.")}

Provável causa:
{analysis.get("probable_cause", "Não determinada.")}

Investigar primeiro:
{next_action}
"""

    msg.set_content(body)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
