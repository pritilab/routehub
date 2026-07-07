<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api/client'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const auth = useAuthStore()

const profile = ref(null)
const people = ref({ tab: null, list: [] })
const error = ref(null)
const busy = ref(false)

async function load() {
  error.value = null
  profile.value = null
  people.value = { tab: null, list: [] }
  try {
    profile.value = await api.profile(route.params.username, auth.token)
  } catch (e) {
    error.value = e.message
  }
}

async function toggleFollow() {
  if (!auth.token || !profile.value) return
  busy.value = true
  try {
    if (profile.value.is_following) {
      await api.unfollow(profile.value.username, auth.token)
      profile.value.is_following = false
      profile.value.followers_count -= 1
    } else {
      await api.follow(profile.value.username, auth.token)
      profile.value.is_following = true
      profile.value.followers_count += 1
    }
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}

async function showPeople(tab) {
  if (people.value.tab === tab) {
    people.value = { tab: null, list: [] }
    return
  }
  const fn = tab === 'followers' ? api.followers : api.following
  people.value = { tab, list: await fn(profile.value.username) }
}

onMounted(load)
watch(() => route.params.username, load)
</script>

<template>
  <div class="mx-auto max-w-2xl px-6 py-8">
    <p v-if="error" class="rounded-md bg-red-50 p-3 text-sm text-red-700">{{ error }}</p>

    <template v-if="profile">
      <div class="flex items-start gap-4">
        <div
          class="flex h-16 w-16 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-2xl font-bold text-emerald-700"
        >
          {{ (profile.display_name || profile.username)[0].toUpperCase() }}
        </div>
        <div class="min-w-0 flex-1">
          <h1 class="text-2xl font-bold text-gray-900">
            {{ profile.display_name || profile.username }}
          </h1>
          <p class="text-sm text-gray-500">@{{ profile.username }} · {{ profile.role }}</p>
          <p v-if="profile.bio" class="mt-2 text-sm text-gray-700">{{ profile.bio }}</p>
        </div>
        <button
          v-if="auth.user && auth.user.username !== profile.username"
          :disabled="busy"
          class="shrink-0 rounded-md px-4 py-1.5 text-sm font-medium disabled:opacity-50"
          :class="
            profile.is_following
              ? 'border border-gray-300 text-gray-600 hover:bg-gray-50'
              : 'bg-emerald-600 text-white hover:bg-emerald-700'
          "
          @click="toggleFollow"
        >
          {{ profile.is_following ? 'Unfollow' : 'Follow' }}
        </button>
      </div>

      <div class="mt-6 flex gap-6 border-b border-gray-200 pb-3 text-sm">
        <button class="hover:text-emerald-600" @click="showPeople('followers')">
          <span class="font-semibold">{{ profile.followers_count }}</span> followers
        </button>
        <button class="hover:text-emerald-600" @click="showPeople('following')">
          <span class="font-semibold">{{ profile.following_count }}</span> following
        </button>
      </div>

      <ul v-if="people.tab" class="mt-4 space-y-2">
        <li v-if="!people.list.length" class="text-sm text-gray-400">
          No {{ people.tab }} yet.
        </li>
        <li v-for="p in people.list" :key="p.id">
          <router-link
            :to="`/u/${p.username}`"
            class="text-sm text-gray-700 hover:text-emerald-600"
          >
            {{ p.display_name || p.username }}
            <span class="text-gray-400">@{{ p.username }}</span>
          </router-link>
        </li>
      </ul>
    </template>
  </div>
</template>
