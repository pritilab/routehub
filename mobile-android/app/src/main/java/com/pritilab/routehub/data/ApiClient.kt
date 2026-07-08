package com.pritilab.routehub.data

import okhttp3.OkHttpClient
import org.json.JSONObject
import retrofit2.HttpException
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.io.IOException
import java.util.concurrent.TimeUnit

fun buildApi(baseUrl: String, tokenProvider: () -> String?): RouteHubApi {
    val client = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .addInterceptor { chain ->
            val token = tokenProvider()
            val request = if (token != null) {
                chain.request().newBuilder().header("Authorization", "Bearer $token").build()
            } else {
                chain.request()
            }
            chain.proceed(request)
        }
        .build()

    return Retrofit.Builder()
        .baseUrl(if (baseUrl.endsWith("/")) baseUrl else "$baseUrl/")
        .client(client)
        .addConverterFactory(GsonConverterFactory.create())
        .build()
        .create(RouteHubApi::class.java)
}

/** Human-readable message: FastAPI `detail` field when present, generic otherwise. */
fun Throwable.userMessage(): String = when (this) {
    is HttpException -> {
        val detail = try {
            JSONObject(response()?.errorBody()?.string().orEmpty()).optString("detail")
        } catch (_: Exception) {
            ""
        }
        detail.ifBlank { "Ошибка сервера (HTTP ${code()})" }
    }
    is IOException -> "Нет соединения с сервером"
    else -> message ?: "Неизвестная ошибка"
}
