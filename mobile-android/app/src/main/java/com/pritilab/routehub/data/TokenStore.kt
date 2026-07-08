package com.pritilab.routehub.data

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.runBlocking

private val Context.authDataStore by preferencesDataStore(name = "auth")
private val KEY_TOKEN = stringPreferencesKey("access_token")

class TokenStore(private val context: Context) {

    /** In-memory copy for the synchronous OkHttp interceptor. */
    @Volatile
    var cached: String? = null
        private set

    /** One-time blocking read at app start (local file, fast). */
    fun loadBlocking() {
        cached = runBlocking { context.authDataStore.data.map { it[KEY_TOKEN] }.first() }
    }

    suspend fun save(token: String) {
        context.authDataStore.edit { it[KEY_TOKEN] = token }
        cached = token
    }

    suspend fun clear() {
        context.authDataStore.edit { it.remove(KEY_TOKEN) }
        cached = null
    }
}
