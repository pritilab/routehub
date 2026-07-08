package com.pritilab.routehub.ui.screens

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
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
import kotlinx.coroutines.launch

@Composable
fun RouteDetailScreen(nav: NavHostController, routeId: String) {
    val app = LocalContext.current.applicationContext as RouteHubApp
    val scope = rememberCoroutineScope()
    var state by remember { mutableStateOf<Ui<RouteOut>>(Ui.Loading) }
    var reloadKey by remember { mutableStateOf(0) }
    var saved by remember { mutableStateOf(false) }
    var saveMsg by remember { mutableStateOf<String?>(null) }

    LaunchedEffect(reloadKey) {
        state = Ui.Loading
        state = try {
            Ui.Data(app.api.getRoute(routeId))
        } catch (e: Exception) {
            Ui.Error(e.userMessage())
        }
    }

    when (val s = state) {
        is Ui.Loading -> LoadingBox()
        is Ui.Error -> ErrorBox(s.message) { reloadKey++ }
        is Ui.Data -> {
            val route = s.value
            LazyColumn(Modifier.fillMaxSize()) {
                item {
                    Column(Modifier.padding(16.dp)) {
                        Text(route.title, style = MaterialTheme.typography.headlineSmall)
                        if (route.description.isNotBlank()) {
                            Text(
                                route.description,
                                style = MaterialTheme.typography.bodyMedium,
                                modifier = Modifier.padding(top = 4.dp),
                            )
                        }
                        Text(
                            "${transportLabel(route.transport_mode)} · " +
                                "${formatDistance(route.total_distance_meters)} · " +
                                formatDuration(route.estimated_duration_minutes),
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                            modifier = Modifier.padding(top = 6.dp),
                        )
                        if (app.session.isLoggedIn) {
                            OutlinedButton(
                                onClick = {
                                    scope.launch {
                                        try {
                                            if (saved) app.api.unsaveRoute(route.id)
                                            else app.api.saveRoute(route.id)
                                            saved = !saved
                                            saveMsg = null
                                        } catch (e: Exception) {
                                            saveMsg = e.userMessage()
                                        }
                                    }
                                },
                                modifier = Modifier.padding(top = 8.dp),
                            ) {
                                Text(if (saved) "✓ Сохранено" else "Сохранить маршрут")
                            }
                            saveMsg?.let {
                                Text(it, color = MaterialTheme.colorScheme.error)
                            }
                        }
                        Text(
                            "Точки маршрута",
                            style = MaterialTheme.typography.titleMedium,
                            modifier = Modifier.padding(top = 12.dp),
                        )
                    }
                }
                itemsIndexed(route.points) { i, point ->
                    Card(
                        Modifier
                            .fillMaxWidth()
                            .padding(horizontal = 12.dp, vertical = 4.dp)
                            .clickable { nav.navigate("poi/${point.poi.id}") },
                    ) {
                        Column(Modifier.padding(12.dp)) {
                            Row {
                                Text(
                                    "${i + 1}. ${point.poi.title}",
                                    style = MaterialTheme.typography.titleSmall,
                                    fontWeight = FontWeight.SemiBold,
                                )
                            }
                            if (point.distance_to_next_meters > 0) {
                                Text(
                                    "до следующей: ${formatDistance(point.distance_to_next_meters)} · " +
                                        formatDuration(point.duration_to_next_minutes),
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}
