package com.noghte.app.config

import android.content.Context
import android.content.SharedPreferences
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json

class ConfigManager(context: Context) {

    private val prefs: SharedPreferences =
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE).also {
            migrateLegacyConfig(context, it)
        }

    private val json = Json {
        ignoreUnknownKeys = true
        encodeDefaults = true
        prettyPrint = false
    }

    private val _config = MutableStateFlow(loadConfig())
    val config: StateFlow<AppConfig> = _config.asStateFlow()

    fun updateConfig(transform: (AppConfig) -> AppConfig) {
        val newConfig = transform(_config.value)
        _config.value = newConfig
        saveConfig(newConfig)
    }

    fun getConfig(): AppConfig = _config.value

    private fun loadConfig(): AppConfig {
        val raw = prefs.getString(KEY_CONFIG, null) ?: return AppConfig()
        return try {
            json.decodeFromString<AppConfig>(raw)
        } catch (_: Exception) {
            AppConfig()
        }
    }

    private fun saveConfig(config: AppConfig) {
        val raw = json.encodeToString(config)
        prefs.edit().putString(KEY_CONFIG, raw).apply()
    }

    fun clear() {
        prefs.edit().clear().apply()
        _config.value = AppConfig()
    }

    companion object {
        private const val KEY_CONFIG = "app_config"
        private const val PREFS_NAME = "noghte_config"
        private const val LEGACY_PREFS_NAME = "haio_config"

        /**
         * One-time migration from the legacy HaioBypass config prefs so saved
         * Trojan configs survive the rebrand to Noghte.
         */
        private fun migrateLegacyConfig(context: Context, prefs: SharedPreferences) {
            if (prefs.contains(KEY_CONFIG)) return
            val legacy = context.getSharedPreferences(LEGACY_PREFS_NAME, Context.MODE_PRIVATE)
            legacy.getString(KEY_CONFIG, null)?.let { raw ->
                prefs.edit().putString(KEY_CONFIG, raw).apply()
            }
        }
    }
}
