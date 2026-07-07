import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'home', component: () => import('../pages/HomeView.vue') },
  { path: '/map', name: 'map', component: () => import('../pages/MapView.vue') },
  { path: '/search', name: 'search', component: () => import('../pages/SearchView.vue') },
  {
    path: '/feed',
    name: 'feed',
    component: () => import('../pages/FeedView.vue'),
    meta: { auth: true },
  },
  { path: '/u/:username', name: 'profile', component: () => import('../pages/ProfileView.vue') },
  { path: '/poi/:id', name: 'poi', component: () => import('../pages/PoiDetailView.vue') },
  { path: '/login', name: 'login', component: () => import('../pages/LoginView.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  if (to.meta.auth && !localStorage.getItem('rh_token')) {
    return { name: 'login', query: { next: to.fullPath } }
  }
})

export default router
