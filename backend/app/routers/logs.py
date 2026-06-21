from fastapi import APIRouter, Query
from app.services.freqtrade import get_logs

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("")
async def logs(limit: int = Query(default=50, ge=1, le=200)):
    return await get_logs(limit=limit)
