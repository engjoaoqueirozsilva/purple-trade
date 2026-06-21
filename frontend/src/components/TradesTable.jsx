function fmt(n, decimals = 2) {
  return n != null ? Number(n).toFixed(decimals) : '—'
}

function dateShort(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })
}

export function TradesTable({ trades = [] }) {
  if (!trades.length) {
    return (
      <div className="card p-8 text-center text-text-muted text-sm">
        Nenhuma operação registrada ainda.
      </div>
    )
  }

  return (
    <div className="card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border">
              <th className="px-4 py-3 text-left stat-label">Par</th>
              <th className="px-4 py-3 text-left stat-label">Abertura</th>
              <th className="px-4 py-3 text-right stat-label">Preço entrada</th>
              <th className="px-4 py-3 text-right stat-label">Preço saída</th>
              <th className="px-4 py-3 text-right stat-label">P&L %</th>
              <th className="px-4 py-3 text-center stat-label">Status</th>
            </tr>
          </thead>
          <tbody>
            {trades.map((t, i) => (
              <tr
                key={t.trade_id ?? i}
                className="border-b border-border/50 hover:bg-surface-2/50 transition-colors"
              >
                <td className="px-4 py-3 font-medium text-text-primary font-mono text-xs">
                  {t.pair}
                </td>
                <td className="px-4 py-3 text-text-muted font-mono text-xs">
                  {dateShort(t.open_date)}
                </td>
                <td className="px-4 py-3 text-right text-text-primary font-mono text-xs">
                  ${fmt(t.open_rate, 2)}
                </td>
                <td className="px-4 py-3 text-right text-text-primary font-mono text-xs">
                  {t.is_open ? <span className="text-yellow">aberto</span> : `$${fmt(t.close_rate, 2)}`}
                </td>
                <td className={`px-4 py-3 text-right font-mono text-xs font-semibold ${
                  t.profit_pct >= 0 ? 'profit-positive' : 'profit-negative'
                }`}>
                  {t.profit_pct >= 0 ? '+' : ''}{fmt(t.profit_pct)}%
                </td>
                <td className="px-4 py-3 text-center">
                  {t.is_open ? (
                    <span className="inline-flex items-center gap-1 text-xs text-yellow bg-yellow/10 border border-yellow/20 px-2 py-0.5 rounded-full">
                      <span className="w-1 h-1 rounded-full bg-yellow animate-pulse" />
                      aberto
                    </span>
                  ) : (
                    <span className="inline-flex items-center text-xs text-text-muted bg-surface-2 border border-border px-2 py-0.5 rounded-full">
                      fechado
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
