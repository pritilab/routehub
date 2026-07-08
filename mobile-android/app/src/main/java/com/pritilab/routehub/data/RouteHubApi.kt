package com.pritilab.routehub.data

import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query

interface RouteHubApi {

    // auth
    @POST("auth/register")
    suspend fun register(@Body body: RegisterIn): UserOut

    @POST("auth/login")
    suspend fun login(@Body body: LoginIn): TokenPair

    @GET("auth/me")
    suspend fun me(): UserOut

    // pois
    @GET("pois")
    suspend fun listPois(
        @Query("lat") lat: Double? = null,
        @Query("lng") lng: Double? = null,
        @Query("radius_m") radiusM: Int? = null,
        @Query("bbox") bbox: String? = null,
        @Query("city") city: String? = null,
        @Query("category") category: String? = null,
        @Query("limit") limit: Int = 50,
        @Query("offset") offset: Int = 0,
    ): List<Poi>

    @GET("pois/{id}")
    suspend fun getPoi(@Path("id") id: String): Poi

    @GET("pois/{id}/similar")
    suspend fun similarPois(@Path("id") id: String, @Query("limit") limit: Int = 5): List<Poi>

    @GET("pois/{id}/reviews")
    suspend fun listReviews(@Path("id") id: String, @Query("limit") limit: Int = 20): List<Review>

    @POST("pois/{id}/reviews")
    suspend fun postReview(@Path("id") id: String, @Body body: ReviewIn): Review

    @POST("pois/{id}/checkin")
    suspend fun checkIn(@Path("id") id: String, @Body body: CheckInIn): CheckIn

    // search
    @GET("search/pois/hybrid")
    suspend fun hybridSearch(@Query("q") q: String, @Query("limit") limit: Int = 20): List<Poi>

    // routes
    @GET("routes")
    suspend fun listRoutes(
        @Query("limit") limit: Int = 20,
        @Query("offset") offset: Int = 0,
    ): List<RouteOut>

    @POST("routes")
    suspend fun createRoute(@Body body: RouteCreate): RouteOut

    @GET("routes/{id}")
    suspend fun getRoute(@Path("id") id: String): RouteOut

    @POST("routes/{id}/save")
    suspend fun saveRoute(@Path("id") id: String)

    @DELETE("routes/{id}/save")
    suspend fun unsaveRoute(@Path("id") id: String)

    @GET("routes/saved/mine")
    suspend fun savedRoutes(
        @Query("limit") limit: Int = 20,
        @Query("offset") offset: Int = 0,
    ): List<RouteOut>

    // social
    @GET("feed")
    suspend fun feed(
        @Query("limit") limit: Int = 20,
        @Query("offset") offset: Int = 0,
    ): List<FeedItem>

    @GET("users/{username}")
    suspend fun profile(@Path("username") username: String): Profile

    @POST("users/{username}/follow")
    suspend fun follow(@Path("username") username: String)

    @DELETE("users/{username}/follow")
    suspend fun unfollow(@Path("username") username: String)
}
