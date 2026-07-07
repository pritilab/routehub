<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api/client'

const routes = ref([])
const error = ref(null)

onMounted(async () => {
  try {
    routes.value = await api.listRoutes()
  } catch (e) {
    error.value = e.message
  }
})
</script>

<template>
  <div class="mx-auto max-w-4xl px-6 py-10">
    <h1 class="text-3xl font-bold text-gray-900">Discover routes</h1>
    <p class="mt-2 text-gray-600">
      Curated and community walks, rides and city explorations.
    </p>

    <p v-if="error" class="mt-6 rounded-md bg-red-50 p-3 text-sm text-red-700">{{ error }}</p>

    <div v-else-if="routes.length" class="mt-8 grid gap-4 sm:grid-cols-2">
      <div
        v-for="route in routes"
        :key="route.id"
        class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm"
      >
        <h2 class="font-semibold text-gray-900">{{ route.title }}</h2>
        <p class="mt-1 line-clamp-2 text-sm text-gray-600">{{ route.description }}</p>
        <div class="mt-3 flex gap-3 text-xs text-gray-500">
          <span>{{ (route.total_distance_meters / 1000).toFixed(1) }} km</span>
          <span>~{{ route.estimated_duration_minutes }} min</span>
          <span class="capitalize">{{ route.transport_mode }}</span>
        </div>
      </div>
    </div>

    <p v-else class="mt-8 text-gray-500">
      No public routes yet — be the first:
      <router-link to="/map" class="text-emerald-600 hover:underline">open the map</router-link>.
    </p>
  </div>
</template>
