package com.pritilab.routehub.ui.screens

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.navigation.NavHostController
import com.pritilab.routehub.RouteHubApp
import com.pritilab.routehub.data.Poi
import com.pritilab.routehub.data.userMessage
import com.pritilab.routehub.ui.ErrorBox
import com.pritilab.routehub.ui.LoadingBox
import com.pritilab.routehub.ui.PoiCard
import com.pritilab.routehub.ui.Ui
import kotlinx.coroutines.delay

@Composable
fun SearchScreen(nav: NavHostController) {
    val app = LocalContext.current.applicationContext as RouteHubApp
    var query by remember { mutableStateOf("") }
    var state by remember { mutableStateOf<Ui<List<Poi>>>(Ui.Data(emptyList())) }

    // Debounced hybrid search, mirroring the web frontend (350 ms).
    LaunchedEffect(query) {
        val q = query.trim()
        if (q.length < 2) {
            state = Ui.Data(emptyList())
            return@LaunchedEffect
        }
        delay(350)
        state = Ui.Loading
        state = try {
            Ui.Data(app.api.hybridSearch(q))
        } catch (e: Exception) {
            Ui.Error(e.userMessage())
        }
    }

    Column(Modifier.fillMaxSize()) {
        OutlinedTextField(
            value = query,
            onValueChange = { query = it },
            label = { Text("Поиск мест (гибридный: ключевой + семантика)") },
            singleLine = true,
            modifier = Modifier.fillMaxWidth().padding(12.dp),
        )
        when (val s = state) {
            is Ui.Loading -> LoadingBox()
            is Ui.Error -> ErrorBox(s.message)
            is Ui.Data -> LazyColumn(Modifier.fillMaxSize()) {
                if (s.value.isEmpty() && query.trim().length >= 2) {
                    item {
                        Text(
                            "Ничего не найдено",
                            modifier = Modifier.padding(16.dp),
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                }
                items(s.value, key = { it.id }) { poi ->
                    PoiCard(poi) { nav.navigate("poi/${poi.id}") }
                }
            }
        }
    }
}
