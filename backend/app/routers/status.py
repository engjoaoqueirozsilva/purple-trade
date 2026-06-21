from fastapi import APIRouter
from app.services.freqtrade import get_bot_status
 
router = APIRouter(prefix="/status", tags=["status"])
 
 
@router.get("")
async def bot_status():
    return await get_bot_status()