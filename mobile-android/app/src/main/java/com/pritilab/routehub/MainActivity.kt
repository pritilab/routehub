package com.pritilab.routehub

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import com.pritilab.routehub.ui.AppNav
import com.pritilab.routehub.ui.theme.RouteHubTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            RouteHubTheme {
                AppNav()
            }
        }
    }
}
