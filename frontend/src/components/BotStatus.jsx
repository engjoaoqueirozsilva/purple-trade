export function BotStatus({ status }) {
  const running = status === 'running'

  return (
    <div className={running ? 'badge-running' : 'badge-stopped'}>
      <span className={`w-1.5 h-1.5 rounded-full ${running ? 'bg-green animate-pulse-slow' : 'bg-red'}`} />
      {running ? 'RUNNING' : 'STOPPED'}
    </div>
  )
}
