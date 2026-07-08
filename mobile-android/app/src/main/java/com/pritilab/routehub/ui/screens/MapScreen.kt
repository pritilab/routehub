package com.pritilab.routehub.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.runtime.DisposableEffect
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.navigation.NavHostController
import com.pritilab.routehub.RouteHubApp
import com.pritilab.routehub.data.Poi
import com.pritilab.routehub.data.RouteCreate
import com.pritilab.routehub.data.RouteOut
import com.pritilab.routehub.data.RoutePointIn
import com.pritilab.routehub.data.userMessage
import com.pritilab.routehub.ui.formatDistance
import com.pritilab.routehub.ui.formatDuration
import kotlinx.coroutines.launch
import org.osmdroid.tileprovider.tilesource.TileSourceFactory
import org.osmdroid.util.GeoPoint
import org.osmdroid.views.MapView
import org.osmdroid.views.overlay.Marker
import org.osmdroid.views.overlay.Polyline

// Demo data lives around Amsterdam; a real app would start from device location.
private val DEFAULT_CENTER = GeoPoint(52.372, 4.894)

@Composable
fun MapScreen(nav: NavHostController) {
    val context = LocalContext.current
    val app = context.applicationContext as RouteHubApp
    val scope = rememberCoroutineScope()

    var pois by remember { mutableStateOf<List<Poi>>(emptyList()) }
    var selected by remember { mutableStateOf<List<Poi>>(emptyList()) }
    var createdRoute by remember { mutableStateOf<RouteOut?>(null) }
    var title by remember { mutableStateOf("") }
    var transport by remember { mutableStateOf("walking") }
    var optimize by remember { mutableStateOf(true) }
    var isPublic by remember { mutableStateOf(true) }
    var busy by remember { mutableStateOf(false) }
    var message by remember { mutableStateOf<String?>(null) }

    val mapView = remember {
        MapView(context).apply {
            setTileSource(TileSourceFactory.MAPNIK)
            setMultiTouchControls(true)
            controller.setZoom(13.5)
            controller.setCenter(DEFAULT_CENTER)
        }
    }
    DisposableEffect(Unit) {
        mapView.onResume()
        onDispose {
            mapView.onPause()
            mapView.onDetach()
        }
    }

    fun loadPois(lat: Double, lng: Double) {
        scope.launch {
            try {
                pois = app.api.listPois(lat = lat, lng = lng, radiusM = 10_000, limit = 100)
                message = if (pois.isEmpty()) "В этой области нет POI" else null
            } catch (e: Exception) {
                message = e.userMessage()
            }
        }
    }

    LaunchedEffect(Unit) { loadPois(DEFAULT_CENTER.latitude, DEFAULT_CENTER.longitude) }

    // Redraw overlays whenever data or selection changes.
    LaunchedEffect(pois, selected, createdRoute) {
        mapView.overlays.clear()
        createdRoute?.let { route ->
            val line = Polyline(mapView)
            line.setPoints(route.geometry.map { GeoPoint(it.lat, it.lng) })
            line.outlinePaint.color = android.graphics.Color.parseColor("#16A34A")
            line.outlinePaint.strokeWidth = 8f
            mapView.overlays.add(line)
        }
        pois.forEach { poi ->
            val index = selected.indexOfFirst { it.id == poi.id }
            val marker = Marker(mapView)
            marker.position = GeoPoint(poi.location.lat, poi.location.lng)
            marker.setAnchor(Marker.ANCHOR_CENTER, Marker.ANCHOR_BOTTOM)
            marker.title = if (index >= 0) "${index + 1}. ${poi.title}" else poi.title
            marker.alpha = if (index >= 0 || selected.isEmpty()) 1f else 0.6f
            marker.setOnMarkerClickListener { _, _ ->
                selected = if (index >= 0) selected.filterNot { it.id == poi.id }
                else selected + poi
                true
            }
            mapView.overlays.add(marker)
        }
        mapView.invalidate()
    }

    fun createRoute() {
        busy = true
        message = null
        scope.launch {
            try {
                val route = app.api.createRoute(
                    RouteCreate(
                        title = title.trim().ifBlank { "Маршрут из приложения" },
                        transport_mode = transport,
                        is_public = isPublic,
                        optimize_order = optimize,
                        route_type = if (optimize) "auto" else "manual",
                        points = selected.map { RoutePointIn(poi_id = it.id) },
                    ),
                )
                createdRoute = route
                message = "Маршрут создан: ${formatDistance(route.total_distance_meters)}, " +
                    formatDuration(route.estimated_duration_minutes)
            } catch (e: Exception) {
                message = e.userMessage()
            } finally {
                busy = false
            }
        }
    }

    Column(Modifier.fillMaxSize()) {
        Box(Modifier.fillMaxWidth().weight(1f)) {
            AndroidView(factory = { mapView }, modifier = Modifier.fillMaxSize())
            OutlinedButton(
                onClick = {
                    val c = mapView.mapCenter
                    loadPois(c.latitude, c.longitude)
                },
                modifier = Modifier.align(Alignment.TopEnd).padding(8.dp),
            ) {
                Text("Искать здесь")
            }
        }

        Column(
            Modifier
                .fillMaxWidth()
                .verticalScroll(rememberScrollState())
                .padding(12.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            message?.let { Text(it, style = MaterialTheme.typography.bodySmall) }

            if (selected.isEmpty() && createdRoute == null) {
                Text(
                    "Нажимайте на маркеры, чтобы собрать маршрут (мин. 2 точки).",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }

            if (selected.isNotEmpty()) {
                Card {
                    Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text(
                            "Точки: " + selected.mapIndexed { i, p -> "${i + 1}. ${p.title}" }
                                .joinToString(" → "),
                            style = MaterialTheme.typography.bodySmall,
                        )
                        OutlinedTextField(
                            value = title,
                            onValueChange = { title = it },
                            label = { Text("Название маршрута") },
                            singleLine = true,
                            modifier = Modifier.fillMaxWidth(),
                        )
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            listOf("walking", "cycling", "driving").forEach { mode ->
                                FilterChip(
                                    selected = transport == mode,
                                    onClick = { transport = mode },
                                    label = { Text(transportLabel(mode)) },
                                )
                            }
                        }
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Switch(checked = optimize, onCheckedChange = { optimize = it })
                            Text("Оптимизировать порядок", Modifier.padding(start = 8.dp))
                        }
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Switch(checked = isPublic, onCheckedChange = { isPublic = it })
                            Text("Публичный маршрут", Modifier.padding(start = 8.dp))
                        }
                        if (app.session.isLoggedIn) {
                            Button(
                                onClick = { createRoute() },
                                enabled = !busy && selected.size >= 2,
                                modifier = Modifier.fillMaxWidth(),
                            ) {
                                Text(if (busy) "Создание..." else "Создать маршрут (${selected.size})")
                            }
                        } else {
                            OutlinedButton(
                                onClick = { nav.navigate("login") },
                                modifier = Modifier.fillMaxWidth(),
                            ) {
                                Text("Войдите, чтобы создать маршрут")
                            }
                        }
                    }
                }
            }

            createdRoute?.let { route ->
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(onClick = { nav.navigate("route/${route.id}") }) {
                        Text("Открыть маршрут")
                    }
                    TextButton(onClick = {
                        createdRoute = null
                        selected = emptyList()
                        title = ""
                    }) {
                        Text("Сбросить")
                    }
                }
            }
        }
    }
}
