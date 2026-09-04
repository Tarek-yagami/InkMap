interface Props {
  label: string
  value: number
}

export function StatCard({ label, value }: Props) {
  return (
    <div className="stat-card">
      <span className="stat-value">{value}</span>
      <span className="stat-label">{label}</span>
    </div>
  )
}
