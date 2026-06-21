/**
 * DiagnosticsPanel — consome GET /api/diagnostics e exibe um relatório
 * visual de cada etapa da conexão com o Freqtrade.
 *
 * Uso no Dashboard (exemplo):
 *   import { DiagnosticsPanel } from '../components/DiagnosticsPanel'
 *   // renderize abaixo do LogTerminal ou em uma rota /diagnostics separada
 *   <DiagnosticsPanel />
 */

import { useState } from 'react'
import { useApi } from '../hooks/useApi'

// ─────────────────────────────────────────
// Ícones
// ─────────────────────────────────────────
const RefreshIcon = ({ size = 14, spinning = false }) => (
  <svg
    width={size} height={size} viewBox="0 0 24 24"
    fill="none" stroke="currentColor" strokeWidth="2"
    style={{ animation: spinning ? 'spin 1s linear infinite' : 'none' }}
  >
    <polyline points="23 4 23 10 17 10" />
    <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
    <style>{`@keyframes spin { from { transform: rotate(0deg) } to { transform: rotate(360deg) } }`}</style>
  </svg>
)

// ─────────────────────────────────────────
// Mapa visual por overall
// ─────────────────────────────────────────
const OVERALL_STYLE = {
  ok:      { dot: 'bg-green',  label: 'OPERACIONAL',    border: 'border-green/20',  bg: 'bg-green/5'  },
  partial: { dot: 'bg-yellow', label: 'PARCIAL',        border: 'border-yellow/20', bg: 'bg-yellow/5' },
  failed:  { dot: 'bg-red',    label: 'FALHA TOTAL',    border: 'border-red/20',    bg: 'bg-red/5'    },
}

// ─────────────────────────────────────────
// Linha de step individual
// ─────────────────────────────────────────
function StepRow({ name, step }) {
  const [open, setOpen] = useState(false)

  const statusDot = step.ok
    ? 'bg-green text-green'
    : 'bg-red text-red'

  const latencyColor =
    step.latency_ms == null   ? 'text-text-dim' :
    step.latency_ms < 200     ? 'text-green/80' :
    step.latency_ms < 1000    ? 'text-yellow/80' :
                                'text-red/80'

  return (
    <div className="border-b border-white/5 last:border-0">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center gap-3 px-4 py-3 hover:bg-white/2 transition-colors text-left"
      >
        {/* Status dot */}
        <span className={`shrink-0 w-2 h-2 rounded-full ${step.ok ? 'bg-green' : 'bg-red'}`} />

        {/* Nome do step */}
        <span className="font-mono text-xs font-semibold uppercase tracking-widest text-text-primary w-20 shrink-0">
          {name}
        </span>

        {/* HTTP status */}
        <span className="font-mono text-xs text-text-dim w-16 shrink-0">
          {step.status_code != null ? `HTTP ${step.status_code}` : '—'}
        </span>

        {/* Latência */}
        <span className={`font-mono text-xs w-20 shrink-0 ${latencyColor}`}>
          {step.latency_ms != null ? `${step.latency_ms}ms` : '—'}
        </span>

        {/* Erro resumido ou ok */}
        <span className={`font-mono text-xs truncate flex-1 ${step.ok ? 'text-green/70' : 'text-red/80'}`}>
          {step.ok ? 'ok' : step.error}
        </span>

        {/* Expand toggle */}
        {(step.body || step.error) && (
          <span className="text-text-dim text-xs ml-2 shrink-0">{open ? '▲' : '▼'}</span>
        )}
      </button>

      {/* Detalhe expandido */}
      {open && (step.body || step.error) && (
        <div className="px-4 pb-3 space-y-2">
          {step.error && (
            <div className="rounded-lg bg-red/5 border border-red/15 px-3 py-2">
              <p className="text-[11px] font-mono text-red/80 break-all">{step.error}</p>
            </div>
          )}
          {step.body && (
            <div className="rounded-lg bg-white/3 border border-white/8 px-3 py-2">
              <p className="text-[10px] text-text-dim font-mono mb-1">body (300 chars):</p>
              <p className="text-[11px] font-mono text-text-primary break-all whitespace-pre-wrap">
                {step.body}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ─────────────────────────────────────────
// DiagnosticsPanel
// ─────────────────────────────────────────
export function DiagnosticsPanel() {
  const { data, loading, error, refetch } = useApi('/diagnostics')

  const overall = data?.overall ?? null
  const ovStyle = OVERALL_STYLE[overall] ?? OVERALL_STYLE.failed

  return (
    <div className="rounded-xl border border-white/8 bg-surface overflow-hidden">

      {/* Cabeçalho */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/6 bg-white/2">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-text-primary">Diagnóstico de Conexão</span>
          {data && (
            <span className={`text-[10px] font-mono font-semibold uppercase tracking-widest px-2 py-0.5 rounded-full border ${ovStyle.border} ${ovStyle.bg} flex items-center gap-1.5`}>
              <span className={`w-1.5 h-1.5 rounded-full ${ovStyle.dot}`} />
              {ovStyle.label}
            </span>
          )}
        </div>

        <button
          onClick={refetch}
          disabled={loading}
          className="flex items-center gap-1.5 text-xs text-text-dim hover:text-text-primary transition-colors disabled:opacity-40"
        >
          <RefreshIcon size={13} spinning={loading} />
          {loading ? 'testando…' : 'testar agora'}
        </button>
      </div>

      {/* Meta info */}
      {data && (
        <div className="flex items-center gap-6 px-4 py-2.5 border-b border-white/5 bg-white/1">
          <span className="text-[11px] font-mono text-text-dim">
            url: <span className="text-text-primary">{data.target_url}</span>
          </span>
          <span className="text-[11px] font-mono text-text-dim">
            usuário: <span className="text-text-primary">{data.auth_user}</span>
          </span>
          <span className="text-[11px] font-mono text-text-dim">
            resultado: <span className="text-text-primary">{data.passed}</span>
          </span>
          <span className="text-[11px] font-mono text-text-dim ml-auto">
            {data.timestamp ? new Date(data.timestamp).toLocaleTimeString('pt-BR', { hour12: false }) : '—'}
          </span>
        </div>
      )}

      {/* Loading skeleton */}
      {loading && !data && (
        <div className="px-4 py-6 space-y-3 animate-pulse">
          {['ping', 'auth', 'config', 'balance', 'trades'].map(s => (
            <div key={s} className="flex items-center gap-3">
              <div className="w-2 h-2 rounded-full bg-white/10" />
              <div className="h-3 w-16 rounded bg-white/10" />
              <div className="h-3 w-24 rounded bg-white/8" />
              <div className="h-3 flex-1 rounded bg-white/5" />
            </div>
          ))}
        </div>
      )}

      {/* Erro de rede (o próprio /diagnostics falhou) */}
      {error && !data && (
        <div className="px-4 py-6 text-center">
          <p className="text-xs text-red/80 font-mono">
            Não foi possível alcançar /api/diagnostics: {error}
          </p>
          <p className="text-xs text-text-dim mt-1">
            Verifique se o backend Python está rodando.
          </p>
        </div>
      )}

      {/* Steps */}
      {data?.steps && (
        <div>
          {Object.entries(data.steps).map(([name, step]) => (
            <StepRow key={name} name={name} step={step} />
          ))}
        </div>
      )}

      {/* Diagnóstico em linguagem natural */}
      {data?.diagnosis?.length > 0 && (
        <div className="px-4 py-4 border-t border-white/6 space-y-2">
          <p className="text-[11px] text-text-dim font-mono uppercase tracking-widest mb-3">
            diagnóstico
          </p>
          {data.diagnosis.map((msg, i) => (
            <p key={i} className="text-xs text-text-primary font-mono leading-relaxed">
              {msg}
            </p>
          ))}
        </div>
      )}

    </div>
  )
}