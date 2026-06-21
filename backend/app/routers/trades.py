from fastapi import APIRouter, Query
from app.services.freqtrade import get_trades

router = APIRouter(prefix="/trades", tags=["trades"])


@router.get("")
async def trades(limit: int = Query(default=20, ge=1, le=100)):
    return await get_trades(limit=limit)
