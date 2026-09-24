-keepattributes Signature, Exceptions, InnerClasses, EnclosingMethod
-keepattributes *Annotation*
-keepattributes SourceFile,LineNumberTable
-renamesourcefileattribute SourceFile
-keep public class * extends java.lang.Exception

# Retrofit
-dontwarn retrofit2.**
-keep class retrofit2.** { *; }
-keepclassmembers,allowshrinking,allowobfuscation interface * {
    @retrofit2.http.* <methods>;
}

# Keep API service interface methods with their generic signatures
# Kotlin suspend functions need explicit signature preservation
-keep,allowobfuscation,allowshrinking class com.noghte.app.network.api.NoghteApiService {
    <methods>;
}

# Kotlin reflect + generic signatures — needed by Retrofit type resolution
-keep class kotlin.Metadata { *; }
-keep class kotlin.reflect.full.** { *; }
-keep class kotlin.reflect.jvm.** { *; }
-keep class kotlin.coroutines.Continuation
-dontwarn javax.annotation.**
-dontwarn kotlin.Unit
-dontwarn retrofit2.KotlinExtensions
-dontwarn retrofit2.KotlinExtensions$*

# Gson
-keep class com.google.gson.** { *; }
-keep class * implements com.google.gson.TypeAdapterFactory
-keep class * implements com.google.gson.JsonSerializer
-keep class * implements com.google.gson.JsonDeserializer
-keepclassmembers,allowobfuscation class * {
  @com.google.gson.annotations.SerializedName <fields>;
}

# Keep API models
-keep class com.noghte.app.network.api.** { *; }
-keepclassmembers class com.noghte.app.network.api.** { *; }

# Kotlinx serialization
-keepattributes *Annotation*, InnerClasses
-dontnote kotlinx.serialization.AnnotationsKt
-keepclassmembers class kotlinx.serialization.json.** { *** Companion; }
-keepclasseswithmembers class kotlinx.serialization.json.** {
    kotlinx.serialization.KSerializer serializer(...);
}
-keep,includedescriptorclasses class com.noghte.app.**$$serializer { *; }
-keepclassmembers class com.noghte.app.** {
    *** Companion;
}
-keepclasseswithmembers class com.noghte.app.** {
    kotlinx.serialization.KSerializer serializer(...);
}

# OkHttp
-dontwarn okhttp3.**
-dontwarn okio.**
-keep class okhttp3.** { *; }
-keep interface okhttp3.** { *; }
-keep class okio.** { *; }

# Keep raw resources
-keep class com.noghte.app.R$raw { *; }

# Kotlin reflection — needed for Retrofit type tokens
-keep class kotlin.Metadata { *; }
-keepclassmembers class kotlin.Metadata { *; }