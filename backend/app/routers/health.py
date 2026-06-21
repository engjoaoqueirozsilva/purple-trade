from fastapi import APIRouter
from datetime import datetime

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "purple-trade-api",
        "timestamp": datetime.utcnow().isoformat(),
    }
