import { PAGES, OPTIONS, DEFAULTS } from './catalog.js';

export function parseSettings(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('Settings must be a JSON object. Correct generator/settings.json before saving.');
  const result = { ...value };
  if (!PAGES.some(p => p.id === result.page)) result.page = 'almanac';
  if (!['auto', 'light', 'dark'].includes(result.mode)) result.mode = 'auto';
  if (typeof result.hotspot !== 'string') result.hotspot = DEFAULTS.hotspot;
  return result;
}
export function validateDraft(draft) {
  if (!PAGES.some(p => p.id === draft.page)) throw new Error('Choose a print from the collection.');
  if (!['auto', 'light', 'dark'].includes(draft.mode)) throw new Error('Choose Auto, Light, or Dark.');
  if (!/^[\x20-\x7e]{1,24}$/.test(draft.hotspot.trim())) throw new Error('Frame label must contain 1–24 letters, numbers, spaces, or standard English punctuation.');
  for (const option of Object.values(OPTIONS).flat()) {
    if (draft[option.key] !== undefined && !option.values.includes(draft[option.key])) throw new Error(`Choose a valid value for ${option.label.toLowerCase()}.`);
  }
  return { ...draft, hotspot: draft.hotspot.trim() };
}
export function changesBetween(saved, draft) {
  return Object.fromEntries(Object.entries(draft).filter(([key, value]) => saved[key] !== value));
}
export function repository(value) {
  const match = /^([a-z\d](?:[a-z\d-]{0,38}))\/([a-z\d_.-]{1,100})$/i.exec(value.trim());
  if (!match || ['.', '..'].includes(match[2])) throw new Error('Use owner/repository, for example chuatzeyee/Tylendar.');
  return `${match[1]}/${match[2]}`;
}
export function singaporeDate(now = new Date()) {
  const parts = new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Singapore', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hourCycle: 'h23', weekday: 'short' }).formatToParts(now);
  const p = Object.fromEntries(parts.map(p => [p.type, p.value]));
  return { date: `${p.year}-${p.month}-${p.day}`, hour: +p.hour, minute: +p.minute, weekend: ['Sat', 'Sun'].includes(p.weekday) };
}
export function nextWake(now = new Date()) {
  const p = singaporeDate(now), minutes = p.hour * 60 + p.minute;
  const next = [20, 450, 780, 1140].find(v => v > minutes) ?? 1460;
  const remaining = next - minutes;
  return { time: `${String(Math.floor(next % 1440 / 60)).padStart(2, '0')}:${String(next % 60).padStart(2, '0')}`, relative: remaining >= 60 ? `in ${Math.floor(remaining / 60)}h ${remaining % 60}m` : `in ${remaining}m`, tomorrow: next >= 1440 };
}
export function thumbnail(page, mode, now = new Date()) {
  const p = singaporeDate(now);
  const dark = mode === 'dark' || (mode === 'auto' && p.hour >= 19);
  return page === 'almanac' && dark ? `almanac-dark${p.weekend ? '-weekend' : ''}` : page;
}
export function matchingRun(runs, ticket) {
  return runs.filter(run => Number(run.id) > ticket.baseline && run.head_branch === 'main' &&
    (ticket.sha ? run.head_sha === ticket.sha : run.event === 'workflow_dispatch'))
    .sort((a, b) => b.id - a.id)[0];
}
export function dailyPoem(poems, now = new Date()) {
  if (!Array.isArray(poems) || !poems.length) return null;
  const ordinal = Math.round(Date.parse(`${singaporeDate(now).date}T00:00:00Z`) / 86400000) + 719163;
  return poems[ordinal % poems.length];
}
