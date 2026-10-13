import os
import httpx

PROMETHEUS_URL = os.getenv(
    "PROMETHEUS_URL",
    "http://127.0.0.1:9090"
)


async def query_prometheus(query: str):
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={"query": query},
        )
        response.raise_for_status()

        payload = response.json()

        if payload.get("status") != "success":
            raise RuntimeError("Prometheus query failed")

        return payload.get("data", {}).get("result", [])


async def collect_incident_context():
    queries = {
        "cpu_usage_percent": (
            '100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)'
        ),
        "memory_usage_percent": (
            '100 * (1 - '
            '(node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes))'
        ),
        "disk_usage_percent": (
            '100 * (1 - '
            'node_filesystem_avail_bytes{mountpoint="/",fstype!="rootfs"} '
            '/ node_filesystem_size_bytes{mountpoint="/",fstype!="rootfs"})'
        ),
        "load_1m": "node_load1",
        "portfolio_latency_ms": (
            'probe_duration_seconds{job="portfolio"} * 1000'
        ),
        "portfolio_up": 'probe_success{job="portfolio"}',
        "nginx_up": 'up{job="nginx"}',
        "loki_up": 'up{job="loki"}',
        "alloy_up": 'up{job="alloy"}',
        "node_exporter_up": 'up{job="node_exporter"}',
    }

    context = {}

    for name, query in queries.items():
        try:
            result = await query_prometheus(query)

            if not result:
                context[name] = None
                continue

            values = []

            for item in result:
                value = item.get("value", [None, None])[1]

                try:
                    values.append(float(value))
                except (TypeError, ValueError):
                    pass

            if not values:
                context[name] = None
            elif len(values) == 1:
                context[name] = round(values[0], 2)
            else:
                context[name] = [round(value, 2) for value in values]

        except Exception as exc:
            context[name] = {
                "error": str(exc)
            }

    return context
