package com.chuatzeyee.tylendar

import android.app.Application
import androidx.compose.runtime.*
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.*
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.serialization.json.*
import java.time.LocalDate

class AppViewModel(app: Application) : AndroidViewModel(app) {
    var saved by mutableStateOf(defaultSettings()); private set
    var draft by mutableStateOf(saved); private set
    var github by mutableStateOf<Github?>(null); private set
    var busy by mutableStateOf(false); private set
    var rendering by mutableStateOf(false); private set
    var status by mutableStateOf("You’re exploring the demo. Nothing is sent to a frame."); private set
    var error by mutableStateOf<String?>(null); private set
    var poem by mutableStateOf<JsonObject?>(null); private set
    var latestImage by mutableStateOf<ByteArray?>(null); private set
    private val mutations = Mutex()
    private var work: Job? = null
    private var watch: Job? = null
    private var operationId = 0
    private var watchId = 0
    val selected get() = PRINTS.first { it.id == draft.text("page") }
    val dirty get() = settingsPatch(saved, draft).isNotEmpty()
    val demo get() = github == null
    fun image(page: String = selected.id) = "file:///android_asset/previews/${thumbnailName(page, draft.text("mode"))}.png"

    init {
        busy = true
        val initialId = operationId
        work = viewModelScope.launch {
            try {
                TokenStore.read(getApplication())?.let { credentials ->
                    busy = true
                    status = "Restoring the saved connection…"
                    val candidate = Github(credentials.repository, credentials.token)
                    val file = candidate.connect()
                    github = candidate; saved = file.value; draft = saved
                    status = "Connected to ${candidate.repository}."
                }
            } catch (e: CancellationException) { throw e }
            catch (e: Exception) { status = "Demo collection ready."; error = "Could not restore the connection. Reconnect when ready. ${e.message.orEmpty()}" }
            finally { if (initialId == operationId) busy = false }
        }
        loadPoem()
    }
    fun clearError() { error = null }
    fun loadLatestPreview() = operation { latestImage = null; latestImage = github?.preview() }
    fun select(page: String) { if (!busy && PRINTS.any { it.id == page }) setDraft("page", page) }
    fun setDraft(key: String, value: String) { if (!busy) draft = JsonObject(draft.toMutableMap().apply { put(key, JsonPrimitive(value)) }) }
    fun discard() { if (!busy) { draft = saved; error = null; status = "Draft discarded. Saved settings are unchanged." } }
    fun setLabel(label: String): Boolean {
        return try { val validated = validateSettings(JsonObject(draft + ("hotspot" to JsonPrimitive(label)))); if (!busy) draft = validated; true }
        catch (e: IllegalArgumentException) { error = e.message; false }
    }
    private fun operation(block: suspend () -> Unit) {
        if (busy) return
        val id = ++operationId
        busy = true; error = null
        work = viewModelScope.launch {
            try { mutations.withLock { block() } }
            catch (e: CancellationException) { throw e }
            catch (e: Exception) { if (id == operationId) error = e.message ?: "Something went wrong. Please retry." }
            finally { if (id == operationId) busy = false }
        }
    }
    fun connect(repo: String, token: String, onConnected: () -> Unit) = operation {
        require(Regex("^(github_pat_|ghp_)[A-Za-z0-9_]{20,}$").matches(token.trim())) { "Enter a valid GitHub personal access token." }
        val candidate = Github(repo, token.trim())
        val file = candidate.connect()
        TokenStore.save(getApplication(), Credentials(candidate.repository, token.trim()))
        watch?.cancel(); rendering = false
        github = candidate; saved = file.value; draft = saved
        status = "Connected to ${candidate.repository}. Apply a draft when you’re ready."
        onConnected()
    }
    fun disconnect() {
        operationId++; watchId++
        work?.cancel(); watch?.cancel(); rendering = false; busy = false; github = null
        saved = defaultSettings(); draft = saved; error = null
        latestImage = null
        status = "Disconnected. You’re back in the local demo."
        viewModelScope.launch {
            try { TokenStore.save(getApplication(), null) }
            catch (e: CancellationException) { throw e }
            catch (e: Exception) { error = "Could not clear the stored connection. ${e.message.orEmpty()}" }
        }
    }
    fun apply() = operation {
        val value = validateSettings(draft)
        val patch = settingsPatch(saved, value)
        if (patch.isEmpty()) return@operation
        val gh = github
        if (gh == null) { saved = value; draft = saved; status = "Selection saved in this demo only. No frame or repository was changed."; return@operation }
        val baseline = gh.runs().maxOfOrNull { it.id } ?: 0
        status = "Saving your selection…"
        val result = gh.save(patch)
        saved = result.value; draft = saved
        status = "Settings saved. Waiting for the matching render…"
        watchRender(gh, baseline, result.commit)
    }
    fun refresh() = operation {
        val gh = github
        if (gh == null) { status = "Demo collection is ready. Connect a repository to check render status."; return@operation }
        val patch = settingsPatch(saved, draft)
        saved = gh.settings().value; draft = JsonObject(saved + patch)
        val run = gh.runs().maxByOrNull { it.id }
        status = when {
            run == null -> "No render has run yet."
            run.status != "completed" -> "A render is in progress."
            run.conclusion == "success" -> "Latest render succeeded. The frame fetches it at its next wake."
            else -> "Latest render: ${run.conclusion.ifBlank { "unknown" }}. Try rendering again."
        }
    }
    fun renderSaved(mode: String = "auto") = operation {
        val gh = github
        if (gh == null) { status = "Demo preview ready. No workflow was started."; return@operation }
        val baseline = gh.runs().maxOfOrNull { it.id } ?: 0
        gh.dispatch(mode); status = "Render requested for saved settings. Your draft is not included."
        watchRender(gh, baseline, null)
    }
    private fun watchRender(gh: Github, baseline: Long, sha: String?) {
        val id = ++watchId
        watch?.cancel()
        watch = viewModelScope.launch {
            rendering = true
            try {
                val complete = withTimeoutOrNull(8 * 60_000L) {
                    while (true) {
                        delay(4000)
                        val run = matchingRun(gh.runs(), baseline, sha) ?: continue
                        if (run.status != "completed") { status = "Rendering your saved settings…"; continue }
                        if (run.conclusion != "success") throw GithubException("Render ${run.conclusion.ifBlank { "failed" }}. Settings are saved; try rendering again.")
                        status = "Render complete. The frame fetches the image at its next scheduled wake."
                        break
                    }
                    true
                }
                if (complete == null) status = "The render is taking longer than expected. Refresh status to check again."
            } catch (e: CancellationException) { throw e }
            catch (e: Exception) { error = e.message }
            finally { if (id == watchId) rendering = false }
        }
    }
    fun loadPoem() {
        viewModelScope.launch {
            try {
                poem = withContext(Dispatchers.IO) {
                    val text = getApplication<Application>().assets.open("poems.json").bufferedReader().use { it.readText() }
                    val poems = Json.parseToJsonElement(text).jsonArray
                    if (poems.isEmpty()) null else poems[((LocalDate.now(SGT).toEpochDay() + 719163L) % poems.size).toInt()].jsonObject
                }
            } catch (e: CancellationException) { throw e }
            catch (e: Exception) { error = "The bundled poem collection could not be read." }
        }
    }
}
