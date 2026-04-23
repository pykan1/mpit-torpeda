<template>
  <div class="p-8">
    <div class="mb-6 flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Словарь бизнес-терминов</h1>
        <p class="text-sm text-gray-500 mt-1">Семантический слой — как ИИ понимает ваш бизнес-язык</p>
      </div>
      <button @click="showAddForm = !showAddForm" class="btn-primary">
        <IconPlus class="w-4 h-4" /> Добавить термин
      </button>
    </div>

    <!-- Add form -->
    <div v-if="showAddForm" class="card mb-6 border-drivee-200 animate-slide-up">
      <h3 class="font-bold text-gray-800 mb-4">Новый бизнес-термин</h3>
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="text-xs font-semibold text-gray-500 mb-1 block">Термин *</label>
          <input v-model="newTerm.term" type="text" placeholder="выручка" class="input-field text-sm" />
        </div>
        <div>
          <label class="text-xs font-semibold text-gray-500 mb-1 block">Категория</label>
          <select v-model="newTerm.category" class="input-field text-sm">
            <option value="metric">Метрика</option>
            <option value="dimension">Измерение</option>
            <option value="filter">Фильтр</option>
            <option value="alias">Псевдоним</option>
          </select>
        </div>
        <div>
          <label class="text-xs font-semibold text-gray-500 mb-1 block">Псевдонимы (через запятую)</label>
          <input v-model="aliasesInput" type="text" placeholder="доход, revenue, деньги" class="input-field text-sm" />
        </div>
        <div>
          <label class="text-xs font-semibold text-gray-500 mb-1 block">SQL-выражение *</label>
          <input v-model="newTerm.sql_expression" type="text" placeholder="SUM(trips.revenue)" class="input-field text-sm font-mono" />
        </div>
        <div class="col-span-2">
          <label class="text-xs font-semibold text-gray-500 mb-1 block">Описание</label>
          <input v-model="newTerm.description" type="text" placeholder="Описание термина для аналитиков" class="input-field text-sm" />
        </div>
      </div>
      <div class="flex gap-3 mt-4">
        <button @click="showAddForm = false" class="btn-secondary">Отмена</button>
        <button @click="handleCreate" class="btn-primary" :disabled="!newTerm.term || !newTerm.sql_expression">Добавить</button>
      </div>
    </div>

    <div v-if="loading" class="flex justify-center py-16">
      <div class="w-8 h-8 border-4 border-drivee-200 border-t-drivee-500 rounded-full animate-spin"></div>
    </div>

    <div v-else>
      <div v-for="(group, cat) in groupedTerms" :key="cat" class="mb-6">
        <h2 class="text-sm font-bold text-gray-500 uppercase tracking-wide mb-3 flex items-center gap-2">
          <component :is="categoryIcon(cat)" class="w-4 h-4" />
          {{ categoryLabel(cat) }}
          <span class="ml-auto text-xs font-normal bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">{{ group.length }}</span>
        </h2>
        <div class="grid grid-cols-2 gap-3">
          <div
            v-for="term in group"
            :key="term.id"
            class="card hover:border-drivee-200 transition-all duration-200"
          >
            <div class="flex items-start justify-between mb-2">
              <h3 class="font-bold text-gray-900">{{ term.term }}</h3>
              <span class="text-xs px-2 py-0.5 rounded-full" :class="categoryBadge(term.category)">
                {{ categoryLabel(term.category) }}
              </span>
            </div>
            <p v-if="term.description" class="text-sm text-gray-500 mb-3">{{ term.description }}</p>
            <div class="sql-block text-xs py-2 px-3">{{ term.sql_expression }}</div>
            <div v-if="term.aliases?.length" class="mt-2 flex flex-wrap gap-1">
              <span
                v-for="alias in term.aliases"
                :key="alias"
                class="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded-full"
              >{{ alias }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useApi } from '@/composables/useApi'
import IconPlus from '@/components/icons/IconPlus.vue'
import IconChart from '@/components/icons/IconChart.vue'
import IconDatabase from '@/components/icons/IconDatabase.vue'
import IconFilter from '@/components/icons/IconFilter.vue'
import IconTag from '@/components/icons/IconTag.vue'

const { getSemanticTerms, createSemanticTerm } = useApi()

const terms = ref([])
const loading = ref(false)
const showAddForm = ref(false)
const aliasesInput = ref('')
const newTerm = ref({ term: '', sql_expression: '', description: '', category: 'metric' })

const groupedTerms = computed(() => {
  const groups = {}
  for (const t of terms.value) {
    if (!groups[t.category]) groups[t.category] = []
    groups[t.category].push(t)
  }
  return groups
})

onMounted(async () => {
  loading.value = true
  try { terms.value = await getSemanticTerms() }
  finally { loading.value = false }
})

async function handleCreate() {
  const aliases = aliasesInput.value.split(',').map(a => a.trim()).filter(Boolean)
  const created = await createSemanticTerm({ ...newTerm.value, aliases })
  terms.value.push(created)
  newTerm.value = { term: '', sql_expression: '', description: '', category: 'metric' }
  aliasesInput.value = ''
  showAddForm.value = false
}

function categoryLabel(cat) {
  return { metric: 'Метрика', dimension: 'Измерение', filter: 'Фильтр', alias: 'Псевдоним' }[cat] || cat
}

function categoryIcon(cat) {
  return { metric: IconChart, dimension: IconDatabase, filter: IconFilter, alias: IconTag }[cat] || IconChart
}

function categoryBadge(cat) {
  return {
    metric:    'bg-drivee-100 text-drivee-700',
    dimension: 'bg-blue-100 text-blue-700',
    filter:    'bg-purple-100 text-purple-700',
    alias:     'bg-orange-100 text-orange-700',
  }[cat] || 'bg-gray-100 text-gray-600'
}
</script>
