package com.pritilab.routehub.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

// Green accent to match the web frontend.
private val Green = Color(0xFF16A34A)
private val GreenDark = Color(0xFF15803D)

private val LightColors = lightColorScheme(
    primary = Green,
    secondary = GreenDark,
    tertiary = Color(0xFF0EA5E9),
)

private val DarkColors = darkColorScheme(
    primary = Color(0xFF4ADE80),
    secondary = Color(0xFF86EFAC),
    tertiary = Color(0xFF38BDF8),
)

@Composable
fun RouteHubTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = if (isSystemInDarkTheme()) DarkColors else LightColors,
        content = content,
    )
}
