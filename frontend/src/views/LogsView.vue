<template>
  <div class="p-8">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Логи ИИ</h1>
      <p class="text-sm text-gray-500 mt-1">История запросов с размышлениями модели</p>
    </div>

    <!-- Stats row -->
    <div v-if="stats" class="grid grid-cols-4 gap-4 mb-6">
      <div class="card text-center">
        <div class="text-2xl font-bold text-gray-900">{{ stats.total_queries }}</div>
        <div class="text-xs text-gray-500 mt-1">Всего запросов</div>
      </div>
      <div class="card text-center">
        <div class="text-2xl font-bold text-drivee-600">{{ stats.successful_queries }}</div>
        <div class="text-xs text-gray-500 mt-1">Успешных</div>
      </div>
      <div class="card text-center">
        <div class="text-2xl font-bold text-red-500">{{ stats.blocked_queries }}</div>
        <div class="text-xs text-gray-500 mt-1">Заблокировано</div>
      </div>
      <div class="card text-center">
        <div class="text-2xl font-bold text-purple-600">{{ stats.total_reports }}</div>
        <div class="text-xs text-gray-500 mt-1">Отчётов</div>
      </div>
    </div>

    <div v-if="loading" class="flex justify-center py-16">
      <div class="w-8 h-8 border-4 border-drivee-200 border-t-drivee-500 rounded-full animate-spin"></div>
    </div>

    <div v-else class="space-y-3">
      <div
        v-for="log in logs"
        :key="log.id"
        class="card cursor-pointer hover:border-drivee-200 transition-all"
        @click="toggleLog(log.id)"
      >
        <!-- Header row -->
        <div class="flex items-start gap-3">
          <div class="flex-shrink-0 mt-0.5">
            <IconBan v-if="log.guardrail_status === 'blocked'" class="w-5 h-5 text-red-500" />
            <IconX v-else-if="!log.execution_success" class="w-5 h-5 text-red-400" />
            <IconCheck v-else class="w-5 h-5 text-drivee-500" />
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 flex-wrap">
              <p class="font-medium text-gray-800 truncate">"{{ log.natural_query }}"</p>
              <span :class="guardBadgeClass(log.guardrail_status)" class="text-xs px-2 py-0.5 rounded-full font-mono flex-shrink-0">
                {{ log.guardrail_status }}
              </span>
            </div>
            <div class="flex items-center gap-4 mt-1 text-xs text-gray-400">
              <span>{{ formatDate(log.created_at) }}</span>
              <span>{{ log.row_count }} строк</span>
              <span>{{ log.execution_ms }}ms</span>
              <span>уверенность {{ Math.round(log.confidence * 100) }}%</span>
            </div>
          </div>
          <IconChevronUp v-if="expandedLogs.has(log.id)" class="w-4 h-4 text-gray-300 flex-shrink-0" />
          <IconChevronDown v-else class="w-4 h-4 text-gray-300 flex-shrink-0" />
        </div>

        <!-- Expanded details -->
        <div v-if="expandedLogs.has(log.id)" class="mt-4 space-y-3 animate-fade-in">
          <div v-if="log.interpretation" class="p-3 rounded-xl bg-drivee-50 border border-drivee-100">
            <p class="text-xs font-semibold text-drivee-700 mb-1 flex items-center gap-1">
              <IconBrain class="w-3.5 h-3.5" /> Интерпретация
            </p>
            <p class="text-sm text-gray-700">{{ log.interpretation }}</p>
          </div>

          <div v-if="log.ai_thinking" class="thinking-panel">
            <div class="flex items-center gap-2 mb-2 pb-2 border-b border-yellow-200">
              <IconBrain class="w-4 h-4 text-yellow-600" />
              <span class="text-yellow-700 font-semibold text-xs uppercase tracking-wide">Размышления ИИ</span>
            </div>
            <div class="text-gray-700">{{ log.ai_thinking }}</div>
          </div>

          <div v-if="log.generated_sql">
            <p class="text-xs font-semibold text-gray-500 mb-1 flex items-center gap-1">
              <IconSearch class="w-3.5 h-3.5" /> SQL
            </p>
            <div class="sql-block text-xs">{{ log.generated_sql }}</div>
          </div>

          <div v-if="log.guardrail_violations?.length" class="p-3 rounded-xl bg-red-50 border border-red-100">
            <p class="text-xs font-semibold text-red-700 mb-1 flex items-center gap-1">
              <IconShield class="w-3.5 h-3.5" /> Нарушения guardrail
            </p>
            <ul class="space-y-0.5">
              <li v-for="v in log.guardrail_violations" :key="v" class="text-xs text-red-600">• {{ v }}</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useApi } from '@/composables/useApi'
import IconCheck from '@/components/icons/IconCheck.vue'
import IconX from '@/components/icons/IconX.vue'
import IconBan from '@/components/icons/IconBan.vue'
import IconBrain from '@/components/icons/IconBrain.vue'
import IconSearch from '@/components/icons/IconSearch.vue'
import IconShield from '@/components/icons/IconShield.vue'
import IconChevronUp from '@/components/icons/IconChevronUp.vue'
import IconChevronDown from '@/components/icons/IconChevronDown.vue'
import dayjs from 'dayjs'

const { getLogs, getStats } = useApi()

const logs = ref([])
const stats = ref(null)
const loading = ref(false)
const expandedLogs = ref(new Set())

onMounted(async () => {
  loading.value = true
  try {
    ;[logs.value, stats.value] = await Promise.all([getLogs(100), getStats()])
  } finally {
    loading.value = false
  }
})

function toggleLog(id) {
  if (expandedLogs.value.has(id)) {
    expandedLogs.value.delete(id)
  } else {
    expandedLogs.value.add(id)
  }
}

function guardBadgeClass(status) {
  if (status === 'blocked') return 'bg-red-100 text-red-600'
  if (status === 'warning') return 'bg-yellow-100 text-yellow-600'
  return 'bg-drivee-100 text-drivee-600'
}

function formatDate(dt) {
  return dayjs(dt).format('D MMM HH:mm')
}
</script>
