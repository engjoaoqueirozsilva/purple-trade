import { useState, useCallback } from 'react'
import { useApi } from '../hooks/useApi'
import { MetricCard } from '../components/MetricCard'
import { TradesTable } from '../components/TradesTable'
import { LogTerminal } from '../components/LogTerminal'
import { Header } from '../components/Header'
import { DiagnosticsPanel } from '../components/Diagnosticspanel'

// ─────────────────────────────────────────
// Ícones inline (sem dependência externa)
// ─────────────────────────────────────────
const DollarIcon = ({ size = 14 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <line x1="12" y1="1" x2="12" y2="23" />
    <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
  </svg>
)
const TrendIcon = ({ size = 14 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
    <polyline points="17 6 23 6 23 12" />
  </svg>
)
const ActivityIcon = ({ size = 14 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
  </svg>
)
const ShieldIcon = ({ size = 14 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
  </svg>
)

// ─────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────
function fmt(n, decimals = 2) {
  return n != null
    ? Number(n).toLocaleString('pt-BR', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      })
    : '—'
}

/** Esqueleto pulsante para métricas enquanto carrega */
function SkeletonCard() {
  return (
    <div className="rounded-xl border border-white/5 bg-surface p-4 animate-pulse space-y-3">
      <div className="h-3 w-1/3 rounded bg-white/10" />
      <div className="h-6 w-1/2 rounded bg-white/10" />
      <div className="h-2 w-2/3 rounded bg-white/5" />
    </div>
  )
}

/** Banner de erro ou aviso inline */
function Banner({ type = 'warn', children }) {
  const styles = {
    warn:  'text-yellow/80 bg-yellow/5 border-yellow/15',
    error: 'text-red/80 bg-red/5 border-red/15',
    stale: 'text-text-dim bg-white/3 border-white/8',
  }
  const icons = { warn: '⚠', error: '✕', stale: '↻' }
  return (
    <div className={`flex items-center gap-2 text-xs border rounded-lg px-4 py-2.5 ${styles[type]}`}>
      <span>{icons[type]}</span>
      <span>{children}</span>
    </div>
  )
}

/**
 * Mapeia bot_state (API) para rótulo e cor legíveis pelo usuário.
 *
 *   offline           → ○ OFFLINE   (vermelho)
 *   online_no_exchange→ ◐ SEM EXCHANGE (amarelo)
 *   dry_run           → ● PAPER     (azul / info)
 *   live              → ● LIVE      (verde)
 */
function BotStateLabel({ state }) {
  if (!state) return <span className="text-text-dim">—</span>

  const map = {
    offline:            { label: '○ OFFLINE',      cls: 'text-red' },
    online_no_exchange: { label: '◐ SEM EXCHANGE', cls: 'text-yellow' },
    dry_run:            { label: '● PAPER',         cls: 'text-blue-400' },
    live:               { label: '● LIVE',          cls: 'text-green' },
  }
  const { label, cls } = map[state] ?? { label: state.toUpperCase(), cls: 'text-text-dim' }
  return <div className={`text-sm font-semibold tracking-wide ${cls}`}>{label}</div>
}

// ─────────────────────────────────────────
// Dashboard
// ─────────────────────────────────────────
export default function Dashboard() {
  const POLL = 15_000 // 15 segundos

  /**
   * lastUpdate é atualizado APENAS quando o useApi recebe uma resposta
   * válida do backend, via callback onSuccess — nunca por intervalo cego.
   */
  const [lastUpdate, setLastUpdate] = useState(null)
  const markUpdated = useCallback(() => {
    setLastUpdate(new Date().toLocaleTimeString('pt-BR', { hour12: false }))
  }, [])

  const {
    data: statusEnvelope,
    loading: statusLoading,
    error: statusError,
    isStale: statusStale,
  } = useApi('/status', { interval: POLL, onSuccess: markUpdated })

  const {
    data: balanceEnvelope,
    loading: balanceLoading,
    error: balanceError,
    isStale: balanceStale,
  } = useApi('/balance', { interval: POLL })

  const {
    data: tradesEnvelope,
    loading: tradesLoading,
    error: tradesError,
  } = useApi('/trades', { interval: POLL })

  const {
    data: logsEnvelope,
    loading: logsLoading,
    error: logsError,
  } = useApi('/logs', { interval: POLL })

  // ── Extrai os payloads do envelope padrão ──────────────────────
  const statusData  = statusEnvelope?.data   ?? null
  const balanceData = balanceEnvelope?.data  ?? null
  const trades      = tradesEnvelope?.data   ?? []
  const logs        = logsEnvelope?.data     ?? []

  const isMock      = statusEnvelope?.source === 'mock'
  const isStaleAny  = statusStale || balanceStale

  // ── Campos derivados ───────────────────────────────────────────
  const botState    = statusData?.bot_state   ?? null
  const strategy    = statusData?.strategy    ?? 'PurpleRSIEMA'
  const totalUsd    = balanceData?.total_usd  ?? null
  const profitPct   = statusData?.total_profit_pct ?? null
  const tradesCount = statusData?.trades_count ?? 0
  const winRate     = statusData?.win_rate     ?? null

  const anyError = statusError || balanceError || tradesError || logsError
  const coreLoading = statusLoading || balanceLoading

  return (
    <div className="min-h-screen bg-bg flex flex-col">
      <Header
        status={botState}
        lastUpdate={lastUpdate ?? '—'}
      />

      <main className="flex-1 px-4 md:px-6 py-6 max-w-7xl mx-auto w-full space-y-6">

        {/* ── Banners de estado ─────────────────────────────────── */}
        {isMock && (
          <Banner type="warn">
            Dados mockados — Freqtrade não conectado. Inicie o bot para dados em tempo real.
          </Banner>
        )}

        {anyError && !isMock && (
          <Banner type="error">
            Erro ao comunicar com o backend: {anyError}
          </Banner>
        )}

        {isStaleAny && !anyError && (
          <Banner type="stale">
            Dados desatualizados — última atualização às {lastUpdate ?? '—'}. Tentando reconectar…
          </Banner>
        )}

        {/* ── Métricas principais ───────────────────────────────── */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {coreLoading ? (
            <>
              <SkeletonCard />
              <SkeletonCard />
              <SkeletonCard />
              <SkeletonCard />
            </>
          ) : (
            <>
              <MetricCard
                label="Saldo Total"
                value={totalUsd != null ? `$${fmt(totalUsd)}` : '—'}
                sub={balanceData ? `livre: $${fmt(balanceData.free_usd)}` : undefined}
                icon={DollarIcon}
                accent
              />
              <MetricCard
                label="Lucro Hoje"
                value={
                  profitPct != null
                    ? (
                      <span className={profitPct >= 0 ? 'profit-positive' : 'profit-negative'}>
                        {profitPct >= 0 ? '+' : ''}{fmt(profitPct)}%
                      </span>
                    )
                    : '—'
                }
                sub={statusData ? `${statusData.wins}W / ${statusData.losses}L` : undefined}
                icon={TrendIcon}
              />
              <MetricCard
                label="Trades Hoje"
                value={tradesCount}
                sub={winRate != null ? `win rate ${fmt(winRate, 1)}%` : undefined}
                icon={ActivityIcon}
              />
              <MetricCard
                label="Status do Bot"
                value={<BotStateLabel state={botState} />}
                sub={strategy}
                icon={ShieldIcon}
              />
            </>
          )}
        </div>

        {/* ── Trades ───────────────────────────────────────────── */}
        <section>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-medium text-text-primary">Últimas Operações</h2>
            <span className="text-xs text-text-dim font-mono">
              {tradesLoading ? '…' : `${trades.length} registros`}
            </span>
          </div>
          {tradesLoading
            ? <div className="h-32 rounded-xl bg-surface animate-pulse" />
            : <TradesTable trades={trades} />
          }
        </section>

        {/* ── Logs ─────────────────────────────────────────────── */}
        <section>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-medium text-text-primary">Logs do Bot</h2>
            <span className="text-xs text-text-dim font-mono">
              {logsLoading ? '…' : `${logs.length} entradas`}
            </span>
          </div>
          {logsLoading
            ? <div className="h-48 rounded-xl bg-surface animate-pulse" />
            : <LogTerminal logs={logs} />
          }
        </section>
        <DiagnosticsPanel />
        {/* ── Footer ───────────────────────────────────────────── */}
        <footer className="text-center text-xs text-text-dim pb-2 font-mono">
          Purple Trade · uso pessoal · {new Date().getFullYear()}
        </footer>

      </main>
    </div>
  )
}