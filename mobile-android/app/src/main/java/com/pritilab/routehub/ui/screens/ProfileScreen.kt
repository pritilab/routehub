package com.pritilab.routehub.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.navigation.NavHostController
import com.pritilab.routehub.RouteHubApp
import com.pritilab.routehub.data.Profile
import com.pritilab.routehub.data.userMessage
import com.pritilab.routehub.ui.ErrorBox
import com.pritilab.routehub.ui.LoadingBox
import com.pritilab.routehub.ui.Ui
import kotlinx.coroutines.launch

/** [username] == null → own profile (requires login). */
@Composable
fun ProfileScreen(nav: NavHostController, username: String?) {
    val app = LocalContext.current.applicationContext as RouteHubApp
    val me by app.session.user.collectAsState()
    val scope = rememberCoroutineScope()

    val targetUsername = username ?: me?.username
    if (targetUsername == null) {
        LoginPrompt(nav, "Войдите, чтобы увидеть свой профиль.")
        return
    }
    val isOwn = targetUsername == me?.username

    var state by remember { mutableStateOf<Ui<Profile>>(Ui.Loading) }
    var reloadKey by remember { mutableStateOf(0) }
    var busy by remember { mutableStateOf(false) }

    LaunchedEffect(targetUsername, reloadKey) {
        state = Ui.Loading
        state = try {
            Ui.Data(app.api.profile(targetUsername))
        } catch (e: Exception) {
            Ui.Error(e.userMessage())
        }
    }

    when (val s = state) {
        is Ui.Loading -> LoadingBox()
        is Ui.Error -> ErrorBox(s.message) { reloadKey++ }
        is Ui.Data -> {
            val profile = s.value
            Column(
                Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                Text(
                    profile.display_name.ifBlank { profile.username },
                    style = MaterialTheme.typography.headlineSmall,
                )
                Text("@${profile.username}", color = MaterialTheme.colorScheme.onSurfaceVariant)
                if (profile.bio.isNotBlank()) Text(profile.bio)
                Row(horizontalArrangement = Arrangement.spacedBy(16.dp)) {
                    Text("Подписчики: ${profile.followers_count}")
                    Text("Подписки: ${profile.following_count}")
                }

                if (!isOwn && app.session.isLoggedIn) {
                    val following = profile.is_following == true
                    Button(
                        enabled = !busy,
                        onClick = {
                            busy = true
                            scope.launch {
                                try {
                                    if (following) app.api.unfollow(profile.username)
                                    else app.api.follow(profile.username)
                                    reloadKey++
                                } catch (_: Exception) {
                                } finally {
                                    busy = false
                                }
                            }
                        },
                    ) {
                        Text(if (following) "Отписаться" else "Подписаться")
                    }
                }
                if (!app.session.isLoggedIn) {
                    OutlinedButton(onClick = { nav.navigate("login") }) { Text("Войти") }
                }
                if (isOwn) {
                    OutlinedButton(
                        onClick = { scope.launch { app.session.logout() } },
                        modifier = Modifier.padding(top = 8.dp),
                    ) {
                        Text("Выйти из аккаунта")
                    }
                }
            }
        }
    }
}
