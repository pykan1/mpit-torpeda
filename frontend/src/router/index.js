import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/HomeView.vue'),
    },
    {
      path: '/reports',
      name: 'reports',
      component: () => import('@/views/ReportsView.vue'),
    },
    {
      path: '/security',
      name: 'security',
      component: () => import('@/views/SecurityView.vue'),
    },
    {
      path: '/logs',
      name: 'logs',
      component: () => import('@/views/LogsView.vue'),
    },
    {
      path: '/semantic',
      name: 'semantic',
      component: () => import('@/views/SemanticView.vue'),
    },
    {
      path: '/schema',
      name: 'schema',
      component: () => import('@/views/SchemaView.vue'),
    },
  ],
})

export default router
