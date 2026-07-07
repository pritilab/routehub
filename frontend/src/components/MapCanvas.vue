<script setup>
import { onMounted, onUnmounted, ref, watch } from 'vue'

const props = defineProps({
  pois: { type: Array, default: () => [] },
  route: { type: Array, default: () => [] }, // ordered [{lat, lng}] polyline
})
const emit = defineEmits(['select'])

const container = ref(null)
const token = import.meta.env.VITE_MAPBOX_TOKEN
let map = null
let mapboxgl = null
let markers = []
let styleLoaded = false

async function initMap() {
  if (!token) return
  mapboxgl = (await import('mapbox-gl')).default
  mapboxgl.accessToken = token
  map = new mapboxgl.Map({
    container: container.value,
    style: 'mapbox://styles/mapbox/streets-v12',
    center: [4.8936, 52.3728],
    zoom: 13,
  })
  map.on('load', () => {
    styleLoaded = true
    map.addSource('route-line', {
      type: 'geojson',
      data: { type: 'Feature', geometry: { type: 'LineString', coordinates: [] } },
    })
    map.addLayer({
      id: 'route-line',
      type: 'line',
      source: 'route-line',
      paint: { 'line-color': '#059669', 'line-width': 4, 'line-opacity': 0.8 },
    })
    syncRoute()
  })
  syncMarkers()
}

function syncMarkers() {
  if (!map) return
  markers.forEach((m) => m.remove())
  markers = props.pois.map((poi) => {
    const marker = new mapboxgl.Marker({ color: '#059669' })
      .setLngLat([poi.location.lng, poi.location.lat])
      .setPopup(new mapboxgl.Popup({ offset: 24 }).setText(poi.title))
      .addTo(map)
    marker.getElement().style.cursor = 'pointer'
    marker.getElement().addEventListener('click', () => emit('select', poi))
    return marker
  })
}

function syncRoute() {
  if (!map || !styleLoaded) return
  const coords = props.route.map((p) => [p.lng, p.lat])
  map.getSource('route-line').setData({
    type: 'Feature',
    geometry: { type: 'LineString', coordinates: coords },
  })
  if (coords.length >= 2) {
    const lngs = coords.map((c) => c[0])
    const lats = coords.map((c) => c[1])
    map.fitBounds(
      [
        [Math.min(...lngs), Math.min(...lats)],
        [Math.max(...lngs), Math.max(...lats)],
      ],
      { padding: 60, duration: 700 },
    )
  }
}

watch(() => props.pois, syncMarkers)
watch(() => props.route, syncRoute)

onMounted(initMap)
onUnmounted(() => map?.remove())
</script>

<template>
  <div class="relative h-full">
    <div ref="container" class="h-full w-full" />
    <div
      v-if="!token"
      class="absolute inset-0 flex items-center justify-center bg-gray-100 text-center"
    >
      <div class="max-w-sm text-gray-500">
        <p class="font-medium">Map disabled</p>
        <p class="mt-1 text-sm">
          Set <code class="rounded bg-gray-200 px-1">VITE_MAPBOX_TOKEN</code> in
          <code class="rounded bg-gray-200 px-1">.env</code> to render the map.
          The route builder in the sidebar works without it.
        </p>
      </div>
    </div>
  </div>
</template>
