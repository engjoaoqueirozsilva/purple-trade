/**
 * LogTerminal — exibe logs do bot com colorização por nível.
 *
 * Espera uma lista de objetos com a forma:
 *   { timestamp: string (ISO), level: string, message: string }
 *
 * Níveis reconhecidos (case-insensitive):
 *   ERROR   → vermelho
 *   WARNING → amarelo
 *   INFO    → neutro (branco/cinza claro)
 *   DEBUG   → cinza apagado
 *
 * O terminal tem scroll interno e auto-scroll para o fim quando
 * novos logs chegam. O botão "↓ fim" aparece quando o usuário
 * rola manualmente para cima.
 */

import { useEffect, useRef, useState } from 'react'

// ─────────────────────────────────────────
// Mapa de estilos por nível
// ─────────────────────────────────────────
const LEVEL_STYLES = {
  ERROR:   { badge: 'text-red   bg-red/10   border-red/20',   text: 'text-red/90'      },
  WARNING: { badge: 'text-yellow bg-yellow/10 border-yellow/20', text: 'text-yellow/90' },
  INFO:    { badge: 'text-text-primary bg-white/5 border-white/10', text: 'text-text-primary' },
  DEBUG:   { badge: 'text-text-dim bg-white/3  border-white/5',  text: 'text-text-dim'  },
}

function levelStyles(level = 'INFO') {
  return LEVEL_STYLES[(level ?? '').toUpperCase()] ?? LEVEL_STYLES.INFO
}

// ─────────────────────────────────────────
// Formata timestamp ISO → HH:MM:SS
// ─────────────────────────────────────────
function fmtTime(iso) {
  try {
    return new Date(iso).toLocaleTimeString('pt-BR', { hour12: false })
  } catch {
    return iso ?? ''
  }
}

// ─────────────────────────────────────────
// Linha individual do log
// ─────────────────────────────────────────
function LogLine({ entry }) {
  const { badge, text } = levelStyles(entry.level)
  return (
    <div className="flex items-start gap-3 py-1 group hover:bg-white/2 rounded px-1 -mx-1 transition-colors">
      {/* Timestamp */}
      <span className="shrink-0 text-text-dim font-mono text-[11px] mt-px w-[68px]">
        {fmtTime(entry.timestamp)}
      </span>

      {/* Badge de nível */}
      <span className={`shrink-0 font-mono text-[10px] font-semibold tracking-widest uppercase border rounded px-1.5 py-px mt-px ${badge}`}>
        {(entry.level ?? 'INFO').slice(0, 4)}
      </span>

      {/* Mensagem */}
      <span className={`font-mono text-xs leading-relaxed break-all ${text}`}>
        {entry.message}
      </span>
    </div>
  )
}

// ─────────────────────────────────────────
// LogTerminal
// ─────────────────────────────────────────
export function LogTerminal({ logs = [] }) {
  const containerRef = useRef(null)
  const [userScrolled, setUserScrolled] = useState(false)

  // Auto-scroll para o fim quando chegam novos logs,
  // a menos que o usuário tenha rolado manualmente para cima
  useEffect(() => {
    if (userScrolled) return
    const el = containerRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [logs, userScrolled])

  function handleScroll() {
    const el = containerRef.current
    if (!el) return
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 32
    setUserScrolled(!atBottom)
  }

  function scrollToBottom() {
    const el = containerRef.current
    if (el) el.scrollTop = el.scrollHeight
    setUserScrolled(false)
  }

  return (
    <div className="relative rounded-xl border border-white/8 bg-surface overflow-hidden">
      {/* Cabeçalho estilo terminal */}
      <div className="flex items-center gap-1.5 px-4 py-2.5 border-b border-white/6 bg-white/2">
        <span className="w-2.5 h-2.5 rounded-full bg-red/50"    />
        <span className="w-2.5 h-2.5 rounded-full bg-yellow/50" />
        <span className="w-2.5 h-2.5 rounded-full bg-green/50"  />
        <span className="ml-3 text-[11px] text-text-dim font-mono tracking-wide">
          freqtrade · stdout
        </span>
      </div>

      {/* Corpo do log */}
      <div
        ref={containerRef}
        onScroll={handleScroll}
        className="h-64 overflow-y-auto px-4 py-3 space-y-0.5 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent"
      >
        {logs.length === 0 ? (
          <p className="text-text-dim text-xs font-mono py-8 text-center">
            Nenhum log disponível.
          </p>
        ) : (
          logs.map((entry, i) => <LogLine key={i} entry={entry} />)
        )}
      </div>

      {/* Botão "ir para o fim" — só aparece quando o usuário rolou para cima */}
      {userScrolled && (
        <button
          onClick={scrollToBottom}
          className="absolute bottom-3 right-3 text-[11px] font-mono text-text-dim bg-surface border border-white/10 rounded-full px-3 py-1 hover:text-text-primary hover:border-white/20 transition-colors"
        >
          ↓ fim
        </button>
      )}
    </div>
  )
}