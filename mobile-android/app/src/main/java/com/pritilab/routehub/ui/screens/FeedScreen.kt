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
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.navigation.NavHostController
import com.pritilab.routehub.RouteHubApp
import com.pritilab.routehub.data.FeedItem
import com.pritilab.routehub.data.userMessage
import com.pritilab.routehub.ui.ErrorBox
import com.pritilab.routehub.ui.LoadingBox
import com.pritilab.routehub.ui.Ui
import com.pritilab.routehub.ui.formatDistance
import com.pritilab.routehub.ui.timeAgo

@Composable
fun FeedScreen(nav: NavHostController) {
    val app = LocalContext.current.applicationContext as RouteHubApp

    if (!app.session.isLoggedIn) {
        LoginPrompt(nav, "Лента показывает активность людей, на которых вы подписаны.")
        return
    }

    var state by remember { mutableStateOf<Ui<List<FeedItem>>>(Ui.Loading) }
    var reloadKey by remember { mutableStateOf(0) }

    LaunchedEffect(reloadKey) {
        state = Ui.Loading
        state = try {
            Ui.Data(app.api.feed(limit = 50))
        } catch (e: Exception) {
            Ui.Error(e.userMessage())
        }
    }

    when (val s = state) {
        is Ui.Loading -> LoadingBox()
        is Ui.Error -> ErrorBox(s.message) { reloadKey++ }
        is Ui.Data -> LazyColumn(Modifier.fillMaxSize()) {
            if (s.value.isEmpty()) {
                item {
                    Text(
                        "Лента пуста — подпишитесь на кого-нибудь через профиль.",
                        modifier = Modifier.padding(16.dp),
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }
            items(s.value) { item ->
                FeedCard(item, nav)
            }
        }
    }
}

@Composable
private fun FeedCard(item: FeedItem, nav: NavHostController) {
    Card(
        Modifier
            .fillMaxWidth()
            .padding(horizontal = 12.dp, vertical = 4.dp)
            .clickable {
                item.poi?.let { nav.navigate("poi/${it.id}") }
                    ?: item.route?.let { nav.navigate("route/${it.id}") }
            },
    ) {
        Column(Modifier.padding(12.dp)) {
            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(
                    item.actor.display_name.ifBlank { item.actor.username },
                    fontWeight = FontWeight.SemiBold,
                    modifier = Modifier.clickable { nav.navigate("user/${item.actor.username}") },
                )
                Text(
                    timeAgo(item.created_at),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            val body = when (item.type) {
                "checkin" -> "📍 отметился: ${item.poi?.title ?: ""}" +
                    if (item.comment.isNotBlank()) " — «${item.comment}»" else ""
                "review" -> "★ ${item.rating ?: "?"} — ${item.poi?.title ?: ""}" +
                    if (item.text.isNotBlank()) ": «${item.text}»" else ""
                "route_published" -> "🗺 опубликовал маршрут «${item.route?.title ?: ""}»" +
                    (item.route?.let { " (${formatDistance(it.total_distance_meters)})" } ?: "")
                else -> item.type
            }
            Text(body, style = MaterialTheme.typography.bodyMedium, modifier = Modifier.padding(top = 4.dp))
        }
    }
}

@Composable
fun LoginPrompt(nav: NavHostController, message: String) {
    Column(
        Modifier.fillMaxSize().padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
    ) {
        Text(message, style = MaterialTheme.typography.bodyLarge)
        Button(onClick = { nav.navigate("login") }, modifier = Modifier.padding(top = 16.dp)) {
            Text("Войти")
        }
    }
}
