package com.noghte.app.billing

import android.content.Context
// import android.util.Log
// import androidx.activity.result.ActivityResultRegistry
import com.noghte.app.NoghtePrefs
import com.noghte.app.config.ConfigManager
// import com.noghte.app.network.api.ApiClient
// import com.noghte.app.network.api.CreatePaymentRequest
import com.noghte.app.network.api.Plan
// import com.noghte.app.network.api.VerifyPaymentRequest
// import ir.cafebazaar.poolakey.Connection
// import ir.cafebazaar.poolakey.Payment
// import ir.cafebazaar.poolakey.config.PaymentConfiguration
// import ir.cafebazaar.poolakey.config.SecurityCheck
// import ir.cafebazaar.poolakey.entity.PurchaseInfo
// import ir.cafebazaar.poolakey.entity.SkuDetails
// import ir.cafebazaar.poolakey.request.PurchaseRequest
// import kotlinx.coroutines.CoroutineScope
// import kotlinx.coroutines.Dispatchers
// import kotlinx.coroutines.launch

/**
 * DISABLED — Cafe Bazar (Poolakey) in-app billing.
 * All methods are stubs returning null/no-op.
 * Kept for reference in case Cafe Bazar is re-enabled.
 */
class BazaarPayHelper(
    private val context: Context,
    private val prefs: NoghtePrefs,
    private val configManager: ConfigManager,
    private val onPurchaseSuccess: (planName: String) -> Unit,
    private val onPurchaseFailed: (message: String) -> Unit,
    private val onShowSnackbar: (String) -> Unit
) {
    fun connect() {}
    fun disconnect() {}

    fun launchPurchase(registry: Any? = null, plan: Plan?) {
        onShowSnackbar("Cafe Bazar payment is disabled. Use balance purchase instead.")
    }
}
