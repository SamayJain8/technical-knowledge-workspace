"""Bound request bodies and response wait without releasing active work."""

import asyncio
import json
import logging
from time import perf_counter
from uuid import uuid4

from fastapi import HTTPException, Request
from starlette.concurrency import run_in_threadpool
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)
MAX_BODY_BYTES = 8192
REQUEST_SECONDS = 20
API_PATHS = {"/api/v1/search", "/api/v1/answer"}


class RequestLimits:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        started = perf_counter()
        request_id = uuid4().hex
        scope.setdefault("state", {}).update(request_id=request_id, deadline=started + REQUEST_SECONDS)
        path = scope["path"]
        label = path if path in API_PATHS | {"/", "/health/live", "/health/ready"} else "other"

        async def traced_send(message):
            if message["type"] == "http.response.start":
                message["headers"] = [*message["headers"], (b"x-request-id", request_id.encode("ascii"))]
                logger.info(json.dumps({"event": "request", "request_id": request_id,
                                        "route": label, "status": message["status"],
                                        "latency_ms": round((perf_counter() - started) * 1000, 2)}))
            await send(message)

        if (scope["method"] == "POST" and path in API_PATHS) or (
            scope["method"] == "PATCH" and path.startswith("/api/v1/documents/")
        ):
            body = bytearray()
            try:
                async with asyncio.timeout(REQUEST_SECONDS):
                    while True:
                        message = await receive()
                        if message["type"] == "http.disconnect":
                            return
                        chunk = message.get("body", b"")
                        if len(body) + len(chunk) > MAX_BODY_BYTES:
                            await JSONResponse({"detail": "Request body too large"}, 413)(scope, receive, traced_send)
                            return
                        body.extend(chunk)
                        if not message.get("more_body"):
                            break
            except TimeoutError:
                await JSONResponse({"detail": "Request deadline exceeded"}, 504)(scope, receive, traced_send)
                return
            original_receive = receive

            async def replay():
                nonlocal body
                if body is None:
                    return await original_receive()
                data = bytes(body)
                body = None
                return {"type": "http.request", "body": data, "more_body": False}

            receive = replay
        await self.app(scope, receive, traced_send)


async def within_deadline(request: Request, work, *args):
    remaining = request.state.deadline - perf_counter()
    if remaining <= 0:
        raise HTTPException(504, "Request deadline exceeded")
    try:
        return await asyncio.wait_for(run_in_threadpool(work, *args), remaining)
    except TimeoutError:
        raise HTTPException(504, "Request deadline exceeded") from None
