<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api/client'
import { useAuthStore } from '../stores/auth'
import { timeAgo } from '../utils/time'

const route = useRoute()
const auth = useAuthStore()

const poi = ref(null)
const reviews = ref([])
const similar = ref([])
const error = ref(null)
const notice = ref(null)

const checkinComment = ref('')
const reviewRating = ref(0)
const reviewText = ref('')
const busy = ref(false)

async function load() {
  error.value = null
  notice.value = null
  try {
    const id = route.params.id
    ;[poi.value, reviews.value, similar.value] = await Promise.all([
      api.getPoi(id),
      api.poiReviews(id),
      api.similarPois(id),
    ])
  } catch (e) {
    error.value = e.message
  }
}

async function doCheckIn() {
  busy.value = true
  error.value = null
  try {
    await api.checkIn(poi.value.id, checkinComment.value, auth.token)
    poi.value.visit_count += 1
    checkinComment.value = ''
    notice.value = 'Checked in!'
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}

async function submitReview() {
  if (!reviewRating.value) return
  busy.value = true
  error.value = null
  try {
    await api.review(poi.value.id, reviewRating.value, reviewText.value, auth.token)
    reviewRating.value = 0
    reviewText.value = ''
    notice.value = 'Review saved'
    // rating and the list are recomputed server-side — refetch
    ;[poi.value, reviews.value] = await Promise.all([
      api.getPoi(poi.value.id),
      api.poiReviews(poi.value.id),
    ])
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}

onMounted(load)
watch(() => route.params.id, load)
</script>

<template>
  <div class="mx-auto max-w-3xl px-6 py-8">
    <p v-if="error" class="mb-4 rounded-md bg-red-50 p-3 text-sm text-red-700">{{ error }}</p>
    <p v-if="notice" class="mb-4 rounded-md bg-emerald-50 p-3 text-sm text-emerald-700">
      {{ notice }}
    </p>

    <template v-if="poi">
      <div class="flex items-start justify-between gap-4">
        <div>
          <h1 class="text-3xl font-bold text-gray-900">{{ poi.title }}</h1>
          <p class="mt-1 text-sm text-gray-500">
            {{ [poi.address, poi.city, poi.country].filter(Boolean).join(', ') || 'No address' }}
          </p>
        </div>
        <div class="shrink-0 text-right">
          <div v-if="poi.rating_count" class="text-lg text-amber-600">
            ★ {{ poi.rating_avg.toFixed(1) }}
            <span class="text-sm text-gray-400">({{ poi.rating_count }})</span>
          </div>
          <div class="text-xs text-gray-400">{{ poi.visit_count }} visits</div>
        </div>
      </div>

      <div class="mt-3 flex flex-wrap gap-2">
        <span
          v-for="cat in poi.categories"
          :key="cat"
          class="rounded-full bg-emerald-50 px-2 py-0.5 text-xs text-emerald-700"
        >
          {{ cat }}
        </span>
        <span v-if="poi.is_official" class="rounded-full bg-blue-50 px-2 py-0.5 text-xs text-blue-700">
          official
        </span>
      </div>

      <p v-if="poi.description" class="mt-4 text-gray-700">{{ poi.description }}</p>

      <!-- Check-in -->
      <div v-if="auth.user" class="mt-6 rounded-lg border border-gray-200 bg-white p-4">
        <h2 class="font-semibold text-gray-900">Check in</h2>
        <div class="mt-2 flex gap-2">
          <input
            v-model="checkinComment"
            maxlength="280"
            placeholder="Optional comment…"
            class="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none"
          />
          <button
            :disabled="busy"
            class="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
            @click="doCheckIn"
          >
            📍 Check in
          </button>
        </div>
      </div>

      <!-- Reviews -->
      <div class="mt-6">
        <h2 class="text-xl font-semibold text-gray-900">Reviews</h2>

        <div v-if="auth.user" class="mt-3 rounded-lg border border-gray-200 bg-white p-4">
          <div class="flex items-center gap-1">
            <button
              v-for="n in 5"
              :key="n"
              class="text-2xl"
              :class="n <= reviewRating ? 'text-amber-500' : 'text-gray-300 hover:text-amber-300'"
              :aria-label="`Rate ${n}`"
              @click="reviewRating = n"
            >
              ★
            </button>
          </div>
          <textarea
            v-model="reviewText"
            rows="2"
            placeholder="Share your experience…"
            class="mt-2 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none"
          />
          <button
            :disabled="busy || !reviewRating"
            class="mt-2 rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
            @click="submitReview"
          >
            Submit review
          </button>
        </div>
        <p v-else class="mt-2 text-sm text-gray-500">
          <router-link to="/login" class="text-emerald-600 hover:underline">Sign in</router-link>
          to check in and review.
        </p>

        <div class="mt-4 space-y-3">
          <div
            v-for="r in reviews"
            :key="r.id"
            class="rounded-lg border border-gray-200 bg-white p-4"
          >
            <div class="flex items-baseline justify-between">
              <router-link
                :to="`/u/${r.user.username}`"
                class="text-sm font-medium text-gray-900 hover:text-emerald-600"
              >
                {{ r.user.display_name || r.user.username }}
              </router-link>
              <span class="text-xs text-gray-400">{{ timeAgo(r.created_at) }}</span>
            </div>
            <div class="mt-1 text-amber-500">{{ '★'.repeat(r.rating) }}</div>
            <p v-if="r.text" class="mt-1 text-sm text-gray-700">{{ r.text }}</p>
          </div>
          <p v-if="!reviews.length" class="text-sm text-gray-400">No reviews yet.</p>
        </div>
      </div>

      <!-- Similar -->
      <div v-if="similar.length" class="mt-8">
        <h2 class="text-xl font-semibold text-gray-900">Similar places</h2>
        <ul class="mt-3 space-y-2">
          <li v-for="s in similar" :key="s.id">
            <router-link
              :to="`/poi/${s.id}`"
              class="text-sm text-gray-700 hover:text-emerald-600"
            >
              <span class="font-medium">{{ s.title }}</span>
              <span v-if="s.city" class="text-gray-400"> · {{ s.city }}</span>
            </router-link>
          </li>
        </ul>
      </div>
    </template>
  </div>
</template>
