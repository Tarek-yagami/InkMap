import { useEffect, useState } from 'react'
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

type Theme = 'light' | 'dark'

function App() {
  const [view, setView] = useState<ViewState>({ status: 'form' })
  const [theme, setTheme] = useState<Theme>('light')
  const progress = useJobProgress(view.status === 'progress' ? view.jobId : null)

  // On the document root, not the inner .app div: body's own background
  // (visible in the margins outside the centered content) needs to follow
  // the theme too, not just the content area.
  useEffect(() => {
    document.documentElement.dataset.theme = theme
  }, [theme])

  function reset() {
    setView({ status: 'form' })
  }

  function downloadGraphJson() {
    if (view.status !== 'progress' || !progress.result) return
    const blob = new Blob([JSON.stringify(progress.result, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = 'paper_graph.json'
    link.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="app">
      <div className="theme-toggle" role="group" aria-label="Theme">
        <button aria-pressed={theme === 'light'} onClick={() => setTheme('light')}>
          &#9728; Light
        </button>
        <button aria-pressed={theme === 'dark'} onClick={() => setTheme('dark')}>
          &#9789; Dark
        </button>
      </div>

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
          <GraphView graph={progress.result} theme={theme} />
          <div className="post-graph-actions">
            <button className="reset-button" onClick={downloadGraphJson}>
              Download JSON
            </button>
            <button className="reset-button reset-button-secondary" onClick={reset}>
              Start over
            </button>
          </div>
        </>
      )}
    </div>
  )
}

export default App
