"""
SSE endpoint — pushes analysis completion events to the browser.

Flow:
  1. Browser opens GET /stream with credentials (sends access_token cookie).
  2. FastAPI authenticates via cookie, subscribes to Redis channel
     "analysis:done:{user_id}".
  3. When a Celery task finishes it publishes the analysis ID to that channel.
  4. FastAPI forwards the event as  data: <analysis_id>\n\n  to the browser.
  5. Browser EventSource receives it and refreshes the relevant card.

Keep-alive comments (": keepalive") are sent every 20 s so proxies and
load-balancers don't close idle connections.
"""

import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, Cookie, HTTPException, Request, status  # noqa: F401
from fastapi.responses import StreamingResponse

from app.core.database import SessionLocal
from app.core.security import decode_access_token
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(tags=["stream"])

KEEPALIVE_INTERVAL = 20  # seconds


def _authenticate_cookie(access_token: Optional[str]) -> int:
    """Verify the cookie JWT and return user_id. Opens+closes its own DB session."""
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = decode_access_token(access_token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    email: Optional[str] = payload.get("sub")
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return user.id
    finally:
        db.close()  # release connection immediately — not held for SSE lifetime


@router.get("/stream")
async def stream_analysis_updates(
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """
    SSE endpoint. The browser connects once; the server pushes
    'data: <analysis_id>\\n\\n' whenever an analysis for this user completes.
    """
    user_id = _authenticate_cookie(access_token)

    from app.core.config import settings
    redis_url = getattr(settings, "REDIS_URL", None)
    if not redis_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Real-time updates not available (Redis not configured)",
        )

    channel = f"analysis:done:{user_id}"

    async def generate():
        import redis.asyncio as aioredis

        r = aioredis.from_url(redis_url, decode_responses=True)
        pubsub = r.pubsub()
        await pubsub.subscribe(channel)
        logger.info("SSE: user %d subscribed to %s", user_id, channel)

        loop = asyncio.get_running_loop()
        last_ping = loop.time()
        try:
            while True:
                if await request.is_disconnected():
                    break

                msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                now = loop.time()

                if msg and msg["type"] == "message":
                    analysis_id = msg["data"]
                    logger.info("SSE: pushing analysis %s to user %d", analysis_id, user_id)
                    yield f"data: {analysis_id}\n\n"
                elif now - last_ping >= KEEPALIVE_INTERVAL:
                    yield ": keepalive\n\n"
                    last_ping = now

                await asyncio.sleep(0.5)
        finally:
            await pubsub.unsubscribe(channel)
            await r.aclose()
            logger.info("SSE: user %d disconnected from %s", user_id, channel)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # tell nginx not to buffer SSE
        },
    )
