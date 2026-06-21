from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import health, status, balance, trades, logs, diagnostics_router


app = FastAPI(
    title="Purple Trade API",
    description="Backend de gestão do bot de trading",
    version="0.1.0",
    docs_url="/docs",
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Traefik Basic Auth protege o acesso externo
    allow_credentials=True,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(status.router)
app.include_router(balance.router)
app.include_router(trades.router)
app.include_router(logs.router)
app.include_router(diagnostics_router.router)
