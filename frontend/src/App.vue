<template>
  <div class="min-h-screen bg-drivee-50 flex">
    <!-- Sidebar -->
    <aside class="w-64 min-h-screen bg-white border-r border-gray-100 flex flex-col shadow-sm fixed left-0 top-0 bottom-0 z-20">
      <!-- Logo -->
      <div class="p-6 border-b border-gray-100">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl gradient-brand flex items-center justify-center text-white font-bold text-lg shadow-sm">
            D
          </div>
          <div>
            <div class="font-bold text-gray-900 text-lg leading-none">Driveery</div>
            <div class="text-xs text-drivee-600 font-medium mt-0.5">AI Analytics</div>
          </div>
        </div>
      </div>

      <!-- Navigation -->
      <nav class="flex-1 p-4 space-y-1">
        <RouterLink to="/" class="nav-link" :class="{ active: $route.path === '/' }">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/>
          </svg>
          Запросы
        </RouterLink>

        <RouterLink to="/reports" class="nav-link" :class="{ active: $route.path === '/reports' }">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
          </svg>
          Отчёты
        </RouterLink>

        <RouterLink to="/logs" class="nav-link" :class="{ active: $route.path === '/logs' }">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
          </svg>
          Логи ИИ
        </RouterLink>

        <RouterLink to="/semantic" class="nav-link" :class="{ active: $route.path === '/semantic' }">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
          </svg>
          Словарь терминов
        </RouterLink>

        <RouterLink to="/schema" class="nav-link" :class="{ active: $route.path === '/schema' }">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7h16M4 12h16M4 17h16M7 4v16M17 4v16"/>
          </svg>
          Схема
        </RouterLink>

        <RouterLink to="/security" class="nav-link" :class="{ active: $route.path === '/security' }">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
          </svg>
          Безопасность
        </RouterLink>
      </nav>

      <!-- Bottom brand info -->
      <div class="p-4 border-t border-gray-100">
        <div class="flex items-center gap-2 px-3 py-2 bg-drivee-50 rounded-xl">
          <div class="w-2 h-2 rounded-full bg-drivee-500 animate-pulse"></div>
          <span class="text-xs text-drivee-700 font-medium">AI Online</span>
          <span class="ml-auto text-xs text-gray-400">qwen3</span>
        </div>
      </div>
    </aside>

    <!-- Main content -->
    <main class="flex-1 ml-64 min-h-screen">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import { RouterLink, RouterView } from 'vue-router'
</script>
