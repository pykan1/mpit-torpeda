<template>
  <div class="p-4 sm:p-6 lg:p-8 max-w-7xl">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Схема БД</h1>
      <p class="text-sm text-gray-500 mt-1">
        Таблицы и связи, доступные оператору для аналитических запросов.
      </p>
    </div>

    <div class="card mb-6 border-drivee-100 bg-drivee-50">
      <div class="flex items-start gap-3">
        <div class="w-8 h-8 rounded-lg bg-white flex items-center justify-center text-drivee-600">
          <IconDatabase class="w-5 h-5" />
        </div>
        <div>
          <p class="text-sm font-semibold text-drivee-800">Что есть в схеме</p>
          <p class="text-sm text-drivee-700 mt-1">
            `users`, `cities`, `drivers`, `trips`, `orders`, `saved_reports`, `query_logs`, `semantic_terms`.
          </p>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 xl:grid-cols-2 gap-4">
      <article
        v-for="table in tables"
        :key="table.name"
        class="card border-gray-100"
      >
        <div class="flex items-center justify-between mb-3">
          <h2 class="font-semibold text-gray-900">{{ table.name }}</h2>
          <span class="text-xs px-2 py-1 rounded-full bg-gray-100 text-gray-600">{{ table.kind }}</span>
        </div>
        <ul class="space-y-1.5">
          <li
            v-for="field in table.fields"
            :key="field"
            class="text-sm text-gray-700 font-mono"
          >
            {{ field }}
          </li>
        </ul>
      </article>
    </div>

    <div class="card mt-6">
      <h2 class="font-semibold text-gray-900 mb-3">Связи между таблицами</h2>
      <ul class="space-y-2 text-sm text-gray-700">
        <li v-for="relation in relations" :key="relation" class="font-mono">
          {{ relation }}
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import IconDatabase from '@/components/icons/IconDatabase.vue'

const tables = [
  {
    name: 'users',
    kind: 'core',
    fields: ['id (PK)', 'name', 'email (unique)', 'role', 'is_active', 'created_at'],
  },
  {
    name: 'cities',
    kind: 'dimension',
    fields: ['id (PK)', 'name (unique)', 'region', 'is_active', 'launch_date'],
  },
  {
    name: 'drivers',
    kind: 'fact',
    fields: ['id (PK)', 'full_name', 'city_id (FK)', 'rating', 'total_trips', 'car_model', 'car_class', 'is_active', 'joined_at'],
  },
  {
    name: 'trips',
    kind: 'fact',
    fields: ['id (PK)', 'driver_id (FK)', 'city_id (FK)', 'status', 'distance_km', 'duration_min', 'revenue', 'passenger_rating', 'started_at', 'ended_at', 'cancel_reason'],
  },
  {
    name: 'orders',
    kind: 'fact',
    fields: ['id (PK)', 'city_id (FK)', 'status', 'amount', 'channel', 'created_at', 'cancel_reason'],
  },
  {
    name: 'saved_reports',
    kind: 'service',
    fields: ['id (PK)', 'user_id (FK)', 'title', 'natural_query', 'sql_query', 'chart_type', 'schedule', 'is_public', 'created_at', 'last_run_at'],
  },
  {
    name: 'query_logs',
    kind: 'audit',
    fields: ['id (PK)', 'user_id (FK, nullable)', 'natural_query', 'interpretation', 'generated_sql', 'ai_thinking', 'confidence', 'guardrail_status', 'guardrail_violations', 'execution_success', 'row_count', 'execution_ms', 'created_at'],
  },
  {
    name: 'semantic_terms',
    kind: 'semantic',
    fields: ['id (PK)', 'term (unique)', 'aliases', 'sql_expression', 'description', 'category'],
  },
]

const relations = [
  'saved_reports.user_id -> users.id',
  'query_logs.user_id -> users.id',
  'drivers.city_id -> cities.id',
  'trips.driver_id -> drivers.id',
  'trips.city_id -> cities.id',
  'orders.city_id -> cities.id',
]
</script>
