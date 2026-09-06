import { repository, parseSettings } from './core.js';

export class GitHubError extends Error { constructor(message, status) { super(message); this.status = status; } }
const decode = value => new TextDecoder().decode(Uint8Array.from(atob(value.replace(/\s/g, '')), c => c.charCodeAt(0)));
const encode = value => {
  let binary = '';
  for (const byte of new TextEncoder().encode(value)) binary += String.fromCharCode(byte);
  return btoa(binary);
};
export class GitHub {
  constructor(repo, token, fetcher = (url, options) => globalThis.fetch(url, options)) {
    this.repo = repository(repo); this.token = token.trim(); this.fetcher = fetcher;
    this.api = `https://api.github.com/repos/${this.repo}`;
    this.raw = `https://raw.githubusercontent.com/${this.repo}/main`;
  }
  async request(path, { method = 'GET', body, signal, raw = false } = {}) {
    const timeout = AbortSignal.timeout(30000);
    const combined = signal ? AbortSignal.any([signal, timeout]) : timeout;
    let response;
    try {
      response = await this.fetcher(this.api + path, { method, signal: combined,
        headers: { Accept: raw ? 'application/vnd.github.raw+json' : 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28', Authorization: `Bearer ${this.token}`, ...(body ? { 'Content-Type': 'application/json' } : {}) },
        ...(body ? { body: JSON.stringify(body) } : {}) });
    } catch (error) {
      if (signal?.aborted) throw error;
      throw new GitHubError(error.name === 'TimeoutError' ? 'GitHub took too long to respond. Try again.' : 'Could not reach GitHub. Check your connection and retry.', 0);
    }
    if (!response.ok) {
      const rate = response.status === 429 || response.headers.get('x-ratelimit-remaining') === '0';
      const messages = {
        401: 'GitHub rejected the token. Reconnect with a valid token.',
        403: 'GitHub denied access. Check the token’s Contents and Actions permissions.',
        404: 'Repository or file not found. Check the repository, main branch, and token access.',
        409: 'Settings changed on GitHub while saving. Please try again.',
        422: 'GitHub could not accept this request. Check that the render workflow exists on main.',
      };
      throw new GitHubError(rate ? 'GitHub is limiting requests. Wait a few minutes before retrying.' : messages[response.status] || `GitHub returned ${response.status}. Try again.`, response.status);
    }
    return response.status === 204 ? null : raw ? response.blob() : response.json();
  }
  async settings(signal) {
    const file = await this.request('/contents/generator/settings.json?ref=main', { signal });
    if (typeof file.content !== 'string' || !file.sha) throw new Error('GitHub returned an incomplete settings file.');
    return { value: parseSettings(JSON.parse(decode(file.content))), sha: file.sha };
  }
  async connect(signal) {
    const repo = await this.request('', { signal });
    if (repo.permissions?.push !== true) throw new Error('This token’s account cannot write to the selected repository.');
    const settings = await this.settings(signal);
    await this.runs(signal);
    return { ...settings, private: repo.private === true };
  }
  async runs(signal) {
    const data = await this.request('/actions/workflows/render.yml/runs?per_page=20&branch=main', { signal });
    return data.workflow_runs || [];
  }
  async save(patch, signal) {
    for (let attempt = 0; attempt < 4; attempt++) {
      const current = await this.settings(signal);
      const value = { ...current.value, ...patch };
      try {
        const result = await this.request('/contents/generator/settings.json', { method: 'PUT', signal,
          body: { message: 'studio: update frame settings', content: encode(JSON.stringify(value, null, 2) + '\n'), sha: current.sha, branch: 'main' } });
        if (!result.commit?.sha) throw new Error('Settings were saved, but GitHub did not return a render reference. Refresh status before trying again.');
        return { value, sha: result.commit.sha };
      } catch (error) {
        if (error.status !== 409 || attempt === 3) throw error;
        await new Promise(resolve => setTimeout(resolve, 500 * (attempt + 1)));
      }
    }
  }
  dispatch(mode, signal) { return this.request('/actions/workflows/render.yml/dispatches', { method: 'POST', body: { ref: 'main', inputs: { mode } }, signal }); }
  image(path, signal) { return this.request(`/contents/${path}?ref=main`, { signal, raw: true }); }
  async photos(signal) {
    try {
      const files = await this.request('/contents/generator/photos?ref=main', { signal });
      return files.filter(f => f.type === 'file' && /\.(png|jpe?g)$/i.test(f.name));
    } catch (error) { if (error.status === 404) return []; throw error; }
  }
  upload(name, content, signal) {
    return this.request(`/contents/generator/photos/${encodeURIComponent(name)}`, { method: 'PUT', signal, body: { message: `studio: add photo ${name}`, content, branch: 'main' } });
  }
  remove(photo, signal) {
    return this.request(`/contents/generator/photos/${encodeURIComponent(photo.name)}`, { method: 'DELETE', signal, body: { message: `studio: remove photo ${photo.name}`, sha: photo.sha, branch: 'main' } });
  }
}
