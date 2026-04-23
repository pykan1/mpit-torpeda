import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useApi } from '@/composables/useApi'

export const useQueryStore = defineStore('query', () => {
  const { runQuery, getTemplates } = useApi()

  const loading = ref(false)
  const error = ref(null)
  const currentResult = ref(null)
  const templates = ref([])
  const history = ref([])

  async function executeQuery(queryText) {
    loading.value = true
    error.value = null
    try {
      const result = await runQuery(queryText)
      currentResult.value = result
      history.value.unshift({ query: queryText, result, timestamp: new Date().toISOString() })
      if (history.value.length > 20) history.value.pop()
      return result
    } catch (e) {
      error.value = e.response?.data?.detail?.error || e.message || 'Ошибка запроса'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function fetchTemplates() {
    templates.value = await getTemplates()
  }

  function clearResult() {
    currentResult.value = null
    error.value = null
  }

  return { loading, error, currentResult, templates, history, executeQuery, fetchTemplates, clearResult }
})
