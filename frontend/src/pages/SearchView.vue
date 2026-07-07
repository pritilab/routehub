<script setup>
import { ref, watch } from 'vue'
import { api } from '../api/client'
import PoiCard from '../components/PoiCard.vue'

const query = ref('')
const results = ref([])
const busy = ref(false)
const error = ref(null)
const searched = ref(false)
let debounceTimer = null

async function runSearch() {
  const q = query.value.trim()
  if (!q) {
    results.value = []
    searched.value = false
    return
  }
  busy.value = true
  error.value = null
  try {
    results.value = await api.hybridSearch(q)
    searched.value = true
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}

watch(query, () => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(runSearch, 350)
})
</script>

<template>
  <div class="mx-auto max-w-3xl px-6 py-8">
    <h1 class="text-2xl font-bold text-gray-900">Find places</h1>
    <p class="mt-1 text-sm text-gray-500">
      Hybrid search: keywords + meaning. Try “quiet coffee for working” or “medieval history”.
    </p>

    <div class="relative mt-4">
      <input
        v-model="query"
        type="search"
        placeholder="Search places…"
        autofocus
        class="w-full rounded-lg border border-gray-300 px-4 py-3 text-lg shadow-sm focus:border-emerald-500 focus:outline-none"
        @keyup.enter="runSearch"
      />
      <span v-if="busy" class="absolute right-4 top-3.5 text-sm text-gray-400">…</span>
    </div>

    <p v-if="error" class="mt-4 rounded-md bg-red-50 p-3 text-sm text-red-700">{{ error }}</p>

    <div class="mt-6 space-y-3">
      <PoiCard v-for="poi in results" :key="poi.id" :poi="poi" />
    </div>

    <p v-if="searched && !busy && !results.length" class="mt-8 text-center text-gray-400">
      Nothing found for “{{ query }}”.
    </p>
  </div>
</template>
