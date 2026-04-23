import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
})

export function useApi() {
  const runQuery = async (query, userId = null) => {
    const { data } = await api.post('/query', { query, user_id: userId })
    return data
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

  return {
    runQuery,
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
  }
}
