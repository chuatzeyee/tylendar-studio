package com.chuatzeyee.tylendar.ui

import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.*
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.focus.*
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.key.*
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.semantics.*
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.*
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import coil3.compose.AsyncImage
import com.chuatzeyee.tylendar.*
import kotlinx.coroutines.delay
import kotlinx.serialization.json.*

@Composable fun App(vm: AppViewModel) {
    var group by rememberSaveable { mutableStateOf("All prints") }
    var dialog by rememberSaveable { mutableStateOf<String?>(null) }
    var enlarged by remember { mutableStateOf<String?>(null) }
    var wake by remember { mutableStateOf(nextWake()) }
    val focus = remember { FocusRequester() }
    val uri = LocalUriHandler.current
    val showDialog: (String) -> Unit = { name -> if (name == "poem") vm.loadPoem(); dialog = name }
    LaunchedEffect(Unit) { focus.requestFocus(); while (true) { wake = nextWake(); delay(30000) } }
    Column(Modifier.fillMaxSize().background(Paper).safeDrawingPadding().focusRequester(focus).focusable().onKeyEvent { e ->
        if (e.type != KeyEventType.KeyUp || vm.busy) false else {
            val page = mapOf(Key.A to "almanac", Key.P to "poem", Key.C to "character", Key.L to "landscape", Key.W to "weather", Key.M to "month", Key.Y to "year", Key.J to "joke", Key.O to "photo", Key.F to "flora")[e.key]
            when { page != null -> { vm.select(page); true }; e.key == Key.R -> { vm.renderSaved(); true }; else -> false }
        }
    }) {
        Row(Modifier.fillMaxWidth().padding(horizontal = 20.dp, vertical = 12.dp), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.SpaceBetween) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("泰\n曆", color = Mat, fontSize = 13.sp, lineHeight = 16.sp, modifier = Modifier.background(Seal).padding(horizontal = 8.dp, vertical = 5.dp))
                Column(Modifier.padding(start = 10.dp)) { Text("Tylendar", fontFamily = Canela, fontSize = 26.sp); Text("THE FRAME STUDIO", style = Eyebrow.copy(fontSize = 8.sp), color = Muted) }
            }
            TextButton(onClick = { dialog = "connect" }) { Text(if (vm.demo) "Demo collection ↗" else "Connected ↗", fontSize = 11.sp) }
        }
        HorizontalDivider(color = Hairline)
        BoxWithConstraints(Modifier.fillMaxWidth().weight(1f)) {
            val wide = maxWidth >= 560.dp || (maxWidth >= 430.dp && maxWidth > maxHeight)
            val artHeight = if (wide) (maxHeight * .73f).coerceIn(260.dp, 430.dp) else (maxWidth * .93f).coerceIn(260.dp, 380.dp)
            Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp), verticalArrangement = Arrangement.spacedBy(20.dp)) {
                LazyRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) { items(GROUPS) { g -> FilterChip(selected = group == g, onClick = { group = g }, label = { Text(g) }, modifier = Modifier.heightIn(min = 48.dp)) } }
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                    Text("THE COLLECTION", style = Eyebrow, color = Muted)
                    TextButton(onClick = { group = "All prints"; vm.select(PRINTS.filter { it.id != vm.selected.id }.random().id) }, enabled = !vm.busy) { Text("Surprise me ↗") }
                }
                if (wide) {
                    Row(horizontalArrangement = Arrangement.spacedBy(24.dp)) {
                        Artwork(vm, artHeight, { enlarged = vm.image(); dialog = "art" }, Modifier.weight(1f))
                        Inspector(vm, wake, showDialog, Modifier.weight(1f))
                    }
                } else {
                    Artwork(vm, artHeight, { enlarged = vm.image(); dialog = "art" })
                    Inspector(vm, wake, showDialog)
                }
                Text("Find your next everyday.", fontFamily = Canela, fontSize = 24.sp)
                LazyRow(horizontalArrangement = Arrangement.spacedBy(12.dp), contentPadding = PaddingValues(3.dp)) {
                    items(PRINTS.filter { group == "All prints" || it.group == group }, key = { it.id }) { print ->
                        Surface(onClick = { vm.select(print.id) }, enabled = !vm.busy, color = if (vm.selected.id == print.id) Color(0xFFECE5D9) else Garden,
                            border = BorderStroke(if (vm.selected.id == print.id) 2.dp else 1.dp, if (vm.selected.id == print.id) Seal else Hairline), shape = RoundedCornerShape(3.dp),
                            modifier = Modifier.width(118.dp).semantics { selected = vm.selected.id == print.id; contentDescription = "Preview ${print.name}${if (vm.saved.text("page") == print.id) ", saved selection" else ""}" }) {
                            Column(Modifier.padding(10.dp), verticalArrangement = Arrangement.spacedBy(9.dp)) {
                                AsyncImage(model = vm.image(print.id), contentDescription = null, contentScale = ContentScale.Fit, modifier = Modifier.fillMaxWidth().height(125.dp))
                                Text(print.name, fontSize = 11.sp, lineHeight = 15.sp, minLines = 2)
                                Text(if (vm.saved.text("page") == print.id) "SAVED ✓" else print.group.uppercase(), style = Eyebrow.copy(fontSize = 8.sp), color = if (vm.saved.text("page") == print.id) Seal else Muted)
                            }
                        }
                    }
                }
                HorizontalDivider(color = Hairline)
                Text(if (vm.demo) "DEMO FRAME" else "SAVED TO ${vm.github?.repository}", style = Eyebrow, color = Muted)
                Text(PRINTS.first { it.id == vm.saved.text("page") }.name, fontFamily = Canela, fontSize = 23.sp)
                FrameActions(vm, { dialog = "label" }, {
                    vm.loadLatestPreview(); dialog = "latest"
                })
                if (vm.busy || vm.rendering) LinearProgressIndicator(Modifier.fillMaxWidth(), color = Sage, trackColor = Garden)
                Text(vm.status, style = MaterialTheme.typography.bodySmall, color = Muted, modifier = Modifier.semantics { liveRegion = LiveRegionMode.Polite })
                vm.error?.let { message ->
                    Surface(color = Color(0xFFF4E4DE), shape = RoundedCornerShape(4.dp)) {
                        Column(Modifier.padding(14.dp)) { Text(message, style = MaterialTheme.typography.bodyMedium, color = Seal, modifier = Modifier.semantics { liveRegion = LiveRegionMode.Assertive }); TextButton(onClick = vm::clearError) { Text("Dismiss") } }
                    }
                }
                Text("Made for a slower kind of screen.", style = MaterialTheme.typography.bodySmall, color = Muted)
                Spacer(Modifier.height(12.dp))
            }
        }
    }
    when (dialog) {
        "connect" -> ConnectionDialog(vm) { dialog = null }
        "label" -> LabelDialog(vm) { dialog = null }
        "poem" -> StudioDialog("A moment for words", { dialog = null }) {
            val poem = vm.poem
            if (poem == null) { Text("The poem is unavailable."); TextButton(onClick = vm::loadPoem) { Text("Try again") } }
            else {
                Text(poem.text("title_en", poem.text("title")), fontFamily = Canela, fontSize = 28.sp)
                Text("${poem.text("title")} · ${poem.text("author")} · ${poem.text("author_roman")}", style = MaterialTheme.typography.bodySmall, color = Muted)
                Spacer(Modifier.height(14.dp))
                (poem["english"] as? JsonArray ?: poem["lines"] as? JsonArray).orEmpty().forEach { Text(it.jsonPrimitive.content, fontFamily = Canela, fontSize = 21.sp, lineHeight = 30.sp) }
                Spacer(Modifier.height(12.dp)); Text(poem.text("gist"), style = MaterialTheme.typography.bodySmall, color = Muted)
            }
        }
        "photos" -> StudioDialog("Your photographs", { dialog = null }) {
            Text("The frame rotates through the photographs in its repository. Add and remove photographs using the web portal.")
            Text("For a public repository, uploaded photographs are visible to anyone.", style = MaterialTheme.typography.bodySmall, color = Muted)
            if (vm.demo) Text("Connect a frame to open its photo manager.", color = Sage)
            else Button(onClick = { vm.github?.let { uri.openUri(it.portal) } }) { Text("Open web photo manager ↗") }
        }
        "art", "latest" -> StudioDialog(if (dialog == "latest") "Latest generated image" else "Illustrative preview", { dialog = null }) {
            if (dialog == "latest" && vm.latestImage == null) Text(vm.error ?: "Loading the latest render…", color = Muted)
            else AsyncImage(model = if (dialog == "latest") vm.latestImage else enlarged, contentDescription = if (dialog == "latest") "Latest generated image; physical frame display unconfirmed" else "${vm.selected.name} illustrative preview", modifier = Modifier.fillMaxWidth().aspectRatio(2f / 3f), contentScale = ContentScale.Fit)
            Text(if (dialog == "latest") "The physical frame’s current display cannot be confirmed remotely." else "The next render applies your selected options. This artwork illustrates the design.", style = MaterialTheme.typography.bodySmall, color = Muted)
        }
    }
}

@Composable private fun Artwork(vm: AppViewModel, height: Dp, onEnlarge: () -> Unit, modifier: Modifier = Modifier) {
    Column(modifier.fillMaxWidth().background(Garden).padding(17.dp), horizontalAlignment = Alignment.CenterHorizontally) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Text("ILLUSTRATIVE PREVIEW", style = Eyebrow.copy(fontSize = 8.sp), color = Sage)
            Text("${(PRINTS.indexOf(vm.selected) + 1).toString().padStart(2, '0')} / 10", style = Eyebrow.copy(fontSize = 8.sp), color = Sage)
        }
        Box(Modifier.padding(vertical = 22.dp).height(height).aspectRatio(.71f).shadow(14.dp, RoundedCornerShape(2.dp)).background(Color(0xFF32382F)).padding(7.dp)
            .background(Mat).clickable(role = Role.Button, onClickLabel = "Enlarge selected print", onClick = onEnlarge).padding(12.dp)) {
            AsyncImage(model = vm.image(), contentDescription = "${vm.selected.name}, illustrative preview", modifier = Modifier.fillMaxSize().background(Color.White), contentScale = ContentScale.Fit)
        }
        HorizontalDivider(color = Hairline)
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.SpaceBetween) {
            Text(vm.selected.zh, fontSize = 23.sp)
            Row {
                TextButton(onClick = { vm.select(PRINTS[(PRINTS.indexOf(vm.selected) + PRINTS.size - 1) % PRINTS.size].id) }, enabled = !vm.busy, modifier = Modifier.semantics { contentDescription = "Previous print" }) { Text("←", fontSize = 22.sp) }
                TextButton(onClick = { vm.select(PRINTS[(PRINTS.indexOf(vm.selected) + 1) % PRINTS.size].id) }, enabled = !vm.busy, modifier = Modifier.semantics { contentDescription = "Next print" }) { Text("→", fontSize = 22.sp) }
            }
        }
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable private fun Inspector(vm: AppViewModel, wake: Wake, show: (String) -> Unit, modifier: Modifier = Modifier) {
    Column(modifier, verticalArrangement = Arrangement.spacedBy(15.dp)) {
        Text("${vm.selected.group.uppercase()} / ${vm.selected.name.uppercase()}", style = Eyebrow, color = Seal)
        Text(vm.selected.title, style = PrintTitle)
        Text(vm.selected.description, style = MaterialTheme.typography.bodyMedium, color = Muted)
        PAGE_OPTIONS[vm.selected.id].orEmpty().forEach { option ->
            Column { Text(option.label, style = MaterialTheme.typography.labelLarge)
                FlowRow(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    option.values.forEachIndexed { i, value -> FilterChip(selected = vm.draft.text(option.key, option.values.first()) == value, onClick = { vm.setDraft(option.key, value) }, enabled = !vm.busy, label = { Text(option.names[i]) }, modifier = Modifier.heightIn(min = 48.dp)) }
                }
            }
        }
        if (vm.selected.id == "almanac") {
            Text("Edition", style = MaterialTheme.typography.labelLarge)
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) { listOf("auto", "light", "dark").forEach { mode -> FilterChip(selected = vm.draft.text("mode") == mode, onClick = { vm.setDraft("mode", mode) }, enabled = !vm.busy, label = { Text(mode.replaceFirstChar { it.uppercase() }) }, modifier = Modifier.heightIn(min = 48.dp)) } }
            Text("Auto follows the day and evening editions. The evening edition begins at 19:00 Singapore time.", style = MaterialTheme.typography.bodySmall, color = Muted)
        } else Text("This print uses the light edition.", style = MaterialTheme.typography.bodySmall, color = Muted)
        Button(onClick = vm::apply, enabled = vm.dirty && !vm.busy, shape = RoundedCornerShape(4.dp), modifier = Modifier.fillMaxWidth().heightIn(min = 50.dp)) {
            Text(if (vm.busy) "Working…" else if (!vm.dirty) if (vm.demo) "Selected for demo" else "Settings saved" else if (vm.demo) "Try on the demo frame ↗" else "Apply to frame ↗")
        }
        if (vm.dirty) TextButton(onClick = vm::discard, enabled = !vm.busy) { Text("Discard changes") }
        Text(if (vm.dirty) "Your changes are a draft. Rendering applies your options; this preview illustrates the design." else "Browse freely. Nothing changes until you apply a new selection.", style = MaterialTheme.typography.bodySmall, color = Muted)
        HorizontalDivider(color = Hairline)
        Text("NEXT SCHEDULED WAKE · SINGAPORE", style = Eyebrow.copy(fontSize = 9.sp), color = Muted)
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) { Text(wake.time, fontFamily = Canela, fontSize = 32.sp); Text(wake.relative, style = MaterialTheme.typography.bodySmall, color = Muted) }
        Text("The frame fetches the latest render when it wakes. Its current display cannot be confirmed remotely.", style = MaterialTheme.typography.bodySmall, color = Muted)
        if (vm.selected.id == "poem") TextButton(onClick = { show("poem") }) { Text("Read today’s poem in English ↗") }
        if (vm.selected.id == "photo") TextButton(onClick = { show("photos") }) { Text("Manage the photo rotation ↗") }
    }
}
@OptIn(ExperimentalLayoutApi::class)
@Composable private fun FrameActions(vm: AppViewModel, label: () -> Unit, latest: () -> Unit) {
    var mode by rememberSaveable { mutableStateOf("auto") }
    if (vm.saved.text("page") == "almanac") {
        Text("NEXT RENDER ONLY", style = Eyebrow, color = Muted)
        FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            listOf("auto" to "Saved edition", "light" to "Light once", "dark" to "Dark once").forEach { (value, name) ->
                FilterChip(selected = mode == value, onClick = { mode = value }, enabled = !vm.busy, label = { Text(name) }, modifier = Modifier.heightIn(min = 48.dp))
            }
        }
    }
    FlowRow(horizontalArrangement = Arrangement.spacedBy(10.dp), verticalArrangement = Arrangement.spacedBy(5.dp)) {
        TextButton(onClick = label, enabled = !vm.busy) { Text("Frame label") }
        if (!vm.demo) TextButton(onClick = latest) { Text("Latest render") }
        OutlinedButton(onClick = vm::refresh, enabled = !vm.busy) { Text("Refresh status") }
        OutlinedButton(onClick = { vm.renderSaved(if (vm.saved.text("page") == "almanac") mode else "auto") }, enabled = !vm.busy) { Text("Render saved settings ↻") }
    }
}
@Composable private fun StudioDialog(title: String, dismiss: () -> Unit, content: @Composable ColumnScope.() -> Unit) {
    Dialog(onDismissRequest = dismiss, properties = DialogProperties(usePlatformDefaultWidth = false)) {
        Surface(shape = RoundedCornerShape(12.dp), color = Mat, modifier = Modifier.padding(20.dp).widthIn(max = 620.dp).fillMaxWidth().heightIn(max = 760.dp).imePadding()) {
            Column(Modifier.verticalScroll(rememberScrollState()).padding(24.dp), verticalArrangement = Arrangement.spacedBy(13.dp)) {
                Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) { Text(title, fontFamily = Canela, fontSize = 28.sp, lineHeight = 32.sp, modifier = Modifier.weight(1f)); TextButton(onClick = dismiss, modifier = Modifier.semantics { contentDescription = "Close dialog" }) { Text("×", fontSize = 25.sp) } }
                content()
            }
        }
    }
}
@Composable private fun ConnectionDialog(vm: AppViewModel, dismiss: () -> Unit) {
    var repository by rememberSaveable { mutableStateOf(vm.github?.repository.orEmpty()) }
    // A token deliberately stays out of saved-instance-state and screenshots of previews.
    var token by remember { mutableStateOf("") }
    val uri = LocalUriHandler.current
    StudioDialog("Make it yours.", dismiss) {
        Text("Connect the GitHub repository that renders your frame. Demo changes never update a repository.", style = MaterialTheme.typography.bodyMedium, color = Muted)
        OutlinedTextField(value = repository, onValueChange = { repository = it }, label = { Text("Repository · owner/name") }, singleLine = true, modifier = Modifier.fillMaxWidth(), enabled = !vm.busy)
        OutlinedTextField(value = token, onValueChange = { token = it }, label = { Text("GitHub personal access token") }, singleLine = true, visualTransformation = PasswordVisualTransformation(), modifier = Modifier.fillMaxWidth(), enabled = !vm.busy)
        Text("Use a fine-grained token with Contents and Actions read/write access. It is encrypted with Android Keystore on this phone and excluded from backups.", style = MaterialTheme.typography.bodySmall, color = Muted)
        TextButton(onClick = { uri.openUri("https://github.com/settings/personal-access-tokens/new") }) { Text("Create a token on GitHub ↗") }
        vm.error?.let { Text(it, color = Seal, style = MaterialTheme.typography.bodyMedium, modifier = Modifier.semantics { liveRegion = LiveRegionMode.Assertive }) }
        Button(onClick = { vm.connect(repository, token) { token = ""; dismiss() } }, enabled = !vm.busy && repository.isNotBlank() && token.isNotBlank(), modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)) { Text(if (vm.busy) "Connecting…" else "Connect frame") }
        if (!vm.demo) OutlinedButton(onClick = { vm.disconnect(); token = ""; dismiss() }, modifier = Modifier.fillMaxWidth()) { Text("Disconnect and return to demo") }
    }
}
@Composable private fun LabelDialog(vm: AppViewModel, dismiss: () -> Unit) {
    var label by rememberSaveable { mutableStateOf(vm.draft.text("hotspot")) }
    StudioDialog("A name for your frame.", dismiss) {
        Text("This label appears beside the Wi-Fi symbol on the almanac. It does not change the Wi-Fi connection.", style = MaterialTheme.typography.bodyMedium, color = Muted)
        OutlinedTextField(value = label, onValueChange = { if (it.length <= 24) label = it }, label = { Text("Frame label") }, singleLine = true, modifier = Modifier.fillMaxWidth())
        Text("1–24 letters, numbers, spaces, or standard English punctuation.", style = MaterialTheme.typography.bodySmall, color = Muted)
        vm.error?.let { Text(it, color = Seal, style = MaterialTheme.typography.bodySmall) }
        Button(onClick = { if (vm.setLabel(label)) dismiss() }, modifier = Modifier.fillMaxWidth()) { Text("Keep in draft") }
    }
}
