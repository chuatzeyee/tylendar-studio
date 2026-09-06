package com.chuatzeyee.tylendar

import java.time.ZonedDateTime
import java.time.ZoneId
import kotlinx.serialization.json.*

data class Print(val id: String, val name: String, val zh: String, val group: String, val title: String, val description: String)
val PRINTS = listOf(
    Print("landscape", "Ink landscape", "山水", "Nature", "A little room\nto wander.", "Date-seeded mountains, quiet water, and a new horizon each day."),
    Print("almanac", "Daily almanac", "黃曆", "Daily", "Every day,\na fresh page.", "Lunar dates, seasonal markers, and the rhythm of the everyday."),
    Print("poem", "A daily poem", "詩箋", "Daily", "Make space\nfor a few words.", "A Tang poem from a collection of 135, with an English reading close at hand."),
    Print("character", "One character", "一字", "Daily", "One character.\nA whole world.", "A generous study of a Chinese character, its meaning, and the words it becomes."),
    Print("flora", "Seasonal flora", "四君子", "Nature", "Let the season\ncome inside.", "Plum, orchid, bamboo, and chrysanthemum, drawn afresh as the year unfolds."),
    Print("weather", "Island weather", "天氣", "Daily", "A feeling\nfor the day.", "Singapore’s outlook, temperatures, air quality, and the chance of rain."),
    Print("month", "The month", "月曆", "Calendar", "A wider view\nof what’s ahead.", "Lunar dates, Singapore holidays, and calendar event markers."),
    Print("year", "Year in progress", "歲時", "Calendar", "Watch a year\nbecome a life.", "One square for every day. A record of time passed and time still to come."),
    Print("photo", "Your photographs", "相片", "Personal", "Keep something\nclose to you.", "Your photographs, translated into the four colors of e-paper."),
    Print("joke", "Local vocabulary", "俚語", "Personal", "A small dose\nof local color.", "A playful dictionary of Singlish profanity. Contains strong language."),
)
val GROUPS = listOf("All prints", "Daily", "Nature", "Calendar", "Personal")
data class PageOption(val key: String, val label: String, val values: List<String>, val names: List<String>)
val PAGE_OPTIONS = mapOf(
    "landscape" to listOf(PageOption("landscape_scenery", "The scenery", listOf("lake", "gorge", "islands", "night"), listOf("Quiet lake", "Gorge", "Islands", "Night sky"))),
    "poem" to listOf(PageOption("poem_lang", "On the print", listOf("cn", "en"), listOf("Chinese", "English"))),
    "month" to listOf(PageOption("month_week_start", "Week begins", listOf("monday", "sunday"), listOf("Monday", "Sunday"))),
    "year" to listOf(
        PageOption("year_lang", "Language", listOf("bilingual", "en", "cn"), listOf("Bilingual", "English", "Chinese")),
        PageOption("year_footer", "At the foot of the page", listOf("holidays", "event", "weather"), listOf("Holiday", "Event", "Weather"))),
    "flora" to listOf(PageOption("flora_plant", "The plant", listOf("season", "plum", "orchid", "bamboo", "chrysanthemum"), listOf("Seasonal", "Plum", "Orchid", "Bamboo", "Chrysanthemum"))),
    "joke" to listOf(PageOption("joke_word", "The word", listOf("daily", "jibai", "kanina", "lanjiao", "nabei", "jiaksai", "sibei", "walao", "siao"), listOf("Daily", "Ji bai", "Kan ni na", "Lan jiao", "Na beh", "Jiak sai", "Si beh", "Wa lao", "Siao"))),
)
val SGT: ZoneId = ZoneId.of("Asia/Singapore")
fun defaultSettings() = buildJsonObject { put("page", "landscape"); put("mode", "auto"); put("hotspot", "Tylendar") }
fun JsonObject.text(key: String, fallback: String = "") = (this[key] as? JsonPrimitive)?.contentOrNull ?: fallback
fun settingsObject(element: JsonElement): JsonObject {
    require(element is JsonObject) { "Settings must be a JSON object. Correct generator/settings.json before saving." }
    return JsonObject(element.toMutableMap().apply {
        if (element.text("page") !in PRINTS.map { it.id }) put("page", JsonPrimitive("almanac"))
        if (element.text("mode") !in listOf("auto", "light", "dark")) put("mode", JsonPrimitive("auto"))
        if ((element["hotspot"] as? JsonPrimitive)?.isString != true) put("hotspot", JsonPrimitive("Tylendar"))
    })
}
fun validateSettings(settings: JsonObject): JsonObject {
    require(settings.text("page") in PRINTS.map { it.id }) { "Choose a print from the collection." }
    require(settings.text("mode") in listOf("auto", "light", "dark")) { "Choose a valid edition." }
    val label = settings.text("hotspot").trim()
    require(label.length in 1..24 && label.all { it.code in 32..126 }) { "Use 1–24 letters, numbers, spaces, or standard English punctuation." }
    PAGE_OPTIONS.values.flatten().forEach { o -> require(settings[o.key] == null || settings.text(o.key) in o.values) { "Choose a valid ${o.label.lowercase()}." } }
    return JsonObject(settings.toMutableMap().apply { put("hotspot", JsonPrimitive(label)) })
}
fun settingsPatch(saved: JsonObject, draft: JsonObject) = JsonObject(draft.filter { (key, value) -> saved[key] != value })
fun checkedRepository(value: String): String {
    val repo = value.trim()
    require(Regex("^[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9_.-]{1,100}$").matches(repo) && repo.substringAfter('/') !in listOf(".", "..")) { "Use owner/repository, for example chuatzeyee/Tylendar." }
    return repo
}
fun thumbnailName(page: String, mode: String, now: ZonedDateTime = ZonedDateTime.now(SGT)): String {
    val time = now.withZoneSameInstant(SGT)
    val dark = mode == "dark" || (mode == "auto" && time.hour >= 19)
    return if (page == "almanac" && dark) "almanac-dark" + if (time.dayOfWeek.value >= 6) "-weekend" else "" else page
}
data class Wake(val time: String, val relative: String)
fun nextWake(now: ZonedDateTime = ZonedDateTime.now(SGT)): Wake {
    val time = now.withZoneSameInstant(SGT)
    val minute = time.hour * 60 + time.minute
    val next = listOf(20, 450, 780, 1140).firstOrNull { it > minute } ?: 1460
    val d = next - minute
    return Wake("%02d:%02d".format((next % 1440) / 60, next % 60), (if (next >= 1440) "Tomorrow · " else "") + if (d >= 60) "in ${d / 60}h ${d % 60}m" else "in ${d}m")
}
data class RenderRun(val id: Long, val status: String, val conclusion: String, val headSha: String, val branch: String, val event: String)
fun matchingRun(runs: List<RenderRun>, baseline: Long, sha: String?) = runs.filter { it.id > baseline && it.branch == "main" && if (sha != null) it.headSha == sha else it.event == "workflow_dispatch" }.maxByOrNull { it.id }
