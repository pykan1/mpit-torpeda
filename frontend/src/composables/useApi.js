import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const API_BASE = `${API_URL}/api/v1`

export const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
})

export function useApi() {
  const runQuery = async (query, userId = null, manualApproval = false) => {
    const { data } = await api.post('/query', { query, user_id: userId, manual_approval: manualApproval })
    return data
  }

  const runQueryStream = async (query, userId = null, { onThinking, manualApproval = false } = {}) => {
    const response = await fetch(`${API_BASE}/query/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
      },
      body: JSON.stringify({ query, user_id: userId, manual_approval: manualApproval }),
    })

    if (!response.ok || !response.body) {
      throw new Error(`Streaming request failed with status ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let finalResult = null

    while (true) {
      const { value, done } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const events = buffer.split('\n\n')
      buffer = events.pop() || ''

      for (const eventBlock of events) {
        const dataLines = eventBlock
          .split('\n')
          .filter((line) => line.startsWith('data:'))
          .map((line) => line.replace(/^data:\s?/, ''))

        if (!dataLines.length) continue
        const dataRaw = dataLines.join('\n').trim()
        if (!dataRaw || dataRaw === '[DONE]') continue

        let event
        try {
          event = JSON.parse(dataRaw)
        } catch {
          continue
        }

        if (event.type === 'thinking' && event.delta) {
          onThinking?.(event.delta)
        } else if (event.type === 'final') {
          finalResult = event.data
        } else if (event.type === 'error') {
          throw new Error(event.error || 'Streaming error')
        }
      }
    }

    if (!finalResult) {
      throw new Error('Streaming finished without final result')
    }

    return finalResult
  }

  const getTemplates = async () => {
    const { data } = await api.get('/templates')
    return data
  }

  const getReports = async () => {
    const { data } = await api.get('/reports')
    return data
  }

  const saveReport = async (payload) => {
    const { data } = await api.post('/reports', payload)
    return data
  }

  const deleteReport = async (id) => {
    const { data } = await api.delete(`/reports/${id}`)
    return data
  }

  const runReport = async (id) => {
    const { data } = await api.post(`/reports/${id}/run`)
    return data
  }

  const getLogs = async (limit = 50) => {
    const { data } = await api.get('/logs', { params: { limit } })
    return data
  }

  const getLog = async (id) => {
    const { data } = await api.get(`/logs/${id}`)
    return data
  }

  const getUsers = async () => {
    const { data } = await api.get('/users')
    return data
  }

  const updateUserRole = async (userId, role) => {
    const { data } = await api.patch(`/users/${userId}/role`, { role })
    return data
  }

  const getSemanticTerms = async () => {
    const { data } = await api.get('/semantic')
    return data
  }

  const createSemanticTerm = async (payload) => {
    const { data } = await api.post('/semantic', payload)
    return data
  }

  const getStats = async () => {
    const { data } = await api.get('/stats')
    return data
  }

  const validateSql = async (sql) => {
    const { data } = await api.post('/validate-sql', { sql })
    return data
  }

  const executePreparedSql = async (payload) => {
    const { data } = await api.post('/query/execute', payload)
    return data
  }

  return {
    runQuery,
    runQueryStream,
    getTemplates,
    getReports,
    saveReport,
    deleteReport,
    runReport,
    getLogs,
    getLog,
    getUsers,
    updateUserRole,
    getSemanticTerms,
    createSemanticTerm,
    getStats,
    validateSql,
    executePreparedSql,
  }
}
