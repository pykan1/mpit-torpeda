import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useApi } from '@/composables/useApi'

export const useQueryStore = defineStore('query', () => {
  const { runQueryStream, executePreparedSql, getTemplates } = useApi()

  const loading = ref(false)
  const error = ref(null)
  const currentResult = ref(null)
  const thinkingPreview = ref('')
  const templates = ref([])
  const history = ref([])

  async function executeQuery(queryText, manualApproval = false) {
    loading.value = true
    error.value = null
    thinkingPreview.value = ''
    currentResult.value = null
    try {
      const result = await runQueryStream(queryText, null, {
        manualApproval,
        onThinking: (delta) => {
          thinkingPreview.value += delta
        },
      })
      currentResult.value = result
      history.value.unshift({ query: queryText, result, timestamp: new Date().toISOString() })
      if (history.value.length > 20) history.value.pop()
      return result
    } catch (e) {
      error.value = e.response?.data?.detail?.error || e.message || 'Ошибка запроса'
      throw e
    } finally {
      loading.value = false
      thinkingPreview.value = ''
    }
  }

  async function fetchTemplates() {
    templates.value = await getTemplates()
  }

  function clearResult() {
    currentResult.value = null
    error.value = null
  }

  async function executeApprovedCurrentSql() {
    if (!currentResult.value?.sql || !currentResult.value?.awaiting_manual_execution) return null
    loading.value = true
    error.value = null
    try {
      const result = await executePreparedSql({
        natural_query: currentResult.value.natural_query,
        interpretation: currentResult.value.interpretation || '',
        sql: currentResult.value.sql,
        thinking: currentResult.value.thinking || '',
        confidence: currentResult.value.confidence || 0.8,
      })
      currentResult.value = result
      history.value.unshift({ query: result.natural_query, result, timestamp: new Date().toISOString() })
      if (history.value.length > 20) history.value.pop()
      return result
    } catch (e) {
      error.value = e.response?.data?.detail?.error || e.message || 'Ошибка исполнения SQL'
      throw e
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    error,
    currentResult,
    thinkingPreview,
    templates,
    history,
    executeQuery,
    executeApprovedCurrentSql,
    fetchTemplates,
    clearResult,
  }
})
