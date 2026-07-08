package com.pritilab.routehub.data

// Field names mirror the FastAPI JSON contract verbatim (snake_case) so Gson
// needs no annotations. See backend/api/schemas/*.py.

data class LatLng(val lat: Double, val lng: Double)

// --- auth ---

data class RegisterIn(
    val email: String,
    val username: String,
    val password: String,
    val display_name: String = "",
)

data class LoginIn(val email: String, val password: String)

data class TokenPair(
    val access_token: String,
    val refresh_token: String,
    val token_type: String,
)

data class UserOut(
    val id: String,
    val email: String,
    val username: String,
    val display_name: String,
    val avatar_url: String,
    val bio: String,
    val role: String,
)

// --- pois ---

data class Poi(
    val id: String,
    val title: String,
    val description: String,
    val short_description: String,
    val location: LatLng,
    val address: String,
    val city: String,
    val country: String,
    val categories: List<String>,
    val photos: List<String>,
    val is_official: Boolean,
    val is_temporary: Boolean,
    val rating_avg: Double,
    val rating_count: Int,
    val visit_count: Int,
    val save_count: Int,
    val created_at: String,
)

data class PublicUser(
    val id: String,
    val username: String,
    val display_name: String,
    val avatar_url: String,
)

data class Profile(
    val id: String,
    val username: String,
    val display_name: String,
    val avatar_url: String,
    val bio: String,
    val role: String,
    val followers_count: Int,
    val following_count: Int,
    val is_following: Boolean?,
)

data class ReviewIn(val rating: Int, val text: String = "")

data class Review(
    val id: String,
    val user: PublicUser,
    val rating: Int,
    val text: String,
    val created_at: String,
)

data class CheckInIn(val comment: String = "")

data class CheckIn(
    val id: String,
    val poi_id: String,
    val user: PublicUser,
    val comment: String,
    val created_at: String,
)

// --- routes ---

data class RoutePointIn(
    val poi_id: String,
    val stay_duration_minutes: Int = 0,
    val custom_note: String = "",
)

data class RouteCreate(
    val title: String,
    val description: String = "",
    val route_type: String = "manual",
    val transport_mode: String = "walking",
    val theme_tags: List<String> = emptyList(),
    val is_public: Boolean = false,
    val points: List<RoutePointIn>,
    val optimize_order: Boolean = false,
)

data class RoutePointOut(
    val poi: Poi,
    val order_index: Int,
    val stay_duration_minutes: Int,
    val custom_note: String,
    val distance_to_next_meters: Int,
    val duration_to_next_minutes: Int,
)

data class RouteOut(
    val id: String,
    val title: String,
    val description: String,
    val route_type: String,
    val transport_mode: String,
    val theme_tags: List<String>,
    val total_distance_meters: Int,
    val estimated_duration_minutes: Int,
    val difficulty_level: String,
    val is_public: Boolean,
    val geometry: List<LatLng>,
    val points: List<RoutePointOut>,
    val created_at: String,
)

// --- feed ---

data class PoiBrief(
    val id: String,
    val title: String,
    val city: String,
    val location: LatLng,
)

data class RouteSummary(
    val id: String,
    val title: String,
    val transport_mode: String,
    val theme_tags: List<String>,
    val total_distance_meters: Int,
    val estimated_duration_minutes: Int,
)

data class FeedItem(
    val type: String, // checkin | review | route_published
    val created_at: String,
    val actor: PublicUser,
    val poi: PoiBrief?,
    val route: RouteSummary?,
    val comment: String,
    val rating: Int?,
    val text: String,
)
