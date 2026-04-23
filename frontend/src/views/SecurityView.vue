<template>
  <div class="p-8">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Управление безопасностью</h1>
      <p class="text-sm text-gray-500 mt-1">Ролевой доступ, guardrails и аудит запросов</p>
    </div>

    <div class="grid grid-cols-2 gap-6">
      <!-- Users & Roles -->
      <div class="card col-span-1">
        <h2 class="font-bold text-gray-800 mb-4 flex items-center gap-2">
          <IconUser class="w-5 h-5 text-drivee-500" /> Пользователи и роли
        </h2>

        <div v-if="loadingUsers" class="flex justify-center py-8">
          <div class="w-6 h-6 border-4 border-drivee-200 border-t-drivee-500 rounded-full animate-spin"></div>
        </div>

        <div v-else class="space-y-3">
          <div
            v-for="user in users"
            :key="user.id"
            class="flex items-center justify-between py-2 px-3 rounded-xl hover:bg-gray-50 transition-colors"
          >
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 rounded-full gradient-brand flex items-center justify-center text-white text-xs font-bold">
                {{ user.name.charAt(0) }}
              </div>
              <div>
                <p class="text-sm font-medium text-gray-800">{{ user.name }}</p>
                <p class="text-xs text-gray-400">{{ user.email }}</p>
              </div>
            </div>
            <select
              :value="user.role"
              @change="handleRoleChange(user.id, $event.target.value)"
              class="text-xs border border-gray-200 rounded-lg px-2 py-1 bg-white focus:outline-none focus:ring-2 focus:ring-drivee-400"
              :class="roleClass(user.role)"
            >
              <option v-for="role in roles" :key="role.value" :value="role.value">{{ role.label }}</option>
            </select>
          </div>
        </div>
      </div>

      <!-- SQL Validator -->
      <div class="card col-span-1">
        <h2 class="font-bold text-gray-800 mb-4 flex items-center gap-2">
          <IconSearch class="w-5 h-5 text-drivee-500" /> SQL Guardrail Tester
        </h2>
        <textarea
          v-model="sqlToTest"
          class="input-field text-sm font-mono h-28 resize-none"
          placeholder="Введите SQL для проверки..."
        ></textarea>
        <button @click="testSql" class="btn-primary mt-3 text-sm" :disabled="!sqlToTest.trim() || testingSQL">
          Проверить безопасность
        </button>
        <div v-if="validationResult" class="mt-4 animate-fade-in">
          <GuardrailBadge :guardrail="validationResult" />
        </div>
      </div>

      <!-- Guardrail Rules -->
      <div class="card col-span-2">
        <h2 class="font-bold text-gray-800 mb-4 flex items-center gap-2">
          <IconShield class="w-5 h-5 text-drivee-500" /> Активные правила Guardrail
        </h2>
        <div class="grid grid-cols-2 gap-4">
          <div v-for="rule in guardrailRules" :key="rule.title" class="p-4 rounded-xl border" :class="rule.color">
            <div class="flex items-start gap-3">
              <component :is="rule.icon" class="w-5 h-5 flex-shrink-0 mt-0.5" :class="rule.iconColor" />
              <div>
                <h3 class="font-semibold text-sm mb-1">{{ rule.title }}</h3>
                <p class="text-xs text-gray-600 leading-relaxed">{{ rule.description }}</p>
                <div v-if="rule.items" class="mt-2 flex flex-wrap gap-1">
                  <code
                    v-for="item in rule.items"
                    :key="item"
                    class="text-xs px-1.5 py-0.5 bg-white rounded font-mono border"
                  >{{ item }}</code>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Stats -->
      <div v-if="stats" class="card col-span-2">
        <h2 class="font-bold text-gray-800 mb-4 flex items-center gap-2">
          <IconChart class="w-5 h-5 text-drivee-500" /> Статистика платформы
        </h2>
        <div class="grid grid-cols-4 gap-4">
          <div class="text-center p-4 rounded-xl bg-drivee-50">
            <div class="text-2xl font-bold text-drivee-700">{{ stats.total_drivers }}</div>
            <div class="text-xs text-gray-500 mt-1">Водителей</div>
          </div>
          <div class="text-center p-4 rounded-xl bg-blue-50">
            <div class="text-2xl font-bold text-blue-700">{{ stats.total_trips }}</div>
            <div class="text-xs text-gray-500 mt-1">Поездок</div>
          </div>
          <div class="text-center p-4 rounded-xl bg-purple-50">
            <div class="text-2xl font-bold text-purple-700">{{ formatRevenue(stats.total_revenue) }}</div>
            <div class="text-xs text-gray-500 mt-1">Выручка</div>
          </div>
          <div class="text-center p-4 rounded-xl bg-orange-50">
            <div class="text-2xl font-bold text-orange-700">{{ stats.blocked_queries }}</div>
            <div class="text-xs text-gray-500 mt-1">Заблокировано</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useApi } from '@/composables/useApi'
import GuardrailBadge from '@/components/GuardrailBadge.vue'
import IconUser from '@/components/icons/IconUser.vue'
import IconSearch from '@/components/icons/IconSearch.vue'
import IconShield from '@/components/icons/IconShield.vue'
import IconChart from '@/components/icons/IconChart.vue'
import IconBan from '@/components/icons/IconBan.vue'
import IconLock from '@/components/icons/IconLock.vue'
import IconBookOpen from '@/components/icons/IconBookOpen.vue'
import IconBolt from '@/components/icons/IconBolt.vue'

const { getUsers, updateUserRole, validateSql, getStats } = useApi()

const users = ref([])
const loadingUsers = ref(false)
const sqlToTest = ref('')
const testingSQL = ref(false)
const validationResult = ref(null)
const stats = ref(null)

const roles = [
  { value: 'admin',   label: 'Admin' },
  { value: 'analyst', label: 'Analyst' },
  { value: 'manager', label: 'Manager' },
  { value: 'viewer',  label: 'Viewer' },
]

const guardrailRules = [
  {
    title: 'Блокировка опасных команд',
    description: 'Запрещены любые мутирующие SQL-операторы — только чтение данных',
    icon: IconBan,
    iconColor: 'text-red-500',
    color: 'border-red-100 bg-red-50',
    items: ['DROP', 'DELETE', 'TRUNCATE', 'UPDATE', 'INSERT', 'ALTER'],
  },
  {
    title: 'Защита персональных данных',
    description: 'Блокируется доступ к столбцам с чувствительными данными',
    icon: IconLock,
    iconColor: 'text-orange-500',
    color: 'border-orange-100 bg-orange-50',
    items: ['password', 'token', 'secret', 'phone', 'email'],
  },
  {
    title: 'Только SELECT',
    description: 'Система выполняет исключительно запросы на чтение — запись невозможна',
    icon: IconBookOpen,
    iconColor: 'text-blue-500',
    color: 'border-blue-100 bg-blue-50',
    items: null,
  },
  {
    title: 'Лимиты запросов',
    description: 'Максимальная длина SQL 5000 символов, предупреждение при отсутствии LIMIT',
    icon: IconBolt,
    iconColor: 'text-yellow-500',
    color: 'border-yellow-100 bg-yellow-50',
    items: ['MAX 5000 chars', 'LIMIT recommended'],
  },
]

onMounted(async () => {
  loadingUsers.value = true
  try {
    ;[users.value, stats.value] = await Promise.all([getUsers(), getStats()])
  } finally {
    loadingUsers.value = false
  }
})

async function handleRoleChange(userId, role) {
  await updateUserRole(userId, role)
  const user = users.value.find(u => u.id === userId)
  if (user) user.role = role
}

async function testSql() {
  testingSQL.value = true
  try {
    validationResult.value = await validateSql(sqlToTest.value)
  } finally {
    testingSQL.value = false
  }
}

function roleClass(role) {
  if (role === 'admin')   return 'text-red-600 border-red-200'
  if (role === 'analyst') return 'text-yellow-600 border-yellow-200'
  if (role === 'manager') return 'text-drivee-600 border-drivee-200'
  return 'text-gray-500 border-gray-200'
}

function formatRevenue(v) {
  if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}M ₽`
  if (v >= 1000)      return `${Math.round(v / 1000)}K ₽`
  return `${Math.round(v)} ₽`
}
</script>
