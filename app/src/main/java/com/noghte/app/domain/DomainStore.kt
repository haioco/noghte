package com.noghte.app.domain

import android.content.Context
import android.content.SharedPreferences
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json

class DomainStore(context: Context) {

    private val prefs: SharedPreferences =
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE).also {
            // One-time migration from legacy HaioBypass domain cache.
            if (!it.contains(KEY_DOMAINS)) {
                val legacy = context.getSharedPreferences(
                    LEGACY_PREFS_NAME,
                    Context.MODE_PRIVATE
                )
                legacy.getString(KEY_DOMAINS, null)?.let { raw ->
                    it.edit().putString(KEY_DOMAINS, raw).apply()
                }
                it.edit().putLong(
                    KEY_LAST_FETCH,
                    legacy.getLong(KEY_LAST_FETCH, 0)
                ).apply()
            }
        }

    private val router = DomainRouter()

    private val _domainCount = MutableStateFlow(0)
    val domainCount: StateFlow<Int> = _domainCount.asStateFlow()

    private val _lastFetchTime = MutableStateFlow(0L)
    val lastFetchTime: StateFlow<Long> = _lastFetchTime.asStateFlow()

    private val _domains = MutableStateFlow<List<String>>(emptyList())
    val domains: StateFlow<List<String>> = _domains.asStateFlow()

    init {
        val cached = loadCachedDomains()
        if (cached.isNotEmpty()) {
            router.setDomains(cached)
            _domainCount.value = router.getDomainCount()
            _domains.value = cached
        }
        _lastFetchTime.value = prefs.getLong(KEY_LAST_FETCH, 0)
    }

    fun setDomains(domains: List<String>) {
        router.setDomains(domains)
        _domainCount.value = router.getDomainCount()
        _domains.value = domains
        saveCachedDomains(domains)
        _lastFetchTime.value = System.currentTimeMillis()
        prefs.edit().putLong(KEY_LAST_FETCH, _lastFetchTime.value).apply()
    }

    fun addDomain(domain: String) {
        val current = _domains.value.toMutableList()
        val normalized = domain.trim().lowercase()
        if (normalized.isNotEmpty() && !current.contains(normalized)) {
            current.add(normalized)
            setDomains(current)
        }
    }

    fun removeDomain(domain: String) {
        val current = _domains.value.toMutableList()
        if (current.remove(domain)) {
            setDomains(current)
        }
    }

    fun shouldProxy(host: String): Boolean = router.shouldProxy(host)

    fun getDomains(): List<String> = _domains.value

    fun getDomainCount(): Int = router.getDomainCount()

    private fun loadCachedDomains(): List<String> {
        val raw = prefs.getString(KEY_DOMAINS, null) ?: return emptyList()
        return try {
            Json.decodeFromString<List<String>>(raw)
        } catch (_: Exception) {
            emptyList()
        }
    }

    private fun saveCachedDomains(domains: List<String>) {
        val raw = Json.encodeToString(domains)
        prefs.edit().putString(KEY_DOMAINS, raw).apply()
    }

    companion object {
        private const val PREFS_NAME = "noghte_domains"
        private const val LEGACY_PREFS_NAME = "haio_domains"
        private const val KEY_DOMAINS = "cached_domains"
        private const val KEY_LAST_FETCH = "last_fetch_time"
    }
}
