plugins {
    id("com.android.application") version "9.1.1" apply false
    // Must match the KGP version embedded in AGP's built-in Kotlin (2.2.10 for AGP 9.1).
    id("org.jetbrains.kotlin.plugin.compose") version "2.2.10" apply false
}
