"""
FreqtradeService — integração com a API REST do Freqtrade.
No MVP, retorna dados mockados quando o bot não está disponível.
"""

import httpx
import logging
from datetime import datetime, timedelta
from random import uniform, randint
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

BASE_URL = settings.freqtrade_url
AUTH = (settings.freqtrade_user, settings.freqtrade_password)


# ─────────────────────────────────────────
# Utilitários internos
# ─────────────────────────────────────────

async def _get(path: str) -> dict | None:
    """Faz GET autenticado na API do Freqtrade."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{BASE_URL}/api/v1{path}", auth=AUTH)
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.warning(f"Freqtrade unreachable: {e}")
        return None


def _wrap(data, *, source: str, connected: bool) -> dict:
    """
    Envolve qualquer payload no envelope padrão da API interna:
    {
        "connected": bool,
        "source": "live" | "mock",
        "timestamp": "<ISO 8601 UTC>",
        "data": <payload original>
    }
    Todos os endpoints retornam esse formato — o frontend nunca
    precisa lidar com estruturas diferentes por rota.
    """
    return {
        "connected": connected,
        "source": source,
        "timestamp": datetime.utcnow().isoformat(),
        "data": data,
    }


# ─────────────────────────────────────────
# Status do bot
# ─────────────────────────────────────────

async def get_bot_status() -> dict:
    """
    Verificação composta de saúde do bot.

    Etapas:
      1. /ping          — API está viva?
      2. /show_config   — detecta dry_run e exchange configurada
      3. /balance       — carteira acessível (exchange conectada de fato)?

    Estados possíveis retornados em data.bot_state:
      "offline"           — /ping falhou, bot não responde
      "online_no_exchange"— bot vivo mas sem exchange configurada
      "dry_run"           — bot vivo, exchange presente, paper trading
      "live"              — bot vivo, exchange presente, operando real
    """
    ping = await _get("/ping")
    if not ping:
        payload = {
            "bot_state": "offline",
            "strategy": None,
            "dry_run": None,
            "exchange": None,
            "exchange_connected": False,
            "total_profit_pct": 0,
            "trades_count": 0,
            "win_rate": 0,
            "wins": 0,
            "losses": 0,
        }
        return _wrap(payload, source="mock", connected=False)

    # Bot está vivo — inspeciona configuração e carteira
    config  = await _get("/show_config")
    balance = await _get("/balance")
    stats   = await get_daily_stats()

    # /show_config pode retornar exchange como string ("binance") ou como
    # dict {"name": "binance", ...} dependendo da versão do Freqtrade.
    exchange: str | None = None
    dry_run: bool = True
    strategy: str | None = None

    if config:
        dry_run  = bool(config.get("dry_run", True))
        strategy = config.get("strategy")

        raw_exchange = config.get("exchange")
        if isinstance(raw_exchange, dict):
            exchange = raw_exchange.get("name")
        elif isinstance(raw_exchange, str):
            exchange = raw_exchange

    exchange_connected: bool = balance is not None

    if not exchange:
        bot_state = "online_no_exchange"
    elif dry_run:
        bot_state = "dry_run"
    else:
        bot_state = "live"

    # get_daily_stats retorna envelope — extrai data com fallback seguro
    stats_data = stats.get("data", {}) if isinstance(stats, dict) else {}

    payload = {
        "bot_state": bot_state,
        "strategy": strategy,
        "dry_run": dry_run,
        "exchange": exchange,
        "exchange_connected": exchange_connected,
        "total_profit_pct": stats_data.get("total_profit_pct", 0),
        "trades_count":     stats_data.get("trades_count", 0),
        "win_rate":         stats_data.get("win_rate", 0),
        "wins":             stats_data.get("wins", 0),
        "losses":           stats_data.get("losses", 0),
    }
    return _wrap(payload, source="live", connected=True)


# ─────────────────────────────────────────
# Saldo
# ─────────────────────────────────────────

async def get_balance() -> dict:
    """
    O endpoint real /balance do Freqtrade NÃO retorna free/used na raiz —
    esses valores ficam dentro da lista `currencies`. Formato real:

    {
      "currencies": [
        {"currency": "USDT", "free": 1000.0, "used": 0.0, "balance": 1000.0, ...}
      ],
      "total": 1000.0,
      "stake": "USDT",
      "note": "Simulated balances",   # presente quando dry_run=true
      ...
    }
    """
    data = await _get("/balance")
    if data:
        currencies = data.get("currencies", [])
        payload = {
            "total_usd": data.get("total", 0),
            "free_usd": sum(c.get("free", 0) for c in currencies),
            "used_usd": sum(c.get("used", 0) for c in currencies),
            "currency": data.get("stake", "USDT"),
        }
        return _wrap(payload, source="live", connected=True)

    # Mock realístico para desenvolvimento
    total = round(uniform(9800, 10200), 2)
    payload = {
        "total_usd": total,
        "free_usd": round(total * 0.65, 2),
        "used_usd": round(total * 0.35, 2),
        "currency": "USDT",
    }
    return _wrap(payload, source="mock", connected=False)


# ─────────────────────────────────────────
# Trades
# ─────────────────────────────────────────

def _normalize_trade(trade: dict, *, source: str, connected: bool) -> dict:
    """
    Garante que todo trade — live ou mock — carregue os campos
    source, connected e timestamp, além dos campos originais.
    """
    return {
        **trade,
        "source": source,
        "connected": connected,
        "timestamp": datetime.utcnow().isoformat(),
    }


async def get_trades(limit: int = 20) -> dict:
    """
    Formato real de /trades:
    {"trades": [...], "trades_count": N, "offset": 0, "total_trades": N}

    Uma lista vazia de trades (bot novo, sem operações ainda) é um
    resultado "live" válido — não deve cair no mock.
    """
    data = await _get(f"/trades?limit={limit}")
    if data is not None:
        trades = [
            _normalize_trade(t, source="live", connected=True)
            for t in data.get("trades", [])
        ]
        return _wrap(trades, source="live", connected=True)

    # Mock de trades para demonstração
    pairs = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "ADA/USDT"]
    now = datetime.utcnow()
    mock_trades = []

    for i in range(min(limit, 10)):
        pair = pairs[i % len(pairs)]
        profit_pct = round(uniform(-2.5, 4.0), 2)
        open_rate = round(uniform(100, 60000), 2)
        close_rate = round(open_rate * (1 + profit_pct / 100), 2)
        amount = round(uniform(0.001, 0.05), 6)

        raw = {
            "trade_id": i + 1,
            "pair": pair,
            "open_date": (now - timedelta(hours=randint(1, 72))).isoformat(),
            "close_date": (now - timedelta(minutes=randint(10, 120))).isoformat(),
            "open_rate": open_rate,
            "close_rate": close_rate,
            "amount": amount,
            "profit_pct": profit_pct,
            "profit_abs": round(amount * close_rate * profit_pct / 100, 4),
            "is_open": i < 2,
            "strategy": "PurpleRSIEMA",
        }
        mock_trades.append(_normalize_trade(raw, source="mock", connected=False))

    return _wrap(mock_trades, source="mock", connected=False)


# ─────────────────────────────────────────
# Logs
# ─────────────────────────────────────────

async def get_logs(limit: int = 50) -> dict:
    """
    O endpoint real /logs retorna cada entrada como uma LISTA posicional:
    [timestamp_str, timestamp_formatted, logger_name, level, message]

    Convertendo para o formato {timestamp, level, message} que o
    frontend (LogTerminal) espera.
    """
    data = await _get(f"/logs?limit={limit}")
    if data:
        raw_logs = data.get("logs", [])
        parsed_logs = []
        for entry in raw_logs:
            try:
                parsed_logs.append({
                    "timestamp": entry[0],
                    "level": entry[3],
                    "message": entry[4],
                })
            except (IndexError, TypeError):
                logger.warning(f"Unexpected log entry format: {entry}")
                continue
        return _wrap(parsed_logs, source="live", connected=True)

    # Mock de logs
    now = datetime.utcnow()
    mock_entries = [
        ("INFO",    "Bot started — PurpleRSIEMA strategy loaded"),
        ("INFO",    "BTC/USDT — RSI(14) = 32.4, signal: BUY"),
        ("INFO",    "Opening trade: BTC/USDT @ 67,234.50"),
        ("INFO",    "ETH/USDT — RSI(14) = 71.2, signal: SELL"),
        ("INFO",    "Closing trade: ETH/USDT @ 3,521.80, profit: +1.23%"),
        ("WARNING", "SOL/USDT — Insufficient volume, skipping"),
        ("INFO",    "BNB/USDT — EMA(9) crossed EMA(21), signal: BUY"),
        ("INFO",    "Heartbeat — 3 open trades, balance: 10,142 USDT"),
        ("INFO",    "ADA/USDT — RSI(14) = 28.1, signal: BUY"),
        ("DEBUG",   "Fetching candles: BTC/USDT 5m"),
    ]

    logs = [
        {
            "timestamp": (now - timedelta(minutes=i * 3)).isoformat(),
            "level": level,
            "message": msg,
        }
        for i, (level, msg) in enumerate(mock_entries[:limit])
    ]
    return _wrap(logs, source="mock", connected=False)


# ─────────────────────────────────────────
# Métricas diárias (calculadas dos trades)
# ─────────────────────────────────────────

async def get_daily_stats() -> dict:
    """
    Calcula métricas do dia a partir dos trades fechados hoje.
    Retorna sempre no envelope padrão — source herdado dos trades.
    """
    trades_envelope = await get_trades(limit=100)
    trades = trades_envelope["data"]
    source = trades_envelope["source"]
    connected = trades_envelope["connected"]

    today = datetime.utcnow().date()
    today_trades = [
        t for t in trades
        if t.get("close_date") and
        datetime.fromisoformat(t["close_date"]).date() == today
    ]

    total_profit_pct = sum(t.get("profit_pct", 0) for t in today_trades)
    wins = sum(1 for t in today_trades if t.get("profit_pct", 0) > 0)
    losses = len(today_trades) - wins

    payload = {
        "date": today.isoformat(),
        "trades_count": len(today_trades),
        "total_profit_pct": round(total_profit_pct, 2),
        "wins": wins,
        "losses": losses,
        "win_rate": round(wins / len(today_trades) * 100, 1) if today_trades else 0,
    }
    return _wrap(payload, source=source, connected=connected)