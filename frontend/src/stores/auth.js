import { defineStore } from 'pinia'
import { api } from '../api/client'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('rh_token') || null,
    user: null,
  }),
  actions: {
    async login(email, password) {
      const tokens = await api.login({ email, password })
      this.token = tokens.access_token
      localStorage.setItem('rh_token', this.token)
      await this.fetchMe()
    },
    async fetchMe() {
      if (!this.token) return
      try {
        this.user = await api.me(this.token)
      } catch {
        this.logout()
      }
    },
    logout() {
      this.token = null
      this.user = null
      localStorage.removeItem('rh_token')
    },
  },
})
