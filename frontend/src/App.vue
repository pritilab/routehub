<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from './stores/auth'

const auth = useAuthStore()
onMounted(() => auth.fetchMe())
</script>

<template>
  <div class="flex h-screen flex-col">
    <header class="flex items-center justify-between border-b border-gray-200 bg-white px-6 py-3">
      <router-link to="/" class="text-xl font-bold text-emerald-600">RouteHub</router-link>
      <nav class="flex items-center gap-4 text-sm">
        <router-link
          to="/search"
          class="text-gray-600 hover:text-gray-900"
          active-class="text-emerald-600 font-medium"
        >
          Search
        </router-link>
        <router-link
          to="/map"
          class="text-gray-600 hover:text-gray-900"
          active-class="text-emerald-600 font-medium"
        >
          Map
        </router-link>
        <router-link
          v-if="auth.user"
          to="/feed"
          class="text-gray-600 hover:text-gray-900"
          active-class="text-emerald-600 font-medium"
        >
          Feed
        </router-link>
        <template v-if="auth.user">
          <router-link
            :to="`/u/${auth.user.username}`"
            class="text-gray-600 hover:text-gray-900"
          >
            {{ auth.user.display_name || auth.user.username }}
          </router-link>
          <button class="text-gray-400 hover:text-gray-700" @click="auth.logout()">Logout</button>
        </template>
        <router-link
          v-else
          to="/login"
          class="rounded-md bg-emerald-600 px-3 py-1.5 text-white hover:bg-emerald-700"
        >
          Login
        </router-link>
      </nav>
    </header>
    <main class="min-h-0 flex-1 overflow-y-auto">
      <router-view />
    </main>
  </div>
</template>
