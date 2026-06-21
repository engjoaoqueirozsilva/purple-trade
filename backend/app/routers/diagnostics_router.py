"""
Rota de diagnóstico — plugar no FastAPI principal.

No arquivo onde você registra os routers (ex.: app/main.py ou app/api/router.py):

    from app.api.diagnostics_router import router as diagnostics_router
    app.include_router(diagnostics_router)

Endpoint disponível:  GET /api/diagnostics
"""

from fastapi import APIRouter
from app.services.diagnostics import run_diagnostics

router = APIRouter(tags=["diagnostics"])


@router.get("/diagnostics")
async def diagnostics():
    """
    Testa cada etapa da conexão com o Freqtrade e retorna um relatório
    detalhado com status, latência e diagnóstico em linguagem natural.
    """
    return await run_diagnostics()