package com.noghte.app.network.api

import com.noghte.app.NoghtePrefs
import kotlinx.coroutines.runBlocking
import okhttp3.CertificatePinner
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

object ApiClient {

    private const val BASE_URL = "https://haiobypass.haiocloud.com/"

    private var retrofit: Retrofit? = null
    private var accessToken: String? = null

    private val authInterceptor = Interceptor { chain ->
        val original = chain.request()
        val token = accessToken
        if (token.isNullOrBlank()) {
            chain.proceed(original)
        } else {
            val request = original.newBuilder()
                .header("Authorization", "Bearer $token")
                .build()
            chain.proceed(request)
        }
    }

    private val loggingInterceptor = HttpLoggingInterceptor().apply {
        level = HttpLoggingInterceptor.Level.BODY
    }

    // Pin Let's Encrypt intermediates + ISRG roots so LE's ~90-day leaf
    // rotation never breaks the app. Leaf pin kept for current cert.
    private val certificatePinner = CertificatePinner.Builder()
        // current leaf (BE-aware: expires with next LE renewal)
        .add("haiobypass.haiocloud.com", "sha256/wJuF7rJ6WATPff0pYMdEQx42fAFOUIe527IMDpF5e5s=")
        // LE intermediate YE2 (SPKI)
        .add("haiobypass.haiocloud.com", "sha256/s/tdAOmUzd8syaTuqfgGvFcn6DzA5Cmb+Vby1ST+U3Y=")
        // ISRG Root YE (cross-signed) + ISRG Root X2 (ECDSA root)
        .add("haiobypass.haiocloud.com", "sha256/sCkq5UWXjg+7mKu9lMhhYF5bGLsy7VI/UNW3tccdR7w=")
        .add("haiobypass.haiocloud.com", "sha256/diGVwiVYbubAI3RW4hB9xU8e/CH2GnkuvVFZE8zmgzI=")
        .build()

    private val okHttpClient: OkHttpClient by lazy {
        OkHttpClient.Builder()
            .certificatePinner(certificatePinner)
            .addInterceptor(authInterceptor)
            .addInterceptor(loggingInterceptor)
            .connectTimeout(15, TimeUnit.SECONDS)
            .readTimeout(15, TimeUnit.SECONDS)
            .writeTimeout(15, TimeUnit.SECONDS)
            .build()
    }

    fun setAccessToken(token: String?) {
        accessToken = token
    }

    fun getApiService(): NoghteApiService {
        return retrofit?.create(NoghteApiService::class.java) ?: run {
            val newRetrofit = Retrofit.Builder()
                .baseUrl(BASE_URL)
                .client(okHttpClient)
                .addConverterFactory(GsonConverterFactory.create())
                .build()
            retrofit = newRetrofit
            newRetrofit.create(NoghteApiService::class.java)
        }
    }

    fun tryRefreshAccessToken(prefs: NoghtePrefs): String? {
        val refreshToken = prefs.jwtRefreshToken ?: return null
        return runBlocking {
            try {
                val response = getApiService().refreshToken(RefreshRequest(refresh = refreshToken))
                if (response.isSuccessful) {
                    val newAccess = response.body()?.access
                    if (newAccess != null) {
                        prefs.jwtAccessToken = newAccess
                        setAccessToken(newAccess)
                    }
                    newAccess
                } else {
                    null
                }
            } catch (_: Exception) {
                null
            }
        }
    }
}