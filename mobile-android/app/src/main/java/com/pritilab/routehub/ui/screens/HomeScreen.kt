package com.pritilab.routehub.ui.screens

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.navigation.NavHostController
import com.pritilab.routehub.RouteHubApp
import com.pritilab.routehub.data.RouteOut
import com.pritilab.routehub.data.userMessage
import com.pritilab.routehub.ui.ErrorBox
import com.pritilab.routehub.ui.LoadingBox
import com.pritilab.routehub.ui.Ui
import com.pritilab.routehub.ui.formatDistance
import com.pritilab.routehub.ui.formatDuration

private val TRANSPORT_LABELS = mapOf(
    "walking" to "🚶 пешком",
    "cycling" to "🚴 велосипед",
    "driving" to "🚗 авто",
    "transit" to "🚌 транспорт",
)

fun transportLabel(mode: String): String = TRANSPORT_LABELS[mode] ?: mode

@Composable
fun HomeScreen(nav: NavHostController) {
    val app = LocalContext.current.applicationContext as RouteHubApp
    var state by remember { mutableStateOf<Ui<List<RouteOut>>>(Ui.Loading) }
    var reloadKey by remember { mutableStateOf(0) }

    LaunchedEffect(reloadKey) {
        state = Ui.Loading
        state = try {
            Ui.Data(app.api.listRoutes(limit = 50))
        } catch (e: Exception) {
            Ui.Error(e.userMessage())
        }
    }

    when (val s = state) {
        is Ui.Loading -> LoadingBox()
        is Ui.Error -> ErrorBox(s.message) { reloadKey++ }
        is Ui.Data -> LazyColumn(
            Modifier.fillMaxSize(),
            contentPadding = androidx.compose.foundation.layout.PaddingValues(vertical = 8.dp),
        ) {
            item {
                Text(
                    "Публичные маршруты",
                    style = MaterialTheme.typography.titleLarge,
                    modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp),
                )
            }
            if (s.value.isEmpty()) {
                item {
                    Text(
                        "Пока пусто — создайте первый маршрут на вкладке «Карта».",
                        modifier = Modifier.padding(16.dp),
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }
            items(s.value, key = { it.id }) { route ->
                RouteCard(route) { nav.navigate("route/${route.id}") }
            }
        }
    }
}

@Composable
fun RouteCard(route: RouteOut, onClick: () -> Unit) {
    Card(
        Modifier
            .fillMaxWidth()
            .padding(horizontal = 12.dp, vertical = 4.dp)
            .clickable(onClick = onClick),
    ) {
        Column(Modifier.padding(12.dp)) {
            Text(route.title, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
            Row(
                Modifier.fillMaxWidth().padding(top = 6.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                Text(transportLabel(route.transport_mode), style = MaterialTheme.typography.bodySmall)
                Text(
                    "${route.points.size} точек · ${formatDistance(route.total_distance_meters)} · " +
                        formatDuration(route.estimated_duration_minutes),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
    }
}
