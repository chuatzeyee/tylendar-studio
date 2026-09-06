import test from 'node:test';
import assert from 'node:assert/strict';
import { parseSettings, validateDraft, changesBetween, repository, thumbnail, nextWake, matchingRun, dailyPoem } from '../js/core.js';
import { GitHub } from '../js/github.js';

test('corrupt settings are rejected instead of silently overwritten', () => {
  for (const value of [null, [], 'wrong', 5]) assert.throws(() => parseSettings(value), /JSON object/);
  assert.deepEqual(parseSettings({ page: 'missing', mode: 'bad', extra: { retained: true } }), { page: 'almanac', mode: 'auto', hotspot: 'Tylendar', extra: { retained: true } });
});
test('draft validation checks labels, options, and modes', () => {
  const good = { page: 'landscape', mode: 'auto', hotspot: ' Studio ', landscape_scenery: 'lake' };
  assert.equal(validateDraft(good).hotspot, 'Studio');
  for (const patch of [{ hotspot: '' }, { hotspot: '山水' }, { mode: 'invalid' }, { landscape_scenery: 'mars' }]) assert.throws(() => validateDraft({ ...good, ...patch }));
});
test('a draft patches only changed fields', () => {
  assert.deepEqual(changesBetween({ page: 'poem', mode: 'auto', future: true }, { page: 'flora', mode: 'auto', future: true }), { page: 'flora' });
});
test('repository names cannot redirect token-bearing requests', () => {
  assert.equal(repository(' owner/Tylendar '), 'owner/Tylendar');
  for (const v of ['https://evil.test/a', 'owner/../repo', 'owner/repo?x=1', 'owner/..', 'owner/repo#fragment']) assert.throws(() => repository(v));
});
test('almanac thumbnails follow Singapore evening and weekend boundaries', () => {
  assert.equal(thumbnail('almanac', 'auto', new Date('2026-09-04T10:59:00Z')), 'almanac');
  assert.equal(thumbnail('almanac', 'auto', new Date('2026-09-04T11:00:00Z')), 'almanac-dark');
  assert.equal(thumbnail('almanac', 'dark', new Date('2026-09-05T04:00:00Z')), 'almanac-dark-weekend');
  assert.equal(thumbnail('poem', 'dark'), 'poem');
});
test('next wake handles an exact wake minute and midnight rollover', () => {
  assert.equal(nextWake(new Date('2026-09-06T11:00:00Z')).time, '00:20');
  assert.equal(nextWake(new Date('2026-09-06T11:00:00Z')).tomorrow, true);
  assert.equal(nextWake(new Date('2026-09-06T15:59:00Z')).relative, 'in 21m');
  assert.equal(nextWake(new Date('2026-09-06T16:00:00Z')).tomorrow, false);
});
test('a settings save follows its commit rather than an unrelated newer run', () => {
  const run = { id: 12, head_branch: 'main', head_sha: 'wanted', event: 'push' };
  const runs = [run, { ...run, id: 13, head_sha: 'other' }, { ...run, id: 14, head_branch: 'feature' }];
  assert.equal(matchingRun(runs, { baseline: 11, sha: 'wanted' }), run);
  assert.equal(matchingRun(runs, { baseline: 11 }), undefined);
  assert.equal(matchingRun([{ ...run, event: 'workflow_dispatch' }], { baseline: 12 }), undefined);
});
test('daily poems use the same ordinal and Singapore date as the renderer', () => {
  assert.equal(dailyPoem([0, 1, 2, 3, 4], new Date('1970-01-01T00:00:00Z')), 719163 % 5);
  assert.equal(dailyPoem([], new Date()), null);
});
test('connecting uses GET requests only', async () => {
  const methods = [];
  const gh = new GitHub('owner/Tylendar', 'token', async (url, opts) => {
    methods.push(opts.method);
    const result = url.includes('/contents/') ? { content: btoa('{"page":"poem"}'), sha: 'sha' } : url.includes('/runs?') ? { workflow_runs: [] } : { permissions: { push: true }, private: false };
    return new Response(JSON.stringify(result));
  });
  assert.equal((await gh.connect()).value.page, 'poem');
  assert.deepEqual(methods, ['GET', 'GET', 'GET']);
});
test('conflict retry rereads settings and retains independent remote changes', async () => {
  let reads = 0, writes = 0, sent;
  const gh = new GitHub('owner/Tylendar', 'token', async (url, opts) => {
    if (opts.method === 'GET') { reads++; return new Response(JSON.stringify({ content: btoa(JSON.stringify({ page: 'poem', mode: 'auto', hotspot: reads === 1 ? 'Old' : 'New', future: { keep: true } })), sha: `sha${reads}` })); }
    writes++; sent = JSON.parse(opts.body);
    return writes === 1 ? new Response('{}', { status: 409 }) : new Response('{"commit":{"sha":"render-this"}}');
  });
  const result = await gh.save({ page: 'flora' });
  assert.equal(writes, 2); assert.equal(sent.sha, 'sha2'); assert.equal(result.sha, 'render-this');
  assert.equal(result.value.hotspot, 'New'); assert.deepEqual(result.value.future, { keep: true });
});
test('rate limits are reported distinctly from permission errors', async () => {
  const gh = new GitHub('owner/Tylendar', 'token', async () => new Response('{}', { status: 403, headers: { 'x-ratelimit-remaining': '0' } }));
  await assert.rejects(gh.connect(), /limiting requests/);
});
test('private image requests use the authenticated Contents API', async () => {
  let request;
  const gh = new GitHub('owner/Tylendar', 'test-token', async (url, options) => {
    request = { url, options }; return new Response(new Uint8Array([137, 80, 78, 71]), { headers: { 'Content-Type': 'image/png' } });
  });
  const blob = await gh.image('output/preview.png');
  assert.equal(blob.type, 'image/png');
  assert.equal(request.url, 'https://api.github.com/repos/owner/Tylendar/contents/output/preview.png?ref=main');
  assert.equal(request.options.headers.Authorization, 'Bearer test-token');
  assert.equal(request.options.headers.Accept, 'application/vnd.github.raw+json');
});
test('a one-time edition dispatch does not write persistent settings', async () => {
  const requests = [];
  const gh = new GitHub('owner/Tylendar', 'test-token', async (url, options) => {
    requests.push({ url, options }); return new Response(null, { status: 204 });
  });
  await gh.dispatch('dark');
  assert.equal(requests.length, 1);
  assert.equal(requests[0].options.method, 'POST');
  assert.deepEqual(JSON.parse(requests[0].options.body), { ref: 'main', inputs: { mode: 'dark' } });
});
