from fastapi import APIRouter
from app.services.freqtrade import get_balance

router = APIRouter(prefix="/balance", tags=["balance"])


@router.get("")
async def balance():
    return await get_balance()
