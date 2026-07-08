package com.pritilab.routehub.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.navigation.NavHostController
import com.pritilab.routehub.RouteHubApp
import com.pritilab.routehub.data.CheckInIn
import com.pritilab.routehub.data.Poi
import com.pritilab.routehub.data.Review
import com.pritilab.routehub.data.ReviewIn
import com.pritilab.routehub.data.userMessage
import com.pritilab.routehub.ui.ErrorBox
import com.pritilab.routehub.ui.LoadingBox
import com.pritilab.routehub.ui.PoiCard
import com.pritilab.routehub.ui.Ui
import com.pritilab.routehub.ui.timeAgo
import kotlinx.coroutines.launch

private data class PoiDetail(
    val poi: Poi,
    val reviews: List<Review>,
    val similar: List<Poi>,
)

@Composable
fun PoiDetailScreen(nav: NavHostController, poiId: String) {
    val app = LocalContext.current.applicationContext as RouteHubApp
    val scope = rememberCoroutineScope()
    var state by remember { mutableStateOf<Ui<PoiDetail>>(Ui.Loading) }
    var reloadKey by remember { mutableStateOf(0) }
    var actionMsg by remember { mutableStateOf<String?>(null) }

    LaunchedEffect(poiId, reloadKey) {
        state = Ui.Loading
        state = try {
            val poi = app.api.getPoi(poiId)
            val reviews = try { app.api.listReviews(poiId) } catch (_: Exception) { emptyList() }
            val similar = try { app.api.similarPois(poiId) } catch (_: Exception) { emptyList() }
            Ui.Data(PoiDetail(poi, reviews, similar))
        } catch (e: Exception) {
            Ui.Error(e.userMessage())
        }
    }

    when (val s = state) {
        is Ui.Loading -> LoadingBox()
        is Ui.Error -> ErrorBox(s.message) { reloadKey++ }
        is Ui.Data -> {
            val d = s.value
            LazyColumn(Modifier.fillMaxSize()) {
                item {
                    Column(Modifier.padding(16.dp)) {
                        Text(d.poi.title, style = MaterialTheme.typography.headlineSmall)
                        Text(
                            listOfNotNull(
                                d.poi.city.ifBlank { null },
                                d.poi.address.ifBlank { null },
                                d.poi.categories.joinToString(", ").ifBlank { null },
                            ).joinToString(" · "),
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                        if (d.poi.description.isNotBlank()) {
                            Text(d.poi.description, modifier = Modifier.padding(top = 8.dp))
                        }
                        Text(
                            (if (d.poi.rating_count > 0)
                                "★ %.1f (%d оценок)".format(d.poi.rating_avg, d.poi.rating_count)
                            else "Пока нет оценок") + " · ${d.poi.visit_count} визитов",
                            modifier = Modifier.padding(top = 8.dp),
                        )

                        if (app.session.isLoggedIn) {
                            CheckInBlock(
                                onCheckIn = { comment ->
                                    scope.launch {
                                        actionMsg = try {
                                            app.api.checkIn(poiId, CheckInIn(comment))
                                            reloadKey++
                                            null
                                        } catch (e: Exception) {
                                            e.userMessage()
                                        }
                                    }
                                },
                            )
                            ReviewBlock(
                                onSubmit = { rating, text ->
                                    scope.launch {
                                        actionMsg = try {
                                            app.api.postReview(poiId, ReviewIn(rating, text))
                                            reloadKey++
                                            null
                                        } catch (e: Exception) {
                                            e.userMessage()
                                        }
                                    }
                                },
                            )
                        } else {
                            TextButton(onClick = { nav.navigate("login") }) {
                                Text("Войдите, чтобы оставить отзыв или чек-ин")
                            }
                        }
                        actionMsg?.let { Text(it, color = MaterialTheme.colorScheme.error) }

                        if (d.reviews.isNotEmpty()) {
                            Text(
                                "Отзывы",
                                style = MaterialTheme.typography.titleMedium,
                                modifier = Modifier.padding(top = 12.dp),
                            )
                        }
                    }
                }
                items(d.reviews, key = { it.id }) { review ->
                    Card(Modifier.fillMaxWidth().padding(horizontal = 12.dp, vertical = 4.dp)) {
                        Column(Modifier.padding(12.dp)) {
                            Row(
                                Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                            ) {
                                Text(
                                    review.user.display_name.ifBlank { review.user.username },
                                    fontWeight = FontWeight.SemiBold,
                                )
                                Text("★".repeat(review.rating))
                            }
                            if (review.text.isNotBlank()) Text(review.text)
                            Text(
                                timeAgo(review.created_at),
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                            )
                        }
                    }
                }
                if (d.similar.isNotEmpty()) {
                    item {
                        Text(
                            "Похожие места",
                            style = MaterialTheme.typography.titleMedium,
                            modifier = Modifier.padding(start = 16.dp, top = 16.dp, bottom = 4.dp),
                        )
                    }
                    items(d.similar, key = { "sim-${it.id}" }) { poi ->
                        PoiCard(poi) { nav.navigate("poi/${poi.id}") }
                    }
                }
            }
        }
    }
}

@Composable
private fun CheckInBlock(onCheckIn: (String) -> Unit) {
    var comment by remember { mutableStateOf("") }
    Row(
        Modifier.fillMaxWidth().padding(top = 12.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        OutlinedTextField(
            value = comment,
            onValueChange = { comment = it },
            label = { Text("Комментарий (необязательно)") },
            singleLine = true,
            modifier = Modifier.weight(1f),
        )
        Button(onClick = { onCheckIn(comment.trim()); comment = "" }) {
            Text("📍 Я здесь")
        }
    }
}

@Composable
private fun ReviewBlock(onSubmit: (Int, String) -> Unit) {
    var rating by remember { mutableIntStateOf(0) }
    var text by remember { mutableStateOf("") }
    Column(Modifier.padding(top = 12.dp)) {
        Row {
            (1..5).forEach { star ->
                TextButton(onClick = { rating = star }) {
                    Text(
                        if (star <= rating) "★" else "☆",
                        style = MaterialTheme.typography.titleLarge,
                        color = MaterialTheme.colorScheme.primary,
                    )
                }
            }
        }
        OutlinedTextField(
            value = text,
            onValueChange = { text = it },
            label = { Text("Текст отзыва") },
            modifier = Modifier.fillMaxWidth(),
        )
        OutlinedButton(
            onClick = { onSubmit(rating, text.trim()) },
            enabled = rating in 1..5,
            modifier = Modifier.padding(top = 8.dp),
        ) {
            Text("Оставить отзыв")
        }
    }
}
