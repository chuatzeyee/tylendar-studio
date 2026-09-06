package com.chuatzeyee.tylendar

import org.junit.Assert.*
import org.junit.Test
import java.time.ZonedDateTime
import kotlinx.serialization.json.*

class StudioLogicTest {
    @Test fun thumbnailsRespectSingaporeEveningAndWeekends() {
        assertEquals("almanac", thumbnailName("almanac", "auto", ZonedDateTime.parse("2026-09-04T10:59:00Z")))
        assertEquals("almanac-dark", thumbnailName("almanac", "auto", ZonedDateTime.parse("2026-09-04T11:00:00Z")))
        assertEquals("almanac-dark-weekend", thumbnailName("almanac", "dark", ZonedDateTime.parse("2026-09-05T04:00:00Z")))
        assertEquals("poem", thumbnailName("poem", "dark"))
    }
    @Test fun wakeRollsAcrossMidnight() {
        val wake = nextWake(ZonedDateTime.parse("2026-09-06T15:59:00Z"))
        assertEquals("00:20", wake.time)
        assertEquals("Tomorrow, in 21m", wake.relative)
        assertEquals("07:30", nextWake(ZonedDateTime.parse("2026-09-06T16:20:00Z")).time)
    }
    @Test fun tracksTheMatchingCommit() {
        val target = RenderRun(12, "completed", "success", "wanted", "main", "push")
        assertEquals(target, matchingRun(listOf(target, target.copy(id = 13, headSha = "other")), 11, "wanted"))
        assertNull(matchingRun(listOf(target), 11, null))
        assertNull(matchingRun(listOf(target.copy(event = "workflow_dispatch")), 12, null))
    }
    @Test fun preservesUnknownSettingsAndPatchesOnlyChanges() {
        val saved = settingsObject(Json.parseToJsonElement("""{"page":"poem","mode":"auto","hotspot":"Studio","future":{"keep":true}}"""))
        val draft = JsonObject(saved + ("page" to JsonPrimitive("flora")))
        assertEquals(buildJsonObject { put("page", "flora") }, settingsPatch(saved, draft))
        assertEquals(saved["future"], validateSettings(draft)["future"])
    }
    @Test(expected = IllegalArgumentException::class) fun rejectsCorruptSettings() { settingsObject(JsonArray(emptyList())) }
    @Test(expected = IllegalArgumentException::class) fun rejectsUnsupportedLabels() { validateSettings(JsonObject(defaultSettings() + ("hotspot" to JsonPrimitive("山水")))) }
    @Test(expected = IllegalArgumentException::class) fun rejectsRepositoryTraversal() { checkedRepository("owner/../secret") }
}
