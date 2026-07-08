package com.pritilab.routehub

import android.app.Application
import com.pritilab.routehub.data.RouteHubApi
import com.pritilab.routehub.data.Session
import com.pritilab.routehub.data.TokenStore
import com.pritilab.routehub.data.buildApi
import org.osmdroid.config.Configuration

class RouteHubApp : Application() {

    lateinit var tokenStore: TokenStore
        private set
    lateinit var api: RouteHubApi
        private set
    lateinit var session: Session
        private set

    override fun onCreate() {
        super.onCreate()
        // osmdroid requires a distinct user agent for OSM tile policy compliance.
        Configuration.getInstance().userAgentValue = packageName

        tokenStore = TokenStore(this).apply { loadBlocking() }
        api = buildApi(BuildConfig.API_BASE_URL) { tokenStore.cached }
        session = Session(api, tokenStore)
    }
}
