interface Props {
  done: number
  total: number
}

export function ProgressView({ done, total }: Props) {
  const pct = total > 0 ? Math.round((done / total) * 100) : 0

  return (
    <div className="panel progress-view">
      <p className="progress-label">
        Extracting entities and relationships... {total > 0 ? `(${done}/${total} chunks)` : ''}
      </p>
      <div className="progress-bar">
        <div className="progress-bar-fill" style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}
