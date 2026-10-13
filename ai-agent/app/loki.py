import os
import time
import httpx

LOKI_URL = os.getenv(
    "LOKI_URL",
    "http://127.0.0.1:3100"
)

async def query_loki_range(query: str, minutes: int = 5, limit: int = 20):
    end_ns = int(time.time() * 1_000_000_000)
    start_ns = end_ns - (minutes * 60 * 1_000_000_000)

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{LOKI_URL}/loki/api/v1/query_range",
            params={
                "query": query,
                "start": start_ns,
                "end": end_ns,
                "limit": limit,
                "direction": "backward",
            },
        )

        response.raise_for_status()
        payload = response.json()

        if payload.get("status") != "success":
            raise RuntimeError("Loki query failed")

        return payload.get("data", {}).get("result", [])


async def collect_log_context():
    queries = {
        "http_5xx": (
            '{job="nginx",service="portfolio",log_type="access"} '
            '| pattern `<client_ip> - <user> [<_>] "<http_method> <request_uri> <protocol>" '
            '<http_status> <bytes> "<referer>" "<agent>"` '
            '| http_status=~"5.."'
        ),
        "nginx_errors": (
            '{job="nginx",service="portfolio",log_type="error"}'
        ),
    }

    context = {}

    for name, query in queries.items():
        try:
            result = await query_loki_range(query)

            lines = []

            for stream in result:
                labels = stream.get("stream", {})

                for ts, line in stream.get("values", []):
                    lines.append({
                        "timestamp": ts,
                        "labels": labels,
                        "line": line,
                    })

            context[name] = lines[:20]

        except Exception as exc:
            context[name] = {
                "error": str(exc)
            }

    return context
