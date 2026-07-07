<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../api/client'
import { useAuthStore } from '../stores/auth'
import MapCanvas from '../components/MapCanvas.vue'

const auth = useAuthStore()

const pois = ref([])
const selected = ref([]) // ordered stops of the route being built
const title = ref('')
const transportMode = ref('walking')
const optimize = ref(true)
const isPublic = ref(true)
const creating = ref(false)
const created = ref(null)
const error = ref(null)

const selectedIds = computed(() => new Set(selected.value.map((p) => p.id)))
const routeLine = computed(() => created.value?.geometry ?? [])

onMounted(async () => {
  try {
    // Amsterdam center by default; later: geolocate the user
    pois.value = await api.listPois({ lat: 52.3728, lng: 4.8936, radius_m: 10000 })
  } catch {
    pois.value = []
  }
})

function toggleStop(poi) {
  if (selectedIds.value.has(poi.id)) {
    selected.value = selected.value.filter((p) => p.id !== poi.id)
  } else {
    selected.value = [...selected.value, poi]
  }
  created.value = null
}

function removeStop(idx) {
  selected.value = selected.value.filter((_, i) => i !== idx)
  created.value = null
}

async function createRoute() {
  creating.value = true
  error.value = null
  try {
    created.value = await api.createRoute(
      {
        title: title.value.trim() || 'My route',
        route_type: optimize.value ? 'auto' : 'manual',
        transport_mode: transportMode.value,
        is_public: isPublic.value,
        points: selected.value.map((p) => ({ poi_id: p.id })),
      },
      auth.token,
    )
    // reflect the server's (possibly optimized) stop order
    selected.value = created.value.points.map((rp) => rp.poi)
  } catch (e) {
    error.value = e.message
  } finally {
    creating.value = false
  }
}
</script>

<template>
  <div class="flex h-full">
    <aside class="flex w-96 shrink-0 flex-col overflow-y-auto border-r border-gray-200 bg-white">
      <!-- Route builder -->
      <div class="border-b border-gray-200 p-4">
        <h2 class="font-semibold text-gray-900">Route builder</h2>

        <p v-if="!selected.length" class="mt-2 text-sm text-gray-400">
          Pick at least two places below (or click markers on the map).
        </p>

        <ol v-else class="mt-3 space-y-1">
          <li
            v-for="(stop, idx) in selected"
            :key="stop.id"
            class="flex items-center gap-2 rounded-md bg-gray-50 px-2 py-1.5 text-sm"
          >
            <span
              class="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-emerald-600 text-xs font-bold text-white"
            >
              {{ idx + 1 }}
            </span>
            <span class="min-w-0 flex-1 truncate">{{ stop.title }}</span>
            <button
              class="text-gray-400 hover:text-red-500"
              :aria-label="`Remove ${stop.title}`"
              @click="removeStop(idx)"
            >
              ✕
            </button>
          </li>
        </ol>

        <template v-if="selected.length >= 2">
          <input
            v-model="title"
            placeholder="Route title"
            class="mt-3 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none"
          />
          <div class="mt-2 flex items-center gap-2">
            <select
              v-model="transportMode"
              class="flex-1 rounded-md border border-gray-300 px-2 py-2 text-sm focus:border-emerald-500 focus:outline-none"
            >
              <option value="walking">🚶 Walking</option>
              <option value="cycling">🚴 Cycling</option>
              <option value="driving">🚗 Driving</option>
              <option value="transit">🚌 Transit</option>
            </select>
          </div>
          <label class="mt-2 flex items-center gap-2 text-sm text-gray-600">
            <input v-model="optimize" type="checkbox" class="accent-emerald-600" />
            Optimize stop order
          </label>
          <label class="flex items-center gap-2 text-sm text-gray-600">
            <input v-model="isPublic" type="checkbox" class="accent-emerald-600" />
            Public route
          </label>

          <button
            v-if="auth.user"
            :disabled="creating"
            class="mt-3 w-full rounded-md bg-emerald-600 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
            @click="createRoute"
          >
            {{ creating ? 'Building…' : 'Create route' }}
          </button>
          <p v-else class="mt-3 text-sm text-gray-500">
            <router-link to="/login" class="text-emerald-600 hover:underline">Sign in</router-link>
            to create the route.
          </p>
        </template>

        <p v-if="error" class="mt-2 rounded-md bg-red-50 p-2 text-xs text-red-700">{{ error }}</p>

        <div v-if="created" class="mt-3 rounded-md bg-emerald-50 p-3 text-sm text-emerald-800">
          <p class="font-medium">“{{ created.title }}” created!</p>
          <p class="mt-1">
            {{ (created.total_distance_meters / 1000).toFixed(1) }} km ·
            ~{{ created.estimated_duration_minutes }} min · {{ created.transport_mode }}
          </p>
        </div>
      </div>

      <!-- Nearby POIs -->
      <div class="flex-1 p-4">
        <h2 class="font-semibold text-gray-900">Nearby points</h2>
        <ul class="mt-3 space-y-2">
          <li
            v-for="poi in pois"
            :key="poi.id"
            class="flex items-center gap-2 rounded-md border border-gray-100 p-3 text-sm hover:bg-gray-50"
          >
            <div class="min-w-0 flex-1">
              <router-link
                :to="`/poi/${poi.id}`"
                class="font-medium text-gray-900 hover:text-emerald-600"
              >
                {{ poi.title }}
              </router-link>
              <div class="text-xs text-gray-500">
                {{ poi.city || '—' }}
                <template v-if="poi.categories.length"> · {{ poi.categories.join(', ') }}</template>
              </div>
            </div>
            <button
              class="shrink-0 rounded-md px-2 py-1 text-xs font-medium"
              :class="
                selectedIds.has(poi.id)
                  ? 'bg-gray-200 text-gray-600 hover:bg-gray-300'
                  : 'bg-emerald-600 text-white hover:bg-emerald-700'
              "
              @click="toggleStop(poi)"
            >
              {{ selectedIds.has(poi.id) ? '✓ Added' : '+ Add' }}
            </button>
          </li>
          <li v-if="!pois.length" class="text-sm text-gray-400">No POIs in this area yet.</li>
        </ul>
      </div>
    </aside>

    <MapCanvas :pois="pois" :route="routeLine" class="flex-1" @select="toggleStop" />
  </div>
</template>
