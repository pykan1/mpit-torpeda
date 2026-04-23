<template>
  <div class="flex flex-col min-h-screen">
    <!-- Header -->
    <header class="sticky top-0 z-10 bg-white/80 backdrop-blur-md border-b border-gray-100 px-8 py-4">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-xl font-bold text-gray-900">Аналитика на естественном языке</h1>
          <p class="text-sm text-gray-500 mt-0.5">Задайте вопрос о данных Drivee простыми словами</p>
        </div>
        <div class="flex items-center gap-3">
          <div v-if="store.currentResult" class="flex items-center gap-2 text-xs text-gray-500">
            <div class="w-1.5 h-1.5 rounded-full bg-drivee-500"></div>
            {{ store.currentResult.result?.row_count || 0 }} строк
          </div>
          <button
            v-if="store.currentResult && !store.currentResult.is_fallback && store.currentResult.sql"
            @click="showSaveModal = true"
            class="btn-secondary text-sm"
          >
            <IconSave class="w-4 h-4" /> Сохранить отчёт
          </button>
        </div>
      </div>
    </header>

    <div class="flex-1 flex flex-col px-8 py-6 max-w-5xl mx-auto w-full">
      <!-- Templates -->
      <div v-if="!store.currentResult && !store.loading" class="mb-8 animate-fade-in">
        <h2 class="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Популярные запросы</h2>
        <div class="grid grid-cols-2 gap-3">
          <button
            v-for="tmpl in store.templates"
            :key="tmpl.id"
            @click="fillTemplate(tmpl.query)"
            class="card-hover text-left group"
          >
            <div class="flex items-start gap-3">
              <component :is="templateIcon(tmpl.category)" class="w-6 h-6 text-drivee-500 flex-shrink-0 mt-0.5" />
              <div>
                <div class="font-medium text-gray-800 text-sm group-hover:text-drivee-700 transition-colors">{{ tmpl.title }}</div>
                <div class="text-xs text-gray-400 mt-1 leading-relaxed">{{ tmpl.query }}</div>
              </div>
            </div>
          </button>
        </div>
      </div>

      <!-- Result area -->
      <div v-if="store.currentResult || store.loading || store.error" class="mb-6 animate-slide-up">
        <!-- Loading -->
        <div v-if="store.loading" class="card flex items-center justify-center py-16">
          <div class="text-center w-full max-w-2xl">
            <div class="relative w-16 h-16 mx-auto mb-4">
              <div class="w-16 h-16 rounded-full border-4 border-drivee-100 border-t-drivee-500 animate-spin"></div>
              <div class="absolute inset-0 flex items-center justify-center">
                <IconBrain class="w-6 h-6 text-drivee-500" />
              </div>
            </div>
            <p class="text-gray-600 font-medium">ИИ анализирует запрос...</p>
            <p class="text-xs text-gray-400 mt-1">Генерирую SQL и размышляю</p>
            <div v-if="store.thinkingPreview" class="mt-5 text-left">
              <ThinkingLog :thinking="store.thinkingPreview" />
              <div ref="thinkingBottomRef" class="h-1"></div>
            </div>
          </div>
        </div>

        <!-- Error -->
        <div v-else-if="store.error" class="card border-red-200 bg-red-50">
          <div class="flex items-start gap-3">
            <IconX class="w-6 h-6 text-red-500 flex-shrink-0 mt-0.5" />
            <div>
              <p class="font-semibold text-red-700">Ошибка выполнения</p>
              <p class="text-sm text-red-600 mt-1">{{ store.error }}</p>
            </div>
          </div>
        </div>

        <!-- Success result -->
        <div v-else-if="store.currentResult" class="space-y-4">
          <!-- Interpretation -->
          <div class="card border-drivee-100 bg-gradient-to-br from-drivee-50 to-white">
            <div class="flex items-start gap-3">
              <div class="w-9 h-9 rounded-xl gradient-brand flex items-center justify-center text-white text-sm font-bold flex-shrink-0">AI</div>
              <div class="flex-1">
                <p class="font-semibold text-gray-800 mb-1">Я понял запрос так:</p>
                <p class="text-gray-700 leading-relaxed">{{ store.currentResult.interpretation }}</p>
                <div class="mt-3 flex items-center gap-3">
                  <div class="flex items-center gap-1.5 text-xs">
                    <div class="bg-gray-100 rounded-full h-1.5 w-24">
                      <div class="bg-drivee-500 h-1.5 rounded-full transition-all" :style="{ width: `${store.currentResult.confidence * 100}%` }"></div>
                    </div>
                    <span class="text-gray-500">уверенность {{ Math.round(store.currentResult.confidence * 100) }}%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Thinking log -->
          <div v-if="store.currentResult.thinking && !store.currentResult.is_fallback" class="card">
            <ThinkingLog :thinking="store.currentResult.thinking" />
          </div>

          <div v-if="store.currentResult.is_fallback" class="card border-blue-100 bg-blue-50">
            <p class="text-sm text-blue-700">
              Отправьте запрос по данным Drivee: выручка, поездки, отмены, водители, города, периоды.
            </p>
          </div>

          <!-- SQL -->
          <div v-if="!store.currentResult.is_fallback && store.currentResult.sql" class="card">
            <div class="flex items-center justify-between mb-3">
              <span class="text-sm font-semibold text-gray-600 flex items-center gap-2">
                <IconSearch class="w-4 h-4" /> Сгенерированный SQL
              </span>
              <button @click="copySql" class="text-xs text-drivee-600 hover:text-drivee-700 font-medium transition-colors flex items-center gap-1">
                <IconCheck v-if="copied" class="w-3.5 h-3.5" />
                {{ copied ? 'Скопировано' : 'Копировать' }}
              </button>
            </div>
            <div class="sql-block">{{ store.currentResult.sql }}</div>
          </div>

          <!-- Guardrail -->
          <div v-if="!store.currentResult.is_fallback && store.currentResult.sql" class="card">
            <h3 class="text-sm font-semibold text-gray-600 mb-3 flex items-center gap-2">
              <IconShield class="w-4 h-4" /> Проверка безопасности
            </h3>
            <GuardrailBadge :guardrail="store.currentResult.guardrail" />
          </div>

          <!-- Chart & Table -->
          <div v-if="!store.currentResult.is_fallback && store.currentResult.result" class="card">
            <div class="flex items-center justify-between mb-4">
              <h3 class="font-semibold text-gray-800 flex items-center gap-2">
                <IconChart class="w-5 h-5 text-drivee-500" /> Результат запроса
              </h3>
              <span class="text-xs text-gray-400">{{ store.currentResult.result.row_count }} строк</span>
            </div>
            <ChartRenderer
              :chart-type="store.currentResult.result.chart_type"
              :chart-data="store.currentResult.result.chart_data"
              :columns="store.currentResult.result.columns"
              :rows="store.currentResult.result.rows"
            />
          </div>

          <div
            v-else-if="!store.currentResult.is_fallback"
            class="card border-yellow-100 bg-yellow-50 text-center py-8"
          >
            <IconWarning class="w-8 h-8 text-yellow-500 mx-auto mb-2" />
            <p class="text-yellow-700 font-medium">Запрос заблокирован guardrail — данные не получены</p>
          </div>

          <button @click="store.clearResult()" class="btn-secondary w-full justify-center">
            <IconArrowRight class="w-4 h-4 rotate-180" /> Новый запрос
          </button>
        </div>
      </div>

      <!-- Query input -->
      <div class="sticky bottom-6 mt-auto" :class="{ 'pt-4': store.currentResult }">
        <div class="card p-4 shadow-lg border-drivee-100 bg-white/95 backdrop-blur">
          <form @submit.prevent="handleSubmit" class="flex gap-3">
            <input
              v-model="queryText"
              ref="inputRef"
              type="text"
              placeholder="Спросите о данных... например: «Топ-5 городов по выручке за неделю»"
              class="input-field flex-1 text-sm"
              :disabled="store.loading"
            />
            <button
              type="submit"
              class="btn-primary px-6 flex-shrink-0"
              :disabled="store.loading || !queryText.trim()"
            >
              <svg v-if="store.loading" class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
              </svg>
              <IconArrowRight v-else class="w-4 h-4" />
              {{ store.loading ? 'Думаю...' : 'Спросить' }}
            </button>
          </form>

          <div class="flex flex-wrap gap-2 mt-3">
            <span class="text-xs text-gray-400 self-center">Примеры:</span>
            <button
              v-for="ex in quickExamples"
              :key="ex"
              @click="fillTemplate(ex)"
              class="text-xs px-2.5 py-1 rounded-full bg-gray-100 text-gray-600 hover:bg-drivee-100 hover:text-drivee-700 transition-colors"
            >
              {{ ex }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Save Report Modal -->
    <div v-if="showSaveModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div class="bg-white rounded-2xl shadow-xl p-6 w-full max-w-md animate-slide-up">
        <h3 class="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
          <IconSave class="w-5 h-5 text-drivee-500" /> Сохранить отчёт
        </h3>
        <div class="space-y-3">
          <input v-model="reportTitle" type="text" placeholder="Название отчёта" class="input-field text-sm" />
          <select v-model="reportSchedule" class="input-field text-sm">
            <option value="">Без расписания</option>
            <option value="daily">Ежедневно</option>
            <option value="weekly_monday">Еженедельно (понедельник)</option>
            <option value="weekly_friday">Еженедельно (пятница)</option>
          </select>
          <label class="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
            <input v-model="reportPublic" type="checkbox" class="rounded" />
            Сделать отчёт публичным
          </label>
        </div>
        <div class="flex gap-3 mt-5">
          <button @click="showSaveModal = false" class="btn-secondary flex-1 justify-center">Отмена</button>
          <button @click="handleSaveReport" class="btn-primary flex-1 justify-center" :disabled="!reportTitle">Сохранить</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick, onBeforeUnmount } from 'vue'
import { useQueryStore } from '@/stores/query'
import { useApi } from '@/composables/useApi'
import ThinkingLog from '@/components/ThinkingLog.vue'
import GuardrailBadge from '@/components/GuardrailBadge.vue'
import ChartRenderer from '@/components/ChartRenderer.vue'
import IconSave from '@/components/icons/IconSave.vue'
import IconBrain from '@/components/icons/IconBrain.vue'
import IconX from '@/components/icons/IconX.vue'
import IconSearch from '@/components/icons/IconSearch.vue'
import IconCheck from '@/components/icons/IconCheck.vue'
import IconShield from '@/components/icons/IconShield.vue'
import IconChart from '@/components/icons/IconChart.vue'
import IconWarning from '@/components/icons/IconWarning.vue'
import IconArrowRight from '@/components/icons/IconArrowRight.vue'
import IconMap from '@/components/icons/IconMap.vue'
import IconCurrency from '@/components/icons/IconCurrency.vue'
import IconCar from '@/components/icons/IconCar.vue'
import IconStar from '@/components/icons/IconStar.vue'

const store = useQueryStore()
const { saveReport } = useApi()

const queryText = ref('')
const inputRef = ref(null)
const thinkingBottomRef = ref(null)
const copied = ref(false)
const showSaveModal = ref(false)
const reportTitle = ref('')
const reportSchedule = ref('')
const reportPublic = ref(false)
let autoScrollRaf = null

const quickExamples = ['Выручка по городам', 'Отмены за неделю', 'Топ водителей по рейтингу']

const categoryIconMap = {
  trips: IconChart,
  revenue: IconCurrency,
  drivers: IconCar,
  comparison: IconChart,
  cancellations: IconX,
}

function templateIcon(category) {
  return categoryIconMap[category] || IconChart
}

onMounted(() => {
  store.fetchTemplates()
  inputRef.value?.focus()
})

onBeforeUnmount(() => {
  if (autoScrollRaf) {
    cancelAnimationFrame(autoScrollRaf)
    autoScrollRaf = null
  }
})

function scheduleAutoScrollToThinking() {
  if (!store.loading) return
  if (autoScrollRaf) cancelAnimationFrame(autoScrollRaf)
  autoScrollRaf = requestAnimationFrame(async () => {
    await nextTick()
    if (thinkingBottomRef.value) {
      thinkingBottomRef.value.scrollIntoView({ behavior: 'smooth', block: 'end' })
    } else {
      window.scrollTo({ top: document.documentElement.scrollHeight, behavior: 'smooth' })
    }
  })
}

watch(
  () => store.thinkingPreview,
  () => {
    if (!store.thinkingPreview) return
    scheduleAutoScrollToThinking()
  }
)

watch(
  () => store.loading,
  (isLoading) => {
    if (isLoading) scheduleAutoScrollToThinking()
  }
)

async function handleSubmit() {
  if (!queryText.value.trim() || store.loading) return
  const q = queryText.value.trim()
  queryText.value = ''
  await store.executeQuery(q)
}

function fillTemplate(q) {
  queryText.value = q
  inputRef.value?.focus()
}

async function copySql() {
  if (!store.currentResult?.sql) return
  await navigator.clipboard.writeText(store.currentResult.sql)
  copied.value = true
  setTimeout(() => (copied.value = false), 2000)
}

async function handleSaveReport() {
  if (!reportTitle.value || !store.currentResult) return
  await saveReport({
    title: reportTitle.value,
    natural_query: store.currentResult.natural_query,
    sql_query: store.currentResult.sql,
    chart_type: store.currentResult.result?.chart_type || 'table',
    schedule: reportSchedule.value || null,
    is_public: reportPublic.value,
  })
  showSaveModal.value = false
  reportTitle.value = ''
}
</script>
