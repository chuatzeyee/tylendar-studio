package com.chuatzeyee.tylendar

import android.util.Base64
import kotlinx.coroutines.delay
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.serialization.json.*
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.IOException
import java.util.concurrent.TimeUnit
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException

class GithubException(message: String, val status: Int = 0) : Exception(message)
data class RepoFile(val value: JsonObject, val sha: String)
data class SavedSettings(val value: JsonObject, val commit: String)
class Github(repo: String, private val token: String) {
    val repository = checkedRepository(repo)
    val raw = "https://raw.githubusercontent.com/$repository/main"
    val portal = "https://${repository.substringBefore('/')}.github.io/${repository.substringAfter('/')}/"
    private val api = "https://api.github.com/repos/$repository"
    private val client = OkHttpClient.Builder().connectTimeout(15, TimeUnit.SECONDS).callTimeout(30, TimeUnit.SECONDS).build()
    private val json = Json { prettyPrint = true }

    private suspend fun request(path: String, method: String = "GET", body: JsonObject? = null): JsonElement {
        val builder = Request.Builder().url(api + path)
            .header("Accept", "application/vnd.github+json").header("X-GitHub-Api-Version", "2022-11-28")
            .header("Authorization", "Bearer $token")
        if (method != "GET") builder.method(method, (body?.toString() ?: "").toRequestBody("application/json".toMediaType()))
        val call = client.newCall(builder.build())
        return suspendCancellableCoroutine { continuation ->
            continuation.invokeOnCancellation { call.cancel() }
            call.enqueue(object : Callback {
                override fun onFailure(call: Call, e: IOException) {
                    if (continuation.isActive) continuation.resumeWithException(GithubException("Could not reach GitHub. Check your connection and retry."))
                }
                override fun onResponse(call: Call, response: Response) {
                    response.use { res ->
                        try {
                            if (!res.isSuccessful) {
                                val message = when {
                                    res.code == 429 || res.header("x-ratelimit-remaining") == "0" -> "GitHub is limiting requests. Wait a few minutes before retrying."
                                    res.code == 401 -> "GitHub rejected the token. Reconnect with a valid token."
                                    res.code == 403 -> "GitHub denied access. Check Contents and Actions permissions."
                                    res.code == 404 -> "Repository or file not found. Check the repository, main branch, and token access."
                                    res.code == 409 -> "Settings changed on GitHub while saving. Please try again."
                                    else -> "GitHub returned ${res.code}. Check the render workflow and try again."
                                }
                                throw GithubException(message, res.code)
                            }
                            val result = if (res.code == 204) JsonNull else json.parseToJsonElement(res.body.string())
                            if (continuation.isActive) continuation.resume(result)
                        } catch (e: Exception) { if (continuation.isActive) continuation.resumeWithException(e) }
                    }
                }
            })
        }
    }
    suspend fun connect(): RepoFile {
        val repo = request("").jsonObject
        require(repo["permissions"]?.jsonObject?.get("push")?.jsonPrimitive?.booleanOrNull == true) { "This token’s account cannot write to the repository." }
        val file = settings()
        runs()
        return file
    }
    suspend fun settings(): RepoFile {
        val file = request("/contents/generator/settings.json?ref=main").jsonObject
        val content = file.text("content")
        require(content.isNotEmpty() && file.text("sha").isNotEmpty()) { "GitHub returned an incomplete settings file." }
        return RepoFile(settingsObject(json.parseToJsonElement(String(Base64.decode(content, Base64.DEFAULT), Charsets.UTF_8))), file.text("sha"))
    }
    suspend fun save(patch: JsonObject): SavedSettings {
        repeat(4) { attempt ->
            if (attempt > 0) delay(attempt * 700L)
            val current = settings()
            val updated = JsonObject(current.value + patch)
            val encoded = Base64.encodeToString((json.encodeToString(JsonObject.serializer(), updated) + "\n").toByteArray(Charsets.UTF_8), Base64.NO_WRAP)
            try {
                val result = request("/contents/generator/settings.json", "PUT", buildJsonObject {
                    put("message", "studio: update frame settings"); put("content", encoded); put("sha", current.sha); put("branch", "main")
                }).jsonObject
                val commit = result["commit"]?.jsonObject?.text("sha").orEmpty()
                require(commit.isNotEmpty()) { "Settings saved without a render reference. Refresh status before trying again." }
                return SavedSettings(updated, commit)
            } catch (e: GithubException) { if (e.status != 409 || attempt == 3) throw e }
        }
        throw GithubException("Settings kept changing during the save. Try again.")
    }
    suspend fun runs(): List<RenderRun> = request("/actions/workflows/render.yml/runs?per_page=20&branch=main").jsonObject["workflow_runs"]?.jsonArray.orEmpty().map {
        val run = it.jsonObject
        RenderRun(run["id"]!!.jsonPrimitive.long, run.text("status"), run.text("conclusion"), run.text("head_sha"), run.text("head_branch"), run.text("event"))
    }
    suspend fun preview(): ByteArray {
        val file = request("/contents/output/preview.png?ref=main").jsonObject
        require(file.text("content").isNotEmpty()) { "The rendered preview is unavailable or too large. Open it on GitHub." }
        return Base64.decode(file.text("content"), Base64.DEFAULT)
    }
    suspend fun dispatch(mode: String = "auto") {
        require(mode in listOf("auto", "light", "dark")) { "Choose a valid one-time edition." }
        request("/actions/workflows/render.yml/dispatches", "POST", buildJsonObject { put("ref", "main"); put("inputs", buildJsonObject { put("mode", mode) }) })
    }
}
