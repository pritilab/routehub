package com.pritilab.routehub.data

import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import retrofit2.HttpException

/** Auth state shared by all screens: current user + login/logout, 401 → drop token. */
class Session(private val api: RouteHubApi, private val tokenStore: TokenStore) {

    private val _user = MutableStateFlow<UserOut?>(null)
    val user: StateFlow<UserOut?> = _user

    val isLoggedIn: Boolean
        get() = tokenStore.cached != null

    suspend fun login(email: String, password: String) {
        val tokens = api.login(LoginIn(email = email, password = password))
        tokenStore.save(tokens.access_token)
        refreshMe()
    }

    suspend fun register(email: String, username: String, password: String, displayName: String) {
        api.register(RegisterIn(email, username, password, displayName))
        login(email, password)
    }

    /** Restore session on app start; silently logs out on a stale token. */
    suspend fun refreshMe() {
        if (tokenStore.cached == null) return
        try {
            _user.value = api.me()
        } catch (e: HttpException) {
            if (e.code() == 401) logout() else throw e
        }
    }

    suspend fun logout() {
        tokenStore.clear()
        _user.value = null
    }
}
