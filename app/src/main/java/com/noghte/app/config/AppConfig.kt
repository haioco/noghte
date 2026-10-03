package com.noghte.app.config

import kotlinx.serialization.Serializable

@Serializable
data class AppConfig(
    val enabled: Boolean = false,
    val trojanUrl: String = "",
    val trojanConfig: TrojanConfig? = null,
    val socksPort: Int = 10808,
    val cachedDomains: List<String> = emptyList(),
    val lastFetchTime: Long = 0,
    val autostart: Boolean = false,
    val saseEnabled: Boolean = false,
    // "off" | "allow" (only selected apps use VPN) | "deny" (selected apps bypass VPN)
    val sasePerAppMode: String = "off",
    val saseSelectedApps: List<String> = emptyList(),
    val saseBlockDomains: List<String> = emptyList(),
    val saseBlockAds: Boolean = false,
    val saseDnsOverHttps: Boolean = false,
    val saseKillSwitch: Boolean = false
)

data class SubscriptionInfo(
    val title: String,
    val planName: String = "",
    val isPaid: Boolean = false,
    val trafficTotalMb: Float,
    val trafficUsedMb: Float,
    val trafficPercent: Float,
    val expiryDate: String
)
