import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { UploadForm } from './UploadForm'

vi.mock('../api/client')

const mockedFetchProviders = vi.mocked(client.fetchProviders)
const mockedStartJob = vi.mocked(client.startJob)

const PROVIDERS = [
  { name: 'Groq', models: ['openai/gpt-oss-120b', 'openai/gpt-oss-20b'] },
  { name: 'Ollama (local)', models: ['llama3.1', 'qwen2.5'] },
]

describe('UploadForm', () => {
  beforeEach(() => {
    mockedFetchProviders.mockReset()
    mockedStartJob.mockReset()
    mockedFetchProviders.mockResolvedValue(PROVIDERS)
  })

  it('defaults to the first provider and its first model once loaded', async () => {
    render(<UploadForm onStarted={vi.fn()} onError={vi.fn()} />)
    await waitFor(() => expect(screen.getByText('Groq')).toBeInTheDocument())
    expect(screen.getByRole('option', { name: 'openai/gpt-oss-120b', selected: true })).toBeInTheDocument()
  })

  it('shows a free-text model field for Ollama instead of a select', async () => {
    const user = userEvent.setup()
    render(<UploadForm onStarted={vi.fn()} onError={vi.fn()} />)
    await waitFor(() => expect(screen.getByText('Groq')).toBeInTheDocument())

    await user.selectOptions(screen.getByLabelText('Provider'), 'Ollama (local)')
    expect(screen.getByLabelText('Model')).toHaveValue('llama3.1')
    expect(screen.getByLabelText('Model').tagName).toBe('INPUT')
  })

  it('reports an error instead of submitting when neither file nor text is given', async () => {
    const user = userEvent.setup()
    const onError = vi.fn()
    render(<UploadForm onStarted={vi.fn()} onError={onError} />)
    await waitFor(() => expect(screen.getByText('Groq')).toBeInTheDocument())

    await user.click(screen.getByRole('button', { name: 'Generate graph' }))
    expect(onError).toHaveBeenCalledWith('Upload a document or paste some text first.')
    expect(mockedStartJob).not.toHaveBeenCalled()
  })

  it('starts a job with the pasted text and reports the job id back', async () => {
    const user = userEvent.setup()
    const onStarted = vi.fn()
    mockedStartJob.mockResolvedValue({ job_id: 'job-123' })
    render(<UploadForm onStarted={onStarted} onError={vi.fn()} />)
    await waitFor(() => expect(screen.getByText('Groq')).toBeInTheDocument())

    await user.type(screen.getByLabelText('...or paste text directly'), 'The Transformer relies on attention.')
    await user.click(screen.getByRole('button', { name: 'Generate graph' }))

    await waitFor(() => expect(onStarted).toHaveBeenCalledWith('job-123'))
    const submittedFormData = mockedStartJob.mock.calls[0][0]
    expect(submittedFormData.get('text')).toBe('The Transformer relies on attention.')
    expect(submittedFormData.get('provider')).toBe('Groq')
  })
})
