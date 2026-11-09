import asyncio
import os
import time
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse

VERSION = os.getenv("APP_VERSION", "v1")
FAILURE_MODE = os.getenv("FAILURE_MODE") or None
state = {"requests": 0, "errors": 0, "latency_ms": 0.0}
app = FastAPI(title=f"Rook sample workload {VERSION}", docs_url=None, redoc_url=None)


@app.middleware("http")
async def metrics(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    if request.url.path in {"/", "/workload"}:
        state["requests"] += 1
        state["latency_ms"] += elapsed_ms
        if response.status_code >= 500:
            state["errors"] += 1
    response.headers["X-Rook-Version"] = VERSION
    response.headers["X-Rook-Latency-Ms"] = f"{elapsed_ms:.3f}"
    return response


@app.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "ok", "version": VERSION, "failure_mode": FAILURE_MODE or "normal"}


@app.get("/ready")
async def ready() -> Response:
    if FAILURE_MODE in {"readiness_failure", "crash_loop"}:
        return JSONResponse(status_code=503, content={"status": "not_ready", "version": VERSION})
    return JSONResponse(status_code=200, content={"status": "ready", "version": VERSION})


@app.get("/version")
async def version() -> dict[str, str]:
    return {"version": VERSION}


@app.get("/metrics")
async def prometheus_metrics() -> Response:
    if FAILURE_MODE == "telemetry_unavailable":
        return PlainTextResponse("telemetry unavailable", status_code=503)
    average = state["latency_ms"] / state["requests"] if state["requests"] else 0.0
    return PlainTextResponse(
        "\n".join(
            [
                "# TYPE rook_requests_total counter",
                f'rook_requests_total{{version="{VERSION}"}} {state["requests"]}',
                "# TYPE rook_errors_total counter",
                f'rook_errors_total{{version="{VERSION}"}} {state["errors"]}',
                "# TYPE rook_request_latency_average_ms gauge",
                f'rook_request_latency_average_ms{{version="{VERSION}"}} {average:.3f}',
            ]
        )
        + "\n",
        media_type="text/plain",
    )


@app.get("/")
@app.get("/workload")
async def workload(request: Request) -> Response:
    if FAILURE_MODE == "delayed_responses":
        await asyncio.sleep(0.42)
    elif FAILURE_MODE == "resource_pressure":
        await asyncio.sleep(0.03)
    request_number = state["requests"] + 1
    if FAILURE_MODE == "crash_loop":
        return JSONResponse(
            status_code=503,
            content={"error": "container restarting", "version": VERSION},
        )
    if FAILURE_MODE == "elevated_errors" and request_number % 4 != 0:
        return JSONResponse(
            status_code=500,
            content={"error": "controlled canary fault", "version": VERSION},
        )
    return JSONResponse(
        {"message": "rook sample response", "version": VERSION, "request_id": request.headers.get("X-Request-ID")}
    )
