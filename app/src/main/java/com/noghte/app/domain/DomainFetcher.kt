package com.noghte.app.domain

import android.content.Context
import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.CertificatePinner
import okhttp3.OkHttpClient
import okhttp3.Request
import java.util.concurrent.TimeUnit

class DomainFetcher {

    constructor()
    constructor(@Suppress("UNUSED_PARAMETER") context: Context)

    // Pin only haiocloud hosts we control. raw.githubusercontent.com is a
    // public mirror we do not operate — pinning it would break on GitHub's
    // own certificate rotation; fail-closed only for our own infra.
    private val certificatePinner = CertificatePinner.Builder()
        // current leaf (rotates ~every 60-90 days)
        .add("tools.haiocloud.com", "sha256/YXxUe75ka0ejzx1hmUAw1a6dTt0cr/WGZmAzlwOjke4=")
        // LE intermediate YR2 (SPKI) + ISRG Root YR (cross-signed)
        .add("tools.haiocloud.com", "sha256/nWN7PSep5XDQdge5zK24CnCRXHr3KvzhKEGxsdqCX9E=")
        .add("tools.haiocloud.com", "sha256/fk6IOKit1ild5647BH06ujSIq5XbCgqlbYl6ANhhi88=")
        // ISRG Root X2 ECDSA root (covers both YE*/YR* chains)
        .add("tools.haiocloud.com", "sha256/diGVwiVYbubAI3RW4hB9xU8e/CH2GnkuvVFZE8zmgzI=")
        .build()

    private val client = OkHttpClient.Builder()
        .certificatePinner(certificatePinner)
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(10, TimeUnit.SECONDS)
        .build()

    suspend fun fetch(): List<String> = withContext(Dispatchers.IO) {
        // Source of truth is the remote domains.txt. Everything else goes direct.
        val merged = LinkedHashSet<String>()

        for (url in REMOTE_URLS) {
            try {
                val request = Request.Builder()
                    .url(url)
                    .header("Cache-Control", "no-cache")
                    .header("Pragma", "no-cache")
                    .build()

                val response = client.newCall(request).execute()
                if (!response.isSuccessful) {
                    response.close()
                    continue
                }

                val body = response.body?.string() ?: continue
                merged.addAll(parseDomainText(body))
            } catch (_: Exception) {
                continue
            }
        }

        merged.toList().also {
            Log.d(TAG, "fetch complete: ${it.size} domains from remote sources")
        }
    }

    private fun parseDomainText(text: String): List<String> {
        val seen = mutableSetOf<String>()
        val result = mutableListOf<String>()

        text.lines().forEach { line ->
            val trimmed = line.trim().lowercase()
            if (trimmed.isEmpty()) return@forEach
            if (trimmed.startsWith("#")) return@forEach
            if (trimmed.contains("/") || trimmed.contains(":") || trimmed.contains(" ")) return@forEach
            if (!trimmed.contains(".")) return@forEach

            if (isDnsInfrastructure(trimmed)) return@forEach

            if (seen.add(trimmed)) {
                result.add(trimmed)
            }
        }

        return result
    }

    private val dnsPrefixes = setOf("ns1.", "ns2.", "ns3.", "ns4.", "ns5.")
    private val dnsSuffixes = setOf("-hostmaster.", "dns-admin.", "hostmaster.", "dns1.")

    private fun isDnsInfrastructure(domain: String): Boolean {
        if (dnsPrefixes.any { domain.startsWith(it) }) return true
        if (dnsSuffixes.any { domain.contains(it) }) return true
        if (domain.endsWith("nsone.net")) return true
        return false
    }

    companion object {
        private const val TAG = "DomainFetcher"
        private val REMOTE_URLS = listOf(
            "https://tools.haiocloud.com/domains.txt",
            "https://raw.githubusercontent.com/haiocloud/bypass-domains/main/domains.txt"
        )
    }
}
