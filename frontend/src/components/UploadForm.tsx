import { useEffect, useState } from 'react'
import { fetchProviders, startJob } from '../api/client'
import type { ProviderSummary } from '../types'

interface Props {
  onStarted: (jobId: string) => void
  onError: (message: string) => void
}

export function UploadForm({ onStarted, onError }: Props) {
  const [providers, setProviders] = useState<ProviderSummary[]>([])
  const [provider, setProvider] = useState('')
  const [model, setModel] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [text, setText] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    fetchProviders()
      .then((list) => {
        setProviders(list)
        if (list.length > 0) {
          setProvider(list[0].name)
          setModel(list[0].models[0])
        }
      })
      .catch((err) => onError(err.message))
  }, [onError])

  const activeProvider = providers.find((p) => p.name === provider)
  const isOllama = provider === 'Ollama (local)'

  function handleProviderChange(name: string) {
    setProvider(name)
    const found = providers.find((p) => p.name === name)
    if (found) setModel(found.models[0])
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    if (!file && !text.trim()) {
      onError('Upload a document or paste some text first.')
      return
    }

    const formData = new FormData()
    if (file) formData.append('file', file)
    if (text.trim()) formData.append('text', text)
    formData.append('provider', provider)
    formData.append('model', model)

    setSubmitting(true)
    try {
      const { job_id } = await startJob(formData)
      onStarted(job_id)
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Failed to start extraction.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form className="panel upload-form" onSubmit={handleSubmit}>
      <label className="field">
        <span>Upload a document</span>
        <input
          type="file"
          accept=".pdf,.docx,.pptx"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />
      </label>

      <label className="field">
        <span>...or paste text directly</span>
        <textarea rows={6} value={text} onChange={(e) => setText(e.target.value)} />
      </label>

      <div className="field-row">
        <label className="field">
          <span>Provider</span>
          <select value={provider} onChange={(e) => handleProviderChange(e.target.value)}>
            {providers.map((p) => (
              <option key={p.name} value={p.name}>
                {p.name}
              </option>
            ))}
          </select>
        </label>

        <label className="field">
          <span>Model</span>
          {isOllama ? (
            <input value={model} onChange={(e) => setModel(e.target.value)} />
          ) : (
            <select value={model} onChange={(e) => setModel(e.target.value)}>
              {activeProvider?.models.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          )}
        </label>
      </div>

      <button type="submit" disabled={submitting || !provider}>
        {submitting ? 'Starting...' : 'Generate graph'}
      </button>
    </form>
  )
}
