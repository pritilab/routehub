package com.pritilab.routehub.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.pritilab.routehub.data.Poi
import java.time.Duration
import java.time.OffsetDateTime

/** Simple per-screen state machine. */
sealed interface Ui<out T> {
    data object Loading : Ui<Nothing>
    data class Error(val message: String) : Ui<Nothing>
    data class Data<T>(val value: T) : Ui<T>
}

@Composable
fun LoadingBox() {
    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        CircularProgressIndicator()
    }
}

@Composable
fun ErrorBox(message: String, onRetry: (() -> Unit)? = null) {
    Column(
        Modifier.fillMaxSize().padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
    ) {
        Text(message, color = MaterialTheme.colorScheme.error)
        if (onRetry != null) {
            Button(onClick = onRetry, modifier = Modifier.padding(top = 12.dp)) {
                Text("Повторить")
            }
        }
    }
}

@Composable
fun PoiCard(poi: Poi, onClick: () -> Unit) {
    Card(
        Modifier
            .fillMaxWidth()
            .padding(horizontal = 12.dp, vertical = 4.dp)
            .clickable(onClick = onClick),
    ) {
        Column(Modifier.padding(12.dp)) {
            Text(poi.title, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
            if (poi.short_description.isNotBlank()) {
                Text(
                    poi.short_description,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            Row(
                Modifier.fillMaxWidth().padding(top = 6.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                Text(
                    listOfNotNull(
                        poi.city.ifBlank { null },
                        poi.categories.firstOrNull(),
                    ).joinToString(" · "),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                Text(
                    if (poi.rating_count > 0) "★ %.1f (%d)".format(poi.rating_avg, poi.rating_count)
                    else "нет оценок",
                    style = MaterialTheme.typography.bodySmall,
                )
            }
        }
    }
}

fun formatDistance(meters: Int): String =
    if (meters >= 1000) "%.1f км".format(meters / 1000.0) else "$meters м"

fun formatDuration(minutes: Int): String {
    val h = minutes / 60
    val m = minutes % 60
    return if (h > 0) "$h ч $m мин" else "$m мин"
}

fun timeAgo(iso: String): String {
    val then = try {
        OffsetDateTime.parse(iso)
    } catch (_: Exception) {
        return iso
    }
    val d = Duration.between(then, OffsetDateTime.now())
    return when {
        d.toMinutes() < 1 -> "только что"
        d.toMinutes() < 60 -> "${d.toMinutes()} мин назад"
        d.toHours() < 24 -> "${d.toHours()} ч назад"
        else -> "${d.toDays()} дн назад"
    }
}
