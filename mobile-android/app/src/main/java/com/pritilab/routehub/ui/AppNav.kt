package com.pritilab.routehub.ui

import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.List
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.Place
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import androidx.compose.runtime.getValue
import com.pritilab.routehub.RouteHubApp
import com.pritilab.routehub.ui.screens.FeedScreen
import com.pritilab.routehub.ui.screens.HomeScreen
import com.pritilab.routehub.ui.screens.LoginScreen
import com.pritilab.routehub.ui.screens.MapScreen
import com.pritilab.routehub.ui.screens.PoiDetailScreen
import com.pritilab.routehub.ui.screens.ProfileScreen
import com.pritilab.routehub.ui.screens.RouteDetailScreen
import com.pritilab.routehub.ui.screens.SearchScreen

private data class Tab(val route: String, val label: String, val icon: ImageVector)

private val TABS = listOf(
    Tab("home", "Маршруты", Icons.Filled.Home),
    Tab("search", "Поиск", Icons.Filled.Search),
    Tab("map", "Карта", Icons.Filled.Place),
    Tab("feed", "Лента", Icons.AutoMirrored.Filled.List),
    Tab("profile", "Профиль", Icons.Filled.Person),
)

@Composable
fun AppNav() {
    val nav: NavHostController = rememberNavController()
    val app = LocalContext.current.applicationContext as RouteHubApp

    // Restore session from the stored token once at startup.
    LaunchedEffect(Unit) {
        try {
            app.session.refreshMe()
        } catch (_: Exception) {
            // offline start is fine — screens handle their own errors
        }
    }

    val backStack by nav.currentBackStackEntryAsState()
    val currentRoute = backStack?.destination?.route

    Scaffold(
        bottomBar = {
            NavigationBar {
                TABS.forEach { tab ->
                    NavigationBarItem(
                        selected = currentRoute == tab.route,
                        onClick = {
                            nav.navigate(tab.route) {
                                popUpTo(nav.graph.startDestinationId) { saveState = true }
                                launchSingleTop = true
                                restoreState = true
                            }
                        },
                        icon = { Icon(tab.icon, contentDescription = tab.label) },
                        label = { Text(tab.label) },
                    )
                }
            }
        },
    ) { padding ->
        NavHost(
            navController = nav,
            startDestination = "home",
            modifier = Modifier.padding(padding),
        ) {
            composable("home") { HomeScreen(nav) }
            composable("search") { SearchScreen(nav) }
            composable("map") { MapScreen(nav) }
            composable("feed") { FeedScreen(nav) }
            composable("profile") { ProfileScreen(nav, username = null) }
            composable("login") { LoginScreen(nav) }
            composable("poi/{id}") { entry ->
                PoiDetailScreen(nav, entry.arguments?.getString("id").orEmpty())
            }
            composable("route/{id}") { entry ->
                RouteDetailScreen(nav, entry.arguments?.getString("id").orEmpty())
            }
            composable("user/{username}") { entry ->
                ProfileScreen(nav, entry.arguments?.getString("username"))
            }
        }
    }
}
