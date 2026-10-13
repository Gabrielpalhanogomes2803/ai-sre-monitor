# AI SRE Monitor

> From detection to the first actionable diagnosis.

AI SRE Monitor is an observability and incident-triage project designed to reduce the time between detecting a problem and understanding where to start investigating.

The platform combines **Prometheus, Grafana, Loki, Alloy, Docker and a Python/FastAPI AI agent** to correlate alerts, metrics and logs before generating an operational diagnosis.

## Architecture

```text
Infrastructure / Application
          |
          v
 Prometheus + Loki
          |
          v
    Grafana Alerting
          |
     +----+----+
     |         |
     v         v
Operational   AI SRE Agent
  E-mail          |
                  +-- Prometheus
                  +-- Loki
                  +-- LLM analysis
                  +-- SQLite history
                         |
                         v
                  AI SRE Assistant
```

## Main Stack

- Prometheus
- Grafana
- Grafana Loki
- Grafana Alloy
- Node Exporter
- Nginx Prometheus Exporter
- Blackbox Exporter
- Python
- FastAPI
- Docker Compose
- SQLite
- Nginx
- Cloudflare
- Tailscale

## What the AI Agent Does

When Grafana detects an incident, the AI SRE Agent receives the alert and collects additional context from Prometheus and Loki.

Instead of only returning that an alert fired, the agent tries to answer:

- What happened?
- Is the problem still happening?
- What was the impact?
- What evidence supports the diagnosis?
- Where should the operator investigate first?

Prometheus and Loki remain the technical sources of truth. The AI layer is used to interpret evidence and assist incident triage.

## Incident Flow

```text
Alert
  |
  v
Grafana
  |
  v
Webhook
  |
  v
AI SRE Agent
  |
  +-- Metrics
  +-- Logs
  |
  v
Context Analysis
  |
  v
Probable Cause
  |
  v
Investigation Steps
```

## AI SRE Assistant

The project also includes an operational assistant capable of analyzing stored incident history.

Example question:

```text
Explain the latest incidents as if I were taking over the on-call shift.
```

The assistant summarizes related incidents, separates historical conditions from the current state and provides concise investigation steps.

## Monitoring

The environment monitors:

- Portfolio availability
- CPU usage
- Memory usage
- Disk usage
- HTTP 5xx errors
- Application latency
- TLS certificate expiration
- Loki availability
- Alloy availability
- Node Exporter availability
- Nginx Exporter availability

## Controlled Incident Tests

The architecture was validated using controlled failure scenarios.

### HTTP 5xx

A temporary endpoint returned HTTP 500 responses to validate the complete observability flow:

```text
Nginx -> Alloy -> Loki -> Grafana -> AI SRE Agent
```

The test endpoint was removed after validation.

### Loki Outage

Loki was temporarily stopped to validate detection of an observability-layer failure.

The environment detected the outage and the agent differentiated the Loki failure from the state of the monitored application.

### Nginx Exporter Outage

The Nginx Exporter was stopped while the website remained available.

This validated the distinction between an application outage and a telemetry/monitoring outage.

## Security

The project follows a least-exposure approach:

- administrative services bound to localhost;
- private administrative access;
- secrets stored in environment variables;
- `.env` excluded from Git;
- incident database excluded from Git;
- backups excluded from Git;
- no automatic remediation;
- human-in-the-loop for operational decisions.

Sensitive credentials are **not stored in this repository**.

## Human in the Loop

The AI agent provides diagnostic guidance but does not restart services, change firewall rules or perform destructive actions automatically.

Its purpose is to assist the operator, not replace operational decision-making.

## Alerting as Code

Grafana resources are provisioned declaratively, including alert rules, notification policies, dashboards and datasources.

## Project Structure

```text
ai-sre-monitor/
|-- ai-agent/
|-- alloy/
|-- blackbox/
|-- docs/
|   `-- screenshots/
|-- grafana/
|-- loki/
|-- prometheus/
|-- .env.example
|-- .gitignor
|-- docker-compose.yml
`-- README.md
```

## Running the Project

```bash
git clone <repository-url>
cd ai-sre-monitor
cp .env.example .env
cp grafana/provisioning/alerting/contact-points.example.yml grafana/provisioning/alerting/contact-points.yml
docker compose up -d --build
b```

## Screenshots

Screenshots of the NOC dashboards and AI SRE Assistant should be stored in:

<img width="1672" height="941" alt="Imagem do ChatGPT 13 de out  de 2026, 17_29_19-3" src="https://github.com/user-attachments/assets/fe51ab72-2ddd-41ad-bd4c-8c9b2ca78112" />

<img width="1672" height="941" alt="Imagem do ChatGPT 13 de out  de 2026, 17_29_16-2" src="https://github.com/user-attachments/assets/a3ec23e0-b782-4ec9-aa80-7aaa0a6c98c2" />

<img width="1672" height="941" alt="Imagem do ChatGPT 13 de out  de 2026, 17_29_14-1" src="https://github.com/user-attachments/assets/848ab61b-cf9f-4e4e-b222-1ea9cccab49d" />


## Future Improvements

- automated tests;
- incident correlation;
- datasource failure classification;
- AI agent observability;
- runbooks;
- ticketing integrations;
- Docker image version pinning;
- development and production environment separation.

## Project Goal

The goal is not to build an autonomous SRE.

The goal is to reduce the path between:

> **Something is wrong.**

and:

> **I know where to start investigating.**

## Author

**Gabriel Gomes**

Infrastructure | Cloud | DevOps | SRE | Observability

Portfolio: https://gabrielgomes.cloud
