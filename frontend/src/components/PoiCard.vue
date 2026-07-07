<script setup>
import { ref } from 'vue'
import { api } from '../api/client'

const props = defineProps({
  poi: { type: Object, required: true },
  showSimilar: { type: Boolean, default: true },
})

const similar = ref(null)
const loadingSimilar = ref(false)

async function toggleSimilar() {
  if (similar.value !== null) {
    similar.value = null
    return
  }
  loadingSimilar.value = true
  try {
    similar.value = await api.similarPois(props.poi.id)
  } catch {
    similar.value = []
  } finally {
    loadingSimilar.value = false
  }
}
</script>

<template>
  <div class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
    <div class="flex items-start justify-between gap-3">
      <div class="min-w-0">
        <h3 class="font-semibold text-gray-900">
          <router-link :to="`/poi/${poi.id}`" class="hover:text-emerald-600">
            {{ poi.title }}
          </router-link>
        </h3>
        <p class="text-xs text-gray-500">
          {{ [poi.city, poi.country].filter(Boolean).join(', ') || '—' }}
        </p>
      </div>
      <div v-if="poi.rating_count" class="shrink-0 text-sm text-amber-600">
        ★ {{ poi.rating_avg.toFixed(1) }}
        <span class="text-gray-400">({{ poi.rating_count }})</span>
      </div>
    </div>

    <p v-if="poi.short_description || poi.description" class="mt-2 line-clamp-2 text-sm text-gray-600">
      {{ poi.short_description || poi.description }}
    </p>

    <div class="mt-3 flex flex-wrap items-center gap-2">
      <span
        v-for="cat in poi.categories"
        :key="cat"
        class="rounded-full bg-emerald-50 px-2 py-0.5 text-xs text-emerald-700"
      >
        {{ cat }}
      </span>
      <button
        v-if="showSimilar"
        class="ml-auto text-xs text-gray-400 hover:text-emerald-600"
        @click="toggleSimilar"
      >
        {{ similar === null ? (loadingSimilar ? '…' : 'Similar places') : 'Hide similar' }}
      </button>
    </div>

    <div v-if="similar !== null" class="mt-3 border-t border-gray-100 pt-3">
      <p v-if="!similar.length" class="text-xs text-gray-400">No similar places yet.</p>
      <ul v-else class="space-y-1">
        <li v-for="s in similar" :key="s.id" class="text-sm text-gray-700">
          <router-link :to="`/poi/${s.id}`" class="hover:text-emerald-600">
            <span class="font-medium">{{ s.title }}</span>
            <span v-if="s.city" class="text-gray-400"> · {{ s.city }}</span>
          </router-link>
        </li>
      </ul>
    </div>
  </div>
</template>
