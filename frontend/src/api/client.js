const BASE = import.meta.env.VITE_API_BASE || '/api/v1'

async function request(path, { method = 'GET', body, token } = {}) {
  const headers = { 'Content-Type': 'application/json' }
  if (token) headers.Authorization = `Bearer ${token}`
  const resp = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!resp.ok) {
    const detail = await resp.json().catch(() => ({}))
    throw new Error(detail.detail || `Request failed: ${resp.status}`)
  }
  if (resp.status === 204) return null
  return resp.json()
}

const qs = (params) => {
  const s = new URLSearchParams(
    Object.fromEntries(Object.entries(params).filter(([, v]) => v != null && v !== '')),
  ).toString()
  return s ? `?${s}` : ''
}

export const api = {
  // auth
  register: (data) => request('/auth/register', { method: 'POST', body: data }),
  login: (data) => request('/auth/login', { method: 'POST', body: data }),
  me: (token) => request('/auth/me', { token }),

  // pois
  listPois: (params = {}) => request(`/pois${qs(params)}`),
  createPoi: (data, token) => request('/pois', { method: 'POST', body: data, token }),
  getPoi: (id) => request(`/pois/${id}`),
  similarPois: (id, limit = 5) => request(`/pois/${id}/similar${qs({ limit })}`),
  poiReviews: (id) => request(`/pois/${id}/reviews`),
  checkIn: (id, comment, token) =>
    request(`/pois/${id}/checkin`, { method: 'POST', body: { comment }, token }),
  review: (id, rating, text, token) =>
    request(`/pois/${id}/reviews`, { method: 'POST', body: { rating, text }, token }),

  // search
  searchPois: (q, limit = 20) => request(`/search/pois${qs({ q, limit })}`),
  hybridSearch: (q, limit = 20) => request(`/search/pois/hybrid${qs({ q, limit })}`),
  semanticSearch: (q, limit = 20) => request(`/search/pois/semantic${qs({ q, limit })}`),

  // routes
  listRoutes: () => request('/routes'),
  createRoute: (data, token) => request('/routes', { method: 'POST', body: data, token }),
  saveRoute: (id, token) => request(`/routes/${id}/save`, { method: 'POST', token }),
  unsaveRoute: (id, token) => request(`/routes/${id}/save`, { method: 'DELETE', token }),
  savedRoutes: (token) => request('/routes/saved/mine', { token }),

  // social
  feed: (token, params = {}) => request(`/feed${qs(params)}`, { token }),
  profile: (username, token) => request(`/users/${username}`, { token }),
  follow: (username, token) => request(`/users/${username}/follow`, { method: 'POST', token }),
  unfollow: (username, token) =>
    request(`/users/${username}/follow`, { method: 'DELETE', token }),
  followers: (username) => request(`/users/${username}/followers`),
  following: (username) => request(`/users/${username}/following`),
}
