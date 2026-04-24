<template>
  <div class="w-full">
    <!-- Chart type selector -->
    <div class="flex items-center gap-2 mb-4 flex-wrap">
      <span class="text-sm font-medium text-gray-500">Тип визуализации:</span>
      <div class="flex gap-1 flex-wrap">
        <button
          v-for="type in availableTypes"
          :key="type.value"
          @click="selectedType = type.value"
          class="px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200"
          :class="selectedType === type.value
            ? 'bg-drivee-500 text-white shadow-sm'
            : 'bg-gray-100 text-gray-600 hover:bg-drivee-50 hover:text-drivee-600'"
        >
          {{ type.label }}
        </button>
      </div>
    </div>

    <!-- KPI Card -->
    <div v-if="selectedType === 'kpi'" class="flex justify-center py-8">
      <div class="text-center">
        <div class="text-5xl font-bold text-gradient mb-2">
          {{ formatValue(chartData.value) }}
        </div>
        <div class="text-gray-500 text-sm">{{ chartData.label }}</div>
      </div>
    </div>

    <!-- Chart -->
    <div v-else-if="selectedType !== 'table'" class="relative">
      <canvas ref="chartCanvas" class="max-h-80"></canvas>
    </div>

    <!-- Table -->
    <div v-if="selectedType === 'table' || showTable" class="overflow-x-auto mt-4">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-gray-200">
            <th
              v-for="col in columns"
              :key="col"
              class="px-3 py-2 text-left font-semibold text-gray-600 text-xs uppercase tracking-wide"
            >
              {{ col.replace(/_/g, ' ') }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(row, i) in rows"
            :key="i"
            class="border-b border-gray-50 hover:bg-drivee-50 transition-colors"
          >
            <td v-for="(cell, j) in row" :key="j" class="px-3 py-2 text-gray-700">
              {{ formatCell(cell, columns[j]) }}
            </td>
          </tr>
        </tbody>
      </table>
      <div class="mt-2 text-xs text-gray-400 text-right">{{ rows.length }} строк</div>
    </div>

    <!-- Toggle table button -->
    <button
      v-if="selectedType !== 'table'"
      @click="showTable = !showTable"
      class="mt-3 text-xs text-drivee-600 hover:text-drivee-700 font-medium flex items-center gap-1 transition-colors"
    >
      <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M3 14h18M10 3v18M14 3v18"/>
      </svg>
      {{ showTable ? 'Скрыть таблицу' : 'Показать как таблицу' }}
    </button>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, computed, nextTick } from 'vue'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

const props = defineProps({
  chartType: { type: String, default: 'bar' },
  chartData: { type: Object, default: () => ({}) },
  columns: { type: Array, default: () => [] },
  rows: { type: Array, default: () => [] },
})

const chartCanvas = ref(null)
const selectedType = ref(props.chartType)
const showTable = ref(false)
let chartInstance = null

const availableTypes = computed(() => {
  const isTableOnly = props.chartType === 'table' || !props.chartData || Object.keys(props.chartData).length === 0
  if (isTableOnly) {
    return [{ value: 'table', label: '📋 Таблица' }]
  }

  const types = [
    { value: 'bar', label: '📊 Столбцы' },
    { value: 'line', label: '📈 График' },
    { value: 'pie', label: '🥧 Круговая' },
    { value: 'doughnut', label: '🍩 Кольцо' },
    { value: 'table', label: '📋 Таблица' },
  ]
  if (props.chartData?.value !== undefined) {
    types.unshift({ value: 'kpi', label: '🎯 KPI' })
  }
  return types
})

function formatValue(val) {
  if (typeof val === 'number') {
    return val >= 1000 ? val.toLocaleString('ru-RU') : val
  }
  return val
}

function formatCell(cell, col) {
  if (cell === null || cell === undefined) return '—'
  const colLower = col?.toLowerCase() || ''
  if (typeof cell === 'number') {
    if (
      colLower.includes('revenue') ||
      colLower.includes('amount') ||
      colLower.includes('price') ||
      colLower.includes('выручка') ||
      colLower.includes('стоим')
    ) {
      return `${cell.toLocaleString('ru-RU')} ₽`
    }
    if (colLower.includes('rating') || colLower.includes('рейтинг')) {
      return `⭐ ${cell.toFixed(1)}`
    }
    return cell.toLocaleString('ru-RU')
  }
  return String(cell)
}

function destroyChart() {
  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }
}

function normalizeDataForType(chartType, rawData) {
  if (!rawData || typeof rawData !== 'object') return rawData
  const cloned = {
    ...rawData,
    datasets: Array.isArray(rawData.datasets)
      ? rawData.datasets.map((dataset) => ({ ...dataset }))
      : rawData.datasets,
  }
  if (!Array.isArray(cloned.datasets)) return cloned

  if (chartType === 'line') {
    cloned.datasets = cloned.datasets.map((dataset, index) => {
      const next = { ...dataset }
      const fallbackColor = ['#27AE60', '#2ECC71', '#1A7A42'][index % 3]

      next.showLine = true
      next.borderWidth = Number.isFinite(next.borderWidth) ? next.borderWidth : 2
      next.tension = Number.isFinite(next.tension) ? next.tension : 0.35
      next.pointRadius = Number.isFinite(next.pointRadius) ? next.pointRadius : 3
      next.pointHoverRadius = Number.isFinite(next.pointHoverRadius) ? next.pointHoverRadius : 5

      if (!next.borderColor || next.borderColor === '#ffffff' || Array.isArray(next.borderColor)) {
        next.borderColor = fallbackColor
      }
      if (Array.isArray(next.backgroundColor)) {
        next.backgroundColor = `${fallbackColor}33`
      }

      return next
    })
  }

  return cloned
}

async function renderChart() {
  destroyChart()
  await nextTick()

  if (!chartCanvas.value || selectedType.value === 'table' || selectedType.value === 'kpi') return
  if (!props.chartData?.datasets?.length && !props.chartData?.data?.length) return
  let normalizedData = props.chartData
  try {
    normalizedData = normalizeDataForType(selectedType.value, props.chartData)
  } catch {
    normalizedData = props.chartData
  }

  const config = {
    type: selectedType.value,
    data: normalizedData,
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          display: ['pie', 'doughnut'].includes(selectedType.value),
          position: 'bottom',
          labels: { font: { family: 'Inter', size: 12 }, padding: 16 },
        },
        tooltip: {
          backgroundColor: '#0D1117',
          titleColor: '#ffffff',
          bodyColor: '#9ca3af',
          borderColor: '#2ECC71',
          borderWidth: 1,
          padding: 12,
          cornerRadius: 8,
          callbacks: {
            label: (ctx) => {
              const val = ctx.parsed?.y ?? ctx.parsed
              return typeof val === 'number'
                ? ` ${val.toLocaleString('ru-RU')}`
                : ` ${val}`
            },
          },
        },
      },
      scales: ['bar', 'line'].includes(selectedType.value)
        ? {
            x: {
              grid: { display: false },
              ticks: { font: { family: 'Inter', size: 11 }, color: '#6b7280' },
            },
            y: {
              grid: { color: '#f3f4f6', borderDash: [4, 4] },
              ticks: {
                font: { family: 'Inter', size: 11 },
                color: '#6b7280',
                callback: (v) => v.toLocaleString('ru-RU'),
              },
            },
          }
        : undefined,
    },
  }

  chartInstance = new Chart(chartCanvas.value, config)
}

watch(() => selectedType.value, renderChart)
watch(() => props.chartData, renderChart, { deep: true })
watch(
  () => props.chartType,
  (nextType) => {
    selectedType.value = nextType || 'table'
  }
)

onMounted(renderChart)
onUnmounted(destroyChart)
</script>
