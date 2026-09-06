import { PAGES, GROUPS, OPTIONS, DEFAULTS, pageFor } from './catalog.js';
import { validateDraft, changesBetween, nextWake, thumbnail, matchingRun, dailyPoem } from './core.js';
import { GitHub } from './github.js';

const $ = id => document.getElementById(id);
let saved = { ...DEFAULTS }, draft = { ...saved }, group = 'All prints';
let client = null, isPrivate = false, busy = false, latest = false, epoch = 0;
let connection = new AbortController(), watch = null, photoFiles = [], demoPhotos = [];
let latestObjectUrl = null, photoObjectUrls = [];
const sessionKey = 'tylendar-studio-session';
const visiblePages = () => PAGES.filter(p => group === 'All prints' || p.group === group);
const dirty = () => Object.keys(changesBetween(saved, draft)).length > 0;
const el = (tag, text, cls) => { const n = document.createElement(tag); if (text !== undefined) n.textContent = text; if (cls) n.className = cls; return n; };
const open = id => { if (!$(id).open) $(id).showModal(); };
function announce(message, kind = '') { $('status-text').textContent = message; $('status').className = `message ${kind}`; }
function clock() {
  const wake = nextWake(); $('wake-time').textContent = wake.time; $('wake-relative').textContent = `${wake.tomorrow ? 'tomorrow, ' : ''}${wake.relative}`;
}
function previewUrl() { return latest && client ? `${client.raw}/output/preview.png?t=${Date.now()}` : `assets/previews/${thumbnail(draft.page, draft.mode)}.png`; }
function renderFilters() {
  $('filters').replaceChildren(...GROUPS.map(name => {
    const b = el('button', undefined, 'filter-button'); b.setAttribute('aria-pressed', String(name === group));
    b.append(el('span', name), el('span', String(PAGES.filter(p => name === 'All prints' || p.group === name).length).padStart(2, '0'), 'filter-count'));
    b.onclick = () => { group = name; renderFilters(); renderRail(); }; return b;
  }));
}
function renderRail() {
  const pages = visiblePages(); $('collection-count').textContent = `${pages.length} PRINTS`;
  $('collection-label').textContent = group.toUpperCase();
  $('print-rail').replaceChildren(...pages.map(page => {
    const b = el('button', undefined, 'print-card'); b.dataset.page = page.id;
    b.setAttribute('aria-label', `Preview ${page.name}`); b.setAttribute('aria-pressed', String(page.id === draft.page));
    const mat = el('span', undefined, 'thumb-mat'), image = el('img'); image.src = `assets/previews/${thumbnail(page.id, draft.mode)}.png`; image.alt = ''; image.loading = 'lazy';
    mat.append(image); b.append(mat, el('span', page.name, 'card-name'), el('span', page.group.toUpperCase(), 'card-group'));
    if (page.id === saved.page) { const check = el('span', '✓', 'card-check'); check.setAttribute('aria-label', 'Saved selection'); b.append(check); }
    b.onclick = () => select(page.id); return b;
  }));
}
function renderOptions() {
  $('print-options').replaceChildren(...(OPTIONS[draft.page] || []).map(option => {
    const box = el('div'), label = el('label', option.label, 'option-label'), select = el('select');
    label.htmlFor = option.key; select.id = option.key;
    option.values.forEach((v, i) => { const opt = el('option', option.names[i]); opt.value = v; select.append(opt); });
    select.value = draft[option.key] || option.values[0];
    select.onchange = () => { draft = { ...draft, [option.key]: select.value }; latest = false; renderControls(); };
    box.append(label, select); return box;
  }));
}
function renderControls() {
  document.body.classList.toggle('connected', Boolean(client));
  $('connection-label').textContent = client ? 'Frame connected' : 'Demo collection';
  $('disconnect').hidden = !client;
  $('saved-caption').textContent = client ? `SAVED TO ${client.repo}` : 'DEMO FRAME';
  $('saved-page').textContent = pageFor(saved.page).name;
  $('apply-label').textContent = busy ? 'Working…' : dirty() ? (client ? 'Apply to frame' : 'Try on the demo frame') : (client ? 'Settings saved' : 'Selected for demo');
  $('apply').disabled = busy || !dirty(); $('discard').hidden = !dirty(); $('discard').disabled = busy;
  $('render').disabled = busy; $('render-mode').disabled = busy; $('refresh').disabled = busy; $('latest-preview').hidden = !client;
  document.querySelector('.render-once').hidden = saved.page !== 'almanac';
  if (saved.page !== 'almanac') $('render-mode').value = 'auto';
  $('draft-note').textContent = dirty() ? 'Your changes are a draft. Previews illustrate the design; rendering applies your options.' : 'Browse freely. Nothing changes until you apply a new selection.';
  $('mode-field').hidden = draft.page !== 'almanac'; $('light-note').hidden = draft.page === 'almanac';
  document.querySelectorAll('[name=mode]').forEach(radio => { radio.checked = radio.value === draft.mode; radio.disabled = busy; });
  document.querySelectorAll('#print-options select, .print-card, #previous, #next, #surprise, #frame-settings').forEach(n => { n.disabled = busy; });
}
function renderArtwork() {
  const p = pageFor(draft.page);
  $('artwork').src = previewUrl(); $('artwork').alt = `${p.name}: ${latest ? 'latest generated image; frame display unconfirmed' : 'illustrative design preview'}`;
  $('preview-kind').textContent = latest ? 'LATEST GENERATED IMAGE' : 'ILLUSTRATIVE PREVIEW';
  $('art-title').textContent = p.title; $('art-description').textContent = p.description; $('art-chinese').textContent = p.zh;
  $('art-group').textContent = p.group.toUpperCase();
  $('art-detail').textContent = p.detail;
  $('read-poem').hidden = p.id !== 'poem'; $('manage-photos').hidden = p.id !== 'photo';
}
function renderAll() { renderArtwork(); renderOptions(); renderRail(); renderControls(); clock(); }
function select(id) { if (busy) return; draft = { ...draft, page: id }; latest = false; renderAll(); }
async function perform(action) {
  if (busy) return false; busy = true; const captured = epoch; renderControls();
  try { await action(captured); return captured === epoch; } catch (error) { if (captured === epoch && error.name !== 'AbortError') announce(error.message, 'error'); return false; }
  finally { if (captured === epoch) { busy = false; renderControls(); } }
}
function stopWatch() { watch?.abort(); watch = null; }
async function watchRender(ticket) {
  stopWatch(); const ctl = new AbortController(); watch = ctl; const gh = client, captured = epoch;
  const signal = AbortSignal.any([ctl.signal, connection.signal]);
  const deadline = Date.now() + 8 * 60_000;
  try {
    while (!signal.aborted && Date.now() < deadline) {
      await new Promise((resolve, reject) => {
        const cancel = () => { clearTimeout(timer); reject(new DOMException('Cancelled', 'AbortError')); };
        const timer = setTimeout(() => { signal.removeEventListener('abort', cancel); resolve(); }, 4000);
        signal.addEventListener('abort', cancel, { once: true });
      });
      const run = matchingRun(await gh.runs(signal), ticket);
      if (!run) continue;
      if (run.status !== 'completed') { announce('Rendering your saved settings. The frame will fetch the image at its next wake.', 'busy'); continue; }
      if (run.conclusion !== 'success') throw new Error(`The render ${run.conclusion || 'failed'}. Your settings are saved; try rendering again.`);
      announce('Render complete. The frame will fetch the new image at its next scheduled wake.'); return;
    }
    if (!signal.aborted && captured === epoch) announce('The render is taking longer than expected. Refresh status to check it again.');
  } catch (error) { if (!signal.aborted && captured === epoch) announce(error.message, 'error'); }
}
async function apply() {
  await perform(async () => {
    const value = validateDraft(draft), patch = changesBetween(saved, value);
    if (!Object.keys(patch).length) return;
    if (!client) { saved = { ...value }; draft = { ...saved }; announce('Selection saved in this demo only. No frame or repository was changed.'); renderAll(); return; }
    const runs = await client.runs(connection.signal), baseline = Math.max(0, ...runs.map(r => Number(r.id)));
    announce('Saving your selection…', 'busy');
    const result = await client.save(patch, connection.signal);
    saved = result.value; draft = { ...saved }; latest = false; renderAll();
    announce('Settings saved. Waiting for the matching render…', 'busy');
    void watchRender({ baseline, sha: result.sha });
  });
}
async function connect(repo, token, restored = false) {
  if (busy) return; busy = true; $('connection-submit').disabled = true; $('connection-error').textContent = ''; renderControls();
  const captured = epoch;
  try {
    if (!/^(github_pat_|ghp_)[A-Za-z0-9_]{20,}$/.test(token.trim())) throw new Error('Enter a valid GitHub personal access token.');
    const candidate = new GitHub(repo, token), result = await candidate.connect(connection.signal);
    if (captured !== epoch) return;
    stopWatch(); client = candidate; isPrivate = result.private; saved = result.value; draft = { ...saved }; latest = false;
    try { sessionStorage.setItem(sessionKey, JSON.stringify({ repo: candidate.repo, token: candidate.token })); } catch { /* Connection still works when browser storage is disabled. */ }
    $('token').value = ''; $('connection-dialog').close(); renderAll();
    announce(`Connected to ${client.repo}. Apply a draft when you’re ready.`);
  } catch (error) {
    if (captured !== epoch) return;
    if (error.status === 401) { try { sessionStorage.removeItem(sessionKey); } catch {} }
    $('connection-error').textContent = error.message;
    if (restored) announce(`Could not restore the connection: ${error.message} The demo remains available.`, 'error');
  } finally { if (captured === epoch) { busy = false; $('connection-submit').disabled = false; renderControls(); } }
}
function disconnect() {
  epoch++; connection.abort(); connection = new AbortController(); stopWatch(); busy = false; client = null; latest = false;
  saved = { ...DEFAULTS }; draft = { ...saved }; try { sessionStorage.removeItem(sessionKey); } catch {}
  $('token').value = ''; $('connection-dialog').close(); renderAll(); announce('Disconnected. You’re back in the local demo.');
}
function showPhotos() {
  open('photos-dialog'); $('photo-privacy').textContent = !client ? 'Demo photos stay in this tab. Connect a frame to manage its real photo rotation.' : isPrivate ? 'Photos are stored in your private repository.' : 'This repository is public. Uploaded photographs will be visible to anyone.';
  $('photo-status').textContent = '';
  return perform(async () => { photoFiles = client ? await client.photos(connection.signal) : demoPhotos; }).then(success => { renderPhotos(); if (!success) $('photo-status').textContent = $('status-text').textContent; });
}
function renderPhotos() {
  photoObjectUrls.forEach(url => URL.revokeObjectURL(url)); photoObjectUrls = [];
  const list = $('photo-list');
  list.replaceChildren(...photoFiles.map(photo => {
    const row = el('div', undefined, 'photo-row'), img = el('img'), remove = el('button', 'Remove');
    img.alt = photo.name;
    if (photo.url) img.src = photo.url;
    else {
      const captured = epoch;
      client.image(`generator/photos/${encodeURIComponent(photo.name)}`, connection.signal).then(blob => {
        if (captured !== epoch || !row.isConnected) return;
        const url = URL.createObjectURL(blob); photoObjectUrls.push(url); img.src = url;
      }).catch(() => { img.alt = `${photo.name}: thumbnail unavailable`; });
    }
    remove.setAttribute('aria-label', `Remove ${photo.name}`); remove.disabled = busy;
    remove.onclick = async () => {
      $('confirm-description').textContent = `${photo.name} will be removed from ${client ? 'the repository and the rotation' : 'this demo'}.`;
      $('confirm-dialog').returnValue = ''; open('confirm-dialog');
      const approved = await new Promise(resolve => $('confirm-dialog').addEventListener('close', () => resolve($('confirm-dialog').returnValue === 'remove'), { once: true }));
      if (!approved) return;
      const success = await perform(async () => {
        if (client) { await client.remove(photo, connection.signal); photoFiles = await client.photos(connection.signal); }
        else { URL.revokeObjectURL(photo.url); demoPhotos = demoPhotos.filter(p => p !== photo); photoFiles = demoPhotos; }
        $('photo-status').textContent = 'Photograph removed.';
      }); if (!success) $('photo-status').textContent = $('status-text').textContent; renderPhotos();
    };
    row.append(img, el('span', photo.name), remove); return row;
  }));
  if (!photoFiles.length) list.append(el('p', 'Your collection is ready for its first photograph.', 'field-note'));
}
async function encodePhoto(file) {
  if (file.size > 20 * 1024 * 1024) throw new Error(`${file.name} exceeds 20 MB.`);
  if (!['image/jpeg', 'image/png'].includes(file.type)) throw new Error(`${file.name}: choose a JPG or PNG.`);
  const bmp = await createImageBitmap(file, { imageOrientation: 'from-image' });
  try {
    const scale = Math.min(1, 1600 / Math.max(bmp.width, bmp.height)), canvas = document.createElement('canvas');
    canvas.width = Math.max(1, Math.round(bmp.width * scale)); canvas.height = Math.max(1, Math.round(bmp.height * scale));
    const ctx = canvas.getContext('2d'); ctx.fillStyle = '#ffffff'; ctx.fillRect(0, 0, canvas.width, canvas.height); ctx.drawImage(bmp, 0, 0, canvas.width, canvas.height);
    const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg', .85));
    if (!blob) throw new Error(`Could not process ${file.name}.`);
    return await new Promise((resolve, reject) => { const reader = new FileReader(); reader.onload = () => resolve({ blob, content: reader.result.split(',')[1] }); reader.onerror = () => reject(new Error(`Could not read ${file.name}.`)); reader.readAsDataURL(blob); });
  } finally { bmp.close(); }
}

document.querySelectorAll('[data-close]').forEach(b => { b.onclick = () => b.closest('dialog').close(); });
$('connect-button').onclick = () => { $('repository').value = client?.repo || ''; $('connection-error').textContent = ''; open('connection-dialog'); };
$('connection-form').onsubmit = event => { event.preventDefault(); void connect($('repository').value, $('token').value); };
$('disconnect').onclick = disconnect;
$('apply').onclick = apply;
$('discard').onclick = () => { draft = { ...saved }; latest = false; renderAll(); announce('Draft discarded. Saved settings are unchanged.'); };
document.querySelectorAll('[name=mode]').forEach(r => { r.onchange = () => { draft = { ...draft, mode: r.value }; latest = false; renderArtwork(); renderControls(); renderRail(); }; });
for (const [id, direction] of [['previous', -1], ['next', 1]]) $(id).onclick = () => { const pages = visiblePages(), i = pages.findIndex(p => p.id === draft.page); select(pages[(i + direction + pages.length) % pages.length].id); };
$('surprise').onclick = () => { const alternatives = PAGES.filter(p => p.id !== draft.page); group = 'All prints'; renderFilters(); select(alternatives[Math.floor(Math.random() * alternatives.length)].id); };
$('enlarge').onclick = () => { $('enlarged-art').src = $('artwork').src; $('enlarged-art').alt = $('artwork').alt; $('enlarged-caption').textContent = $('preview-kind').textContent; open('art-dialog'); };
$('artwork').onerror = () => { if (latest) { latest = false; renderArtwork(); announce('The latest image is unavailable. Showing an illustrative preview.', 'error'); } };
$('frame-settings').onclick = () => { $('frame-label').value = draft.hotspot; $('label-error').textContent = ''; open('label-dialog'); };
$('label-form').onsubmit = event => { event.preventDefault(); try { draft = validateDraft({ ...draft, hotspot: $('frame-label').value }); $('label-dialog').close(); renderControls(); } catch (error) { $('label-error').textContent = error.message; } };
$('refresh').onclick = () => perform(async () => {
  if (!client) { clock(); announce('Demo collection is ready. Connect a repository to check render status.'); return; }
  const settings = await client.settings(connection.signal), runs = await client.runs(connection.signal);
  const patch = changesBetween(saved, draft); saved = settings.value; draft = { ...saved, ...patch }; latest = false; renderAll();
  const run = runs[0]; announce(!run ? 'No render has run yet.' : run.status !== 'completed' ? 'A render is in progress.' : run.conclusion === 'success' ? 'Latest render succeeded. The frame fetches it at its next wake.' : `Latest render: ${run.conclusion || 'unknown'}.`, run?.conclusion && run.conclusion !== 'success' ? 'error' : '');
});
$('render').onclick = () => perform(async () => {
  if (!client) { announce('Demo preview ready. No workflow was started.'); return; }
  const runs = await client.runs(connection.signal), baseline = Math.max(0, ...runs.map(r => Number(r.id)));
  await client.dispatch($('render-mode').value, connection.signal); announce('Render requested for the saved settings. Your draft is not included.', 'busy'); void watchRender({ baseline });
});
$('latest-preview').onclick = () => perform(async () => {
  const blob = await client.image('output/preview.png', connection.signal);
  if (latestObjectUrl) URL.revokeObjectURL(latestObjectUrl);
  latestObjectUrl = URL.createObjectURL(blob); $('enlarged-art').src = latestObjectUrl;
  $('enlarged-art').alt = 'Latest generated image. Physical frame display unconfirmed.';
  $('enlarged-caption').textContent = 'LATEST GENERATED IMAGE. FRAME DISPLAY UNCONFIRMED.'; open('art-dialog');
});
$('read-poem').onclick = async () => {
  open('poem-dialog'); $('poem-lines').textContent = 'Loading today’s poem…';
  try { const response = await fetch('assets/poems.json'); if (!response.ok) throw new Error('The bundled poem collection is unavailable.'); const poem = dailyPoem(await response.json()); if (!poem) throw new Error('The poem collection is empty.');
    $('poem-title').textContent = poem.title_en || poem.title; $('poem-byline').textContent = [poem.title, poem.author, poem.author_roman].filter(Boolean).join(', ');
    $('poem-lines').replaceChildren(...(poem.english || poem.lines).map(line => el('p', line))); $('poem-gist').textContent = poem.gist || '';
  } catch (error) { $('poem-lines').textContent = error.message; }
};
$('manage-photos').onclick = () => { void showPhotos(); };
$('photo-add').onclick = () => { if (!busy) $('photo-input').click(); };
$('photo-input').onchange = async event => {
  const files = [...event.target.files]; event.target.value = ''; if (!files.length) return;
  if (files.length > 12) { $('photo-status').textContent = 'Choose up to 12 photographs at a time.'; return; }
  let completed = 0; $('photo-add').disabled = true;
  const success = await perform(async () => {
    const taken = new Set((client ? await client.photos(connection.signal) : demoPhotos).map(p => p.name));
    for (const file of files) {
      $('photo-status').textContent = `Preparing ${file.name}…`;
      const { blob, content } = await encodePhoto(file);
      const stem = file.name.replace(/\.[^.]*$/, '').toLowerCase().replace(/[^a-z0-9_-]+/g, '-').slice(0, 40) || 'photo';
      let name = `${stem}.jpg`; for (let i = 2; taken.has(name); i++) name = `${stem}-${i}.jpg`; taken.add(name);
      if (client) await client.upload(name, content, connection.signal); else demoPhotos.push({ name, url: URL.createObjectURL(blob) });
      completed++;
    }
  });
  const failure = success ? '' : ` ${$('status-text').textContent}`;
  $('photo-add').disabled = false;
  await showPhotos(); $('photo-status').textContent = `${completed} of ${files.length} photographs added.${failure}`;
};
$('confirm-cancel').onclick = () => $('confirm-dialog').close('cancel'); $('confirm-remove').onclick = () => $('confirm-dialog').close('remove');
window.addEventListener('beforeunload', event => { if (dirty() || busy) { event.preventDefault(); event.returnValue = ''; } });
document.addEventListener('visibilitychange', () => { if (!document.hidden) clock(); });
renderFilters(); renderAll(); setInterval(clock, 30000);
try { const stored = JSON.parse(sessionStorage.getItem(sessionKey) || 'null'); if (stored?.repo && stored?.token) void connect(stored.repo, stored.token, true); } catch { /* Demo works without browser storage. */ }
