package com.chuatzeyee.tylendar

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

private val Context.studioStore by preferencesDataStore(name = "studio")
data class Credentials(val repository: String, val token: String)
object TokenStore {
    private val REPO = stringPreferencesKey("repository")
    private val TOKEN = stringPreferencesKey("encrypted_token")
    private const val ALIAS = "tylendar-studio-token"
    private fun key(): SecretKey {
        val store = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        (store.getKey(ALIAS, null) as? SecretKey)?.let { return it }
        return KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore").apply {
            init(KeyGenParameterSpec.Builder(ALIAS, KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).build())
        }.generateKey()
    }
    suspend fun read(context: Context): Credentials? = withContext(Dispatchers.IO) {
        val stored = context.studioStore.data.first()
        val encrypted = stored[TOKEN] ?: return@withContext null
        val repository = stored[REPO] ?: return@withContext null
        val parts = encrypted.split(':')
        require(parts.size == 2) { "Saved connection could not be read. Reconnect to your frame." }
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.DECRYPT_MODE, key(), GCMParameterSpec(128, Base64.decode(parts[0], Base64.NO_WRAP)))
        Credentials(repository, String(cipher.doFinal(Base64.decode(parts[1], Base64.NO_WRAP)), Charsets.UTF_8))
    }
    suspend fun save(context: Context, value: Credentials?) = withContext(Dispatchers.IO) {
        if (value == null) { context.studioStore.edit { it.remove(TOKEN); it.remove(REPO) }; return@withContext }
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, key())
        val encrypted = Base64.encodeToString(cipher.iv, Base64.NO_WRAP) + ":" + Base64.encodeToString(cipher.doFinal(value.token.toByteArray(Charsets.UTF_8)), Base64.NO_WRAP)
        context.studioStore.edit { it[REPO] = value.repository; it[TOKEN] = encrypted }
    }
}
