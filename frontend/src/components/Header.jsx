import { BotStatus } from './BotStatus'

export function Header({ status, lastUpdate }) {
  return (
    <header className="flex items-center justify-between py-4 px-6 border-b border-border bg-surface/50 backdrop-blur-sm sticky top-0 z-10">
      <div className="flex items-center gap-3">
        {/* Logo mark */}
        <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-purple-primary to-purple-secondary flex items-center justify-center shadow-purple-glow-sm">
          <span className="text-white text-xs font-bold">P</span>
        </div>
        <span className="font-semibold text-text-primary tracking-tight">Purple Trade</span>
        <span className="text-text-dim text-xs hidden sm:block">/ dashboard</span>
      </div>

      <div className="flex items-center gap-4">
        {lastUpdate && (
          <span className="text-xs text-text-dim font-mono hidden md:block">
            atualizado {lastUpdate}
          </span>
        )}
        {status && <BotStatus status={status} />}
      </div>
    </header>
  )
}
