"""
DiagnosticsService — testa cada etapa da conexão com o Freqtrade
e retorna um relatório detalhado de O QUE está falhando e POR QUÊ.

Rota sugerida:  GET /api/diagnostics
Uso:            apenas em desenvolvimento / debug pessoal
"""

import httpx
import logging
import time
import traceback
from datetime import datetime
from app.config import get_settings

logger = logging.getLogger(__name__)

# Carregado sob demanda em run_diagnostics() para que um .env incompleto
# não quebre o import do módulo inteiro — o erro aparece no JSON, não como 500.
def _load_settings():
    try:
        s = get_settings()
        return s.freqtrade_url, (s.freqtrade_user, s.freqtrade_password), None
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"[diagnostics] Falha ao carregar settings:\n{tb}")
        return None, (None, None), str(e)


# ─────────────────────────────────────────
# Probe individual
# ─────────────────────────────────────────

async def _probe(client: httpx.AsyncClient, path: str, base_url: str, auth: tuple) -> dict:
    """
    Testa um endpoint específico e retorna um dict com:
      ok          — True se respondeu 2xx
      status_code — código HTTP (ou None se nem chegou)
      latency_ms  — tempo de resposta em ms
      error       — mensagem de erro (ou None se ok)
      body        — primeiros 300 chars do body (ou None se erro)
    """
    url = f"{base_url}/api/v1{path}"
    start = time.monotonic()
    try:
        resp = await client.get(url, auth=auth)
        latency = round((time.monotonic() - start) * 1000, 1)
        body = resp.text[:300] if resp.text else None
        return {
            "ok": resp.is_success,
            "status_code": resp.status_code,
            "latency_ms": latency,
            "error": None if resp.is_success else f"HTTP {resp.status_code} {resp.reason_phrase}",
            "body": body,
        }
    except httpx.ConnectError as e:
        latency = round((time.monotonic() - start) * 1000, 1)
        return {
            "ok": False,
            "status_code": None,
            "latency_ms": latency,
            "error": f"ConnectError — host inacessível ou porta fechada: {e}",
            "body": None,
        }
    except httpx.TimeoutException as e:
        latency = round((time.monotonic() - start) * 1000, 1)
        return {
            "ok": False,
            "status_code": None,
            "latency_ms": latency,
            "error": f"Timeout após {latency}ms — bot pode estar sobrecarregado ou travado: {e}",
            "body": None,
        }
    except Exception as e:
        latency = round((time.monotonic() - start) * 1000, 1)
        return {
            "ok": False,
            "status_code": None,
            "latency_ms": latency,
            "error": f"{type(e).__name__}: {e}",
            "body": None,
        }


# ─────────────────────────────────────────
# Diagnóstico completo
# ─────────────────────────────────────────

async def run_diagnostics() -> dict:
    """
    Executa uma bateria de probes em sequência e retorna um relatório
    com diagnóstico de cada etapa.

    Estrutura de retorno:
    {
        "timestamp": "...",
        "target_url": "http://...",
        "auth_user": "...",          # só o username, nunca a senha
        "overall": "ok" | "partial" | "failed" | "config_error",
        "steps": {
            "ping":        { ok, status_code, latency_ms, error, body },
            "auth":        { ok, status_code, latency_ms, error, body },
            "config":      { ok, status_code, latency_ms, error, body },
            "balance":     { ok, status_code, latency_ms, error, body },
            "trades":      { ok, status_code, latency_ms, error, body },
        },
        "diagnosis": [str, ...]      # lista de conclusões em linguagem natural
    }
    """
    base_url, auth, settings_error = _load_settings()

    # Se as settings falharam, retorna um diagnóstico específico sem tentar HTTP
    if settings_error or not base_url:
        return {
            "timestamp":  datetime.utcnow().isoformat(),
            "target_url": base_url or "indefinido",
            "auth_user":  auth[0] or "indefinido",
            "overall":    "config_error",
            "passed":     "0/5",
            "steps":      {},
            "diagnosis":  [
                f"❌ CONFIGURAÇÃO — falha ao carregar settings: {settings_error}",
                "Verifique se as variáveis FREQTRADE_URL, FREQTRADE_USER e "
                "FREQTRADE_PASSWORD existem no .env e no modelo Pydantic de Settings.",
            ],
        }

    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            steps = {
                "ping":    await _probe(client, "/ping",              base_url, auth),
                "auth":    await _probe(client, "/status",            base_url, auth),
                "config":  await _probe(client, "/show_config",       base_url, auth),
                "balance": await _probe(client, "/balance",           base_url, auth),
                "trades":  await _probe(client, "/trades?limit=1",    base_url, auth),
            }
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"[diagnostics] Erro inesperado durante probes:\n{tb}")
        return {
            "timestamp":  datetime.utcnow().isoformat(),
            "target_url": base_url,
            "auth_user":  auth[0],
            "overall":    "failed",
            "passed":     "0/5",
            "steps":      {},
            "diagnosis":  [f"❌ Erro interno durante diagnóstico: {type(e).__name__}: {e}"],
        }

    diagnosis = _diagnose(steps, base_url, auth)
    passed  = sum(1 for s in steps.values() if s["ok"])
    total   = len(steps)
    overall = "ok" if passed == total else ("partial" if passed > 0 else "failed")

    return {
        "timestamp":  datetime.utcnow().isoformat(),
        "target_url": base_url,
        "auth_user":  auth[0],
        "overall":    overall,
        "passed":     f"{passed}/{total}",
        "steps":      steps,
        "diagnosis":  diagnosis,
    }


def _diagnose(steps: dict, base_url: str, auth: tuple) -> list[str]:
    """
    Interpreta os resultados dos probes e gera mensagens acionáveis
    em linguagem natural — o que falhou e o que fazer.
    """
    msgs = []
    ping     = steps["ping"]
    auth_step = steps["auth"]
    config   = steps["config"]
    balance  = steps["balance"]
    trades   = steps["trades"]

    # ── 1. Ping ──────────────────────────────────────────────────
    if not ping["ok"]:
        if ping["status_code"] is None:
            msgs.append(
                f"❌ PING falhou sem resposta HTTP ({ping['error']}). "
                f"Verifique: (a) o Freqtrade está rodando? "
                f"(b) a URL '{base_url}' está correta no .env? "
                f"(c) há firewall bloqueando a porta?"
            )
        else:
            msgs.append(
                f"❌ PING retornou HTTP {ping['status_code']}. "
                f"O servidor respondeu mas com erro inesperado."
            )
        # Sem ping, as demais etapas não fazem sentido
        msgs.append("⏭ Etapas seguintes ignoradas — bot inacessível.")
        return msgs

    msgs.append(f"✅ PING ok ({ping['latency_ms']}ms) — API do Freqtrade está respondendo.")

    # ── 2. Autenticação ──────────────────────────────────────────
    if not auth_step["ok"]:
        if auth_step["status_code"] == 401:
            msgs.append(
                f"❌ AUTH falhou (HTTP 401 Unauthorized). "
                f"Usuário '{auth[0]}' ou senha incorretos. "
                f"Verifique FREQTRADE_USER e FREQTRADE_PASSWORD no .env "
                f"e compare com api_server.username/password no config.json do bot."
            )
        elif auth_step["status_code"] == 403:
            msgs.append(
                f"❌ AUTH falhou (HTTP 403 Forbidden). "
                f"O usuário '{auth[0]}' existe mas não tem permissão. "
                f"Verifique o campo 'jwt_secret_key' e 'allow_cors' no config.json."
            )
        else:
            msgs.append(
                f"❌ AUTH falhou (HTTP {auth_step['status_code']}): {auth_step['error']}"
            )
    else:
        msgs.append(f"✅ AUTH ok ({auth_step['latency_ms']}ms) — credenciais válidas.")

    # ── 3. Config / dry_run / exchange ───────────────────────────
    if not config["ok"]:
        msgs.append(
            f"⚠ CONFIG inacessível ({config['error']}). "
            f"Não foi possível detectar modo dry_run ou exchange configurada."
        )
    else:
        msgs.append(f"✅ CONFIG ok ({config['latency_ms']}ms) — configuração lida com sucesso.")

    # ── 4. Balance / exchange conectada ──────────────────────────
    if not balance["ok"]:
        if balance["status_code"] == 502:
            msgs.append(
                f"❌ BALANCE falhou (HTTP 502 Bad Gateway). "
                f"O Freqtrade está vivo mas não consegue alcançar a Binance. "
                f"Verifique: (a) conexão de internet do servidor onde o bot roda, "
                f"(b) as chaves de API da Binance (key/secret) no config.json, "
                f"(c) se as chaves têm permissão de leitura de saldo."
            )
        elif balance["status_code"] == 500:
            msgs.append(
                f"❌ BALANCE falhou (HTTP 500). "
                f"Erro interno no Freqtrade ao consultar a exchange. "
                f"Verifique os logs do próprio bot: `freqtrade trade --logfile ft.log`"
            )
        elif balance["status_code"] is None:
            msgs.append(
                f"❌ BALANCE sem resposta: {balance['error']}. "
                f"O bot pode ter travado ao tentar conectar na exchange."
            )
        else:
            msgs.append(
                f"❌ BALANCE falhou (HTTP {balance['status_code']}): {balance['error']}"
            )
    else:
        msgs.append(f"✅ BALANCE ok ({balance['latency_ms']}ms) — exchange acessível e saldo lido.")

    # ── 5. Trades ────────────────────────────────────────────────
    if not trades["ok"]:
        msgs.append(
            f"⚠ TRADES falhou ({trades['error']}). "
            f"Histórico de operações indisponível."
        )
    else:
        msgs.append(f"✅ TRADES ok ({trades['latency_ms']}ms) — histórico de operações acessível.")

    # ── Resumo final ─────────────────────────────────────────────
    all_ok = all(s["ok"] for s in steps.values())
    if all_ok:
        msgs.append("🟢 Tudo operacional — os dados no dashboard devem ser reais (live).")
    elif steps["ping"]["ok"] and not steps["balance"]["ok"]:
        msgs.append(
            "🟡 Bot online mas exchange com problema. "
            "O dashboard mostrará dados mockados até a exchange responder."
        )

    return msgs