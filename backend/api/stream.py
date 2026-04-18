from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from backend.events_bus import bus

router = APIRouter(prefix="/api", tags=["stream"])


@router.get("/stream")
async def stream():
    async def gen():
        async for msg in bus.subscribe():
            yield {"data": msg}
    return EventSourceResponse(gen())
