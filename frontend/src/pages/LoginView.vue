<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { api } from '../api/client'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const mode = ref('login')
const email = ref('')
const username = ref('')
const password = ref('')
const error = ref(null)
const busy = ref(false)

async function submit() {
  error.value = null
  busy.value = true
  try {
    if (mode.value === 'register') {
      await api.register({ email: email.value, username: username.value, password: password.value })
    }
    await auth.login(email.value, password.value)
    router.push(route.query.next || '/map')
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="mx-auto mt-16 max-w-sm px-6">
    <h1 class="text-2xl font-bold text-gray-900">
      {{ mode === 'login' ? 'Sign in' : 'Create account' }}
    </h1>
    <form class="mt-6 space-y-4" @submit.prevent="submit">
      <input
        v-model="email"
        type="email"
        required
        placeholder="Email"
        class="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-emerald-500 focus:outline-none"
      />
      <input
        v-if="mode === 'register'"
        v-model="username"
        required
        minlength="3"
        placeholder="Username"
        class="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-emerald-500 focus:outline-none"
      />
      <input
        v-model="password"
        type="password"
        required
        minlength="8"
        placeholder="Password"
        class="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-emerald-500 focus:outline-none"
      />
      <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
      <button
        :disabled="busy"
        class="w-full rounded-md bg-emerald-600 py-2 font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
      >
        {{ mode === 'login' ? 'Sign in' : 'Register' }}
      </button>
    </form>
    <button
      class="mt-4 text-sm text-gray-500 hover:text-gray-700"
      @click="mode = mode === 'login' ? 'register' : 'login'"
    >
      {{ mode === 'login' ? 'Need an account? Register' : 'Have an account? Sign in' }}
    </button>
  </div>
</template>
