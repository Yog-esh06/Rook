import asyncio
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

import httpx

from app.services.sample_runtime import create_sample_app


@dataclass(frozen=True)
class TrafficObservation:
    candidate_version: str
    target_traffic_percentage: int
    request_sample_count: int
    error_rate: float | None
    latency_samples_ms: list[float]
    readiness: bool | None
    restart_count: int
    resource_pressure: float | None
    telemetry_available: bool
    observed_at: datetime
    stable_requests: int
    candidate_requests: int


class LocalTrafficGateway:
    """Deterministic request router for the no-cluster demonstration mode."""

    async def _request(
        self, client: httpx.AsyncClient, path: str, request_id: str
    ) -> tuple[int, float]:
        started = time.perf_counter()
        response = await client.get(path, headers={"X-Request-ID": request_id})
        elapsed_ms = (time.perf_counter() - started) * 1000
        return response.status_code, elapsed_ms

    async def observe(
        self,
        *,
        stable_version: str,
        candidate_version: str,
        failure_mode: str | None,
        target_traffic_percentage: int,
        sample_count: int,
    ) -> TrafficObservation:
        stable_app = create_sample_app(stable_version)
        candidate_app = create_sample_app(candidate_version, failure_mode)
        stable_count = sample_count - round(sample_count * target_traffic_percentage / 100)
        candidate_count = sample_count - stable_count
        stable_transport = httpx.ASGITransport(app=stable_app)
        candidate_transport = httpx.ASGITransport(app=candidate_app)

        async with (
            httpx.AsyncClient(
                transport=stable_transport, base_url="http://stable.local"
            ) as stable_client,
            httpx.AsyncClient(
                transport=candidate_transport, base_url="http://canary.local"
            ) as candidate_client,
        ):
            semaphore = asyncio.Semaphore(32)

            async def limited_request(
                client: httpx.AsyncClient, request_id: str
            ) -> tuple[int, float]:
                async with semaphore:
                    return await self._request(client, "/workload", request_id)

            requests = [
                limited_request(stable_client, f"stable-{uuid4()}-{index}")
                for index in range(stable_count)
            ]
            requests.extend(
                limited_request(candidate_client, f"canary-{uuid4()}-{index}")
                for index in range(candidate_count)
            )
            results = await asyncio.gather(*requests)
            readiness_response = await candidate_client.get("/ready")
            telemetry_response = await candidate_client.get("/metrics")

        candidate_results = results[stable_count:]
        latencies = [latency for _, latency in candidate_results]
        errors = sum(1 for status, _ in candidate_results if status >= 500)
        return TrafficObservation(
            candidate_version=candidate_version,
            target_traffic_percentage=target_traffic_percentage,
            request_sample_count=candidate_count,
            error_rate=(errors / candidate_count if candidate_count else None),
            latency_samples_ms=latencies,
            readiness=readiness_response.status_code == 200,
            restart_count=3 if failure_mode == "crash_loop" else 0,
            resource_pressure=0.93 if failure_mode == "resource_pressure" else 0.18,
            telemetry_available=telemetry_response.status_code == 200,
            observed_at=datetime.now(UTC),
            stable_requests=stable_count,
            candidate_requests=candidate_count,
        )
