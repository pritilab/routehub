<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api/client'
import { useAuthStore } from '../stores/auth'
import { timeAgo } from '../utils/time'

const auth = useAuthStore()
const items = ref([])
const busy = ref(true)
const error = ref(null)
const PAGE = 20
const offset = ref(0)
const exhausted = ref(false)

async function load() {
  busy.value = true
  try {
    const page = await api.feed(auth.token, { limit: PAGE, offset: offset.value })
    items.value.push(...page)
    offset.value += page.length
    exhausted.value = page.length < PAGE
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="mx-auto max-w-2xl px-6 py-8">
    <h1 class="text-2xl font-bold text-gray-900">Your feed</h1>

    <p v-if="error" class="mt-4 rounded-md bg-red-50 p-3 text-sm text-red-700">{{ error }}</p>

    <div class="mt-6 space-y-3">
      <div
        v-for="(item, i) in items"
        :key="i"
        class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm"
      >
        <div class="flex items-baseline justify-between gap-2">
          <router-link
            :to="`/u/${item.actor.username}`"
            class="font-medium text-gray-900 hover:text-emerald-600"
          >
            {{ item.actor.display_name || item.actor.username }}
          </router-link>
          <span class="shrink-0 text-xs text-gray-400">{{ timeAgo(item.created_at) }}</span>
        </div>

        <p class="mt-1 text-sm text-gray-700">
          <template v-if="item.type === 'checkin'">
            📍 checked in at <span class="font-medium">{{ item.poi.title }}</span>
            <span v-if="item.comment" class="text-gray-500"> — “{{ item.comment }}”</span>
          </template>
          <template v-else-if="item.type === 'review'">
            <span class="text-amber-600">{{ '★'.repeat(item.rating) }}</span>
            reviewed <span class="font-medium">{{ item.poi.title }}</span>
            <span v-if="item.text" class="text-gray-500"> — “{{ item.text }}”</span>
          </template>
          <template v-else-if="item.type === 'route_published'">
            🗺️ published route <span class="font-medium">{{ item.route.title }}</span>
            <span class="text-gray-500">
              ({{ (item.route.total_distance_meters / 1000).toFixed(1) }} km,
              ~{{ item.route.estimated_duration_minutes }} min,
              {{ item.route.transport_mode }})
            </span>
          </template>
        </p>
      </div>
    </div>

    <p v-if="!busy && !items.length && !error" class="mt-8 text-center text-gray-400">
      Nothing here yet — follow people to see their check-ins, reviews and routes.
    </p>

    <button
      v-if="items.length && !exhausted"
      :disabled="busy"
      class="mt-6 w-full rounded-md border border-gray-300 py-2 text-sm text-gray-600 hover:bg-gray-50 disabled:opacity-50"
      @click="load"
    >
      Load more
    </button>
  </div>
</template>
