import { useState } from 'react'
import './App.css'
import { GraphView } from './components/GraphView'
import { ProgressView } from './components/ProgressView'
import { StatCard } from './components/StatCard'
import { UploadForm } from './components/UploadForm'
import { useJobProgress } from './hooks/useJobProgress'

type ViewState =
  | { status: 'form' }
  | { status: 'progress'; jobId: string }
  | { status: 'error'; message: string }

function App() {
  const [view, setView] = useState<ViewState>({ status: 'form' })
  const progress = useJobProgress(view.status === 'progress' ? view.jobId : null)

  function reset() {
    setView({ status: 'form' })
  }

  return (
    <div className="app">
      <header className="app-header">
        <p className="eyebrow">InkMap</p>
        <h1>Paper to knowledge graph</h1>
        <p className="subtitle">
          Upload a research paper or paste its text, and InkMap extracts the technologies, methods, people,
          and relationships it discusses into an interactive graph you can explore.
        </p>
      </header>

      {view.status === 'form' && (
        <UploadForm
          onStarted={(jobId) => setView({ status: 'progress', jobId })}
          onError={(message) => setView({ status: 'error', message })}
        />
      )}

      {view.status === 'error' && (
        <div className="panel error-panel">
          <p>{view.message}</p>
          <button onClick={reset}>Try again</button>
        </div>
      )}

      {view.status === 'progress' && !progress.result && !progress.error && (
        <ProgressView done={progress.done} total={progress.total} />
      )}

      {view.status === 'progress' && progress.error && (
        <div className="panel error-panel">
          <p>Extraction failed: {progress.error}</p>
          <button onClick={reset}>Try again</button>
        </div>
      )}

      {view.status === 'progress' && progress.result && (
        <>
          <div className="stats-row">
            <StatCard label="Entities" value={progress.result.nodes.length} />
            <StatCard label="Relationships" value={progress.result.edges.length} />
          </div>
          <GraphView graph={progress.result} />
          <button className="reset-button" onClick={reset}>
            Start over
          </button>
        </>
      )}
    </div>
  )
}

export default App
