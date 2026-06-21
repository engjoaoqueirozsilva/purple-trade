export function MetricCard({ label, value, sub, icon: Icon, accent = false, className = '' }) {
  return (
    <div className={`card p-5 flex flex-col gap-3 ${accent ? 'shadow-purple-glow-sm' : ''} ${className}`}>
      <div className="flex items-center justify-between">
        <span className="stat-label">{label}</span>
        {Icon && (
          <span className={`w-7 h-7 flex items-center justify-center rounded-lg ${
            accent ? 'bg-purple-primary/20 text-purple-secondary' : 'bg-surface-2 text-text-muted'
          }`}>
            <Icon size={14} />
          </span>
        )}
      </div>
      <div className="stat-value">{value ?? '—'}</div>
      {sub && <div className="text-xs text-text-muted">{sub}</div>}
    </div>
  )
}
