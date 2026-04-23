<template>
  <div class="p-4 sm:p-6 lg:p-8 max-w-full overflow-x-hidden">
    <div class="mb-6 flex flex-wrap items-start justify-between gap-3">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Сохранённые отчёты</h1>
        <p class="text-sm text-gray-500 mt-1">Переиспользуйте запросы и настройте расписание</p>
      </div>
      <RouterLink to="/" class="btn-primary shrink-0">
        <IconPlus class="w-4 h-4" /> Новый запрос
      </RouterLink>
    </div>

    <div v-if="loading" class="flex justify-center py-16">
      <div class="w-8 h-8 border-4 border-drivee-200 border-t-drivee-500 rounded-full animate-spin"></div>
    </div>

    <div v-else-if="!reports.length" class="card text-center py-16">
      <IconChart class="w-12 h-12 text-gray-300 mx-auto mb-4" />
      <h3 class="text-lg font-semibold text-gray-700 mb-2">Нет сохранённых отчётов</h3>
      <p class="text-gray-500 text-sm mb-6">Выполните запрос и нажмите «Сохранить отчёт»</p>
      <RouterLink to="/" class="btn-primary">Перейти к запросам</RouterLink>
    </div>

    <div v-else class="grid grid-cols-1 gap-4">
      <div
        v-for="report in reports"
        :key="report.id"
        class="card group hover:border-drivee-200 transition-all duration-200"
      >
        <div class="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-3 mb-2 flex-wrap">
              <h3 class="font-semibold text-gray-800 break-words">{{ report.title }}</h3>
              <span v-if="report.is_public" class="badge-ok text-xs">публичный</span>
              <span v-if="report.schedule" class="badge-warn text-xs flex items-center gap-1">
                <IconClock class="w-3 h-3" /> {{ scheduleLabel(report.schedule) }}
              </span>
            </div>
            <p class="text-sm text-gray-500 mb-3 italic break-all">"{{ report.natural_query }}"</p>
            <div class="flex items-center gap-4 text-xs text-gray-400 flex-wrap">
              <span class="flex items-center gap-1">
                <IconChart class="w-3 h-3" /> {{ report.chart_type }}
              </span>
              <span class="flex items-center gap-1">
                <IconClock class="w-3 h-3" /> {{ formatDate(report.created_at) }}
              </span>
            </div>
          </div>
          <div class="flex gap-2 md:ml-4 shrink-0">
            <button
              @click="handleRun(report)"
              class="btn-primary text-sm py-1.5"
              :disabled="runningId === report.id"
            >
              <svg v-if="runningId === report.id" class="w-3.5 h-3.5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9"/>
              </svg>
              <IconPlay v-else class="w-3.5 h-3.5" />
              Запустить
            </button>
            <button
              @click="handleDelete(report.id)"
              class="btn-secondary text-sm py-1.5 hover:bg-red-50 hover:border-red-100 hover:text-red-500"
            >
              <IconTrash class="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        <div v-if="runResults[report.id]" class="mt-4 pt-4 border-t border-gray-100 animate-fade-in">
          <ChartRenderer
            :chart-type="runResults[report.id].result?.chart_type"
            :chart-data="runResults[report.id].result?.chart_data"
            :columns="runResults[report.id].result?.columns || []"
            :rows="runResults[report.id].result?.rows || []"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { useApi } from '@/composables/useApi'
import ChartRenderer from '@/components/ChartRenderer.vue'
import IconPlus from '@/components/icons/IconPlus.vue'
import IconChart from '@/components/icons/IconChart.vue'
import IconClock from '@/components/icons/IconClock.vue'
import IconPlay from '@/components/icons/IconPlay.vue'
import IconTrash from '@/components/icons/IconTrash.vue'
import dayjs from 'dayjs'
import 'dayjs/locale/ru'

dayjs.locale('ru')

const { getReports, deleteReport, runReport } = useApi()

const reports = ref([])
const loading = ref(false)
const runningId = ref(null)
const runResults = ref({})

onMounted(fetchReports)

async function fetchReports() {
  loading.value = true
  try { reports.value = await getReports() }
  finally { loading.value = false }
}

async function handleRun(report) {
  runningId.value = report.id
  try {
    runResults.value[report.id] = await runReport(report.id)
  } finally {
    runningId.value = null
  }
}

async function handleDelete(id) {
  await deleteReport(id)
  reports.value = reports.value.filter(r => r.id !== id)
}

function formatDate(dt) { return dayjs(dt).format('D MMM, HH:mm') }

function scheduleLabel(s) {
  return { daily: 'ежедневно', weekly_monday: 'пн', weekly_friday: 'пт' }[s] || s
}
</script>
