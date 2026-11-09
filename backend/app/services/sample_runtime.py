import asyncio
import time
from dataclasses import dataclass, field
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse


@dataclass
class SampleRuntimeState:
    version: str
    failure_mode: str | None = None
    request_count: int = 0
    error_count: int = 0
    total_latency_ms: float = 0.0
    started_at: float = field(default_factory=time.perf_counter)


def create_sample_app(version: str, failure_mode: str | None = None) -> FastAPI:
    """Create one disposable version of the real sample workload.

    The local gateway calls this app through httpx ASGI transport. The request still
    traverses FastAPI routing, middleware, readiness, and metrics handlers, while
    keeping the basic demo independent from Docker or a cluster.
    """

    state = SampleRuntimeState(version=version, failure_mode=failure_mode)
    app = FastAPI(title=f"Rook sample workload {version}", docs_url=None, redoc_url=None)
    app.state.runtime = state

    @app.middleware("http")
    async def request_metrics(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        if request.url.path in {"/", "/workload"}:
            state.request_count += 1
            state.total_latency_ms += elapsed_ms
            if response.status_code >= 500:
                state.error_count += 1
        response.headers["X-Rook-Version"] = version
        response.headers["X-Rook-Latency-Ms"] = f"{elapsed_ms:.3f}"
        return response

    @app.get("/health")
    async def health() -> dict[str, Any]:
        if failure_mode == "slow_start":
            await asyncio.sleep(0.15)
        return {
            "status": "ok",
            "version": version,
            "failure_mode": failure_mode or "normal",
        }

    @app.get("/ready")
    async def ready() -> Response:
        if failure_mode in {"readiness_failure", "crash_loop"}:
            return JSONResponse(
                status_code=503,
                content={"status": "not_ready", "version": version, "reason": failure_mode},
            )
        return JSONResponse(status_code=200, content={"status": "ready", "version": version})

    @app.get("/version")
    async def version_route() -> dict[str, str]:
        return {"version": version}

    @app.get("/metrics")
    async def metrics() -> Response:
        if failure_mode == "telemetry_unavailable":
            return PlainTextResponse("telemetry unavailable", status_code=503)
        average = state.total_latency_ms / state.request_count if state.request_count else 0.0
        body = "\n".join(
            [
                "# HELP rook_requests_total Total workload requests.",
                "# TYPE rook_requests_total counter",
                f'rook_requests_total{{version="{version}"}} {state.request_count}',
                "# HELP rook_errors_total Total workload errors.",
                "# TYPE rook_errors_total counter",
                f'rook_errors_total{{version="{version}"}} {state.error_count}',
                "# HELP rook_request_latency_average_ms Average request latency.",
                "# TYPE rook_request_latency_average_ms gauge",
                f'rook_request_latency_average_ms{{version="{version}"}} {average:.3f}',
            ]
        )
        return PlainTextResponse(body + "\n", media_type="text/plain")

    @app.get("/")
    @app.get("/workload")
    async def workload(request: Request) -> Response:
        if failure_mode == "delayed_responses":
            await asyncio.sleep(0.42)
        elif failure_mode == "resource_pressure":
            await asyncio.sleep(0.03)
        elif failure_mode == "slow_start":
            await asyncio.sleep(0.08)

        request_number = state.request_count + 1
        if failure_mode == "crash_loop":
            return JSONResponse(
                status_code=503, content={"error": "container restarting", "version": version}
            )
        if failure_mode == "elevated_errors" and request_number % 4 != 0:
            return JSONResponse(
                status_code=500, content={"error": "controlled canary fault", "version": version}
            )
        return JSONResponse(
            status_code=200,
            content={
                "message": "rook sample response",
                "version": version,
                "request_id": request.headers.get("X-Request-ID", "local-request"),
            },
        )

    return app
