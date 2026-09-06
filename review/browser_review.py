"""Browser regression checks. All GitHub traffic is intercepted locally."""
import base64
import json
import re
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / 'review/screenshots'
SHOTS.mkdir(exist_ok=True)
BASE = 'http://127.0.0.1:8765'


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path='/usr/bin/google-chrome')
        context = browser.new_context(viewport={'width': 1440, 'height': 1100}, reduced_motion='reduce')
        calls, errors, dispatches = [], [], []
        settings = {'page': 'almanac', 'mode': 'auto', 'hotspot': 'Test frame', 'future': {'keep': True}}
        state = {'revision': 10, 'fail': False}

        def github(route):
            req = route.request
            calls.append((req.method, req.url))
            if '/contents/output/preview.png' in req.url:
                route.fulfill(path=str(ROOT / 'docs/previews/almanac.png'), content_type='image/png')
                return
            if '/contents/generator/settings.json' in req.url:
                if req.method == 'GET':
                    result = {'content': base64.b64encode(json.dumps(settings).encode()).decode(), 'sha': str(state['revision'])}
                else:
                    if state['fail']:
                        route.fulfill(status=403, json={'message': 'fixture permission denial'})
                        return
                    data = req.post_data_json
                    settings.clear()
                    settings.update(json.loads(base64.b64decode(data['content'])))
                    state['revision'] += 1
                    result = {'commit': {'sha': f"commit-{state['revision']}"}}
            elif '/runs?' in req.url:
                result = {'workflow_runs': [
                    {'id': state['revision'] + 100, 'head_branch': 'main', 'head_sha': 'unrelated', 'event': 'schedule', 'status': 'completed', 'conclusion': 'failure'},
                    {'id': state['revision'], 'head_branch': 'main', 'head_sha': f"commit-{state['revision']}", 'event': 'push', 'status': 'completed', 'conclusion': 'success'},
                ]}
                # Baseline should include the unrelated run, so real save IDs advance past it.
                if state['revision'] == 10:
                    result['workflow_runs'] = [{'id': 10, 'head_branch': 'main', 'head_sha': 'old', 'event': 'push', 'status': 'completed', 'conclusion': 'success'}]
            elif '/contents/generator/photos' in req.url:
                result = []
            elif req.method == 'POST':
                dispatches.append(req.post_data_json)
                route.fulfill(status=204)
                return
            else:
                result = {'permissions': {'push': True}, 'private': False}
            route.fulfill(json=result)

        context.route('https://api.github.com/**', github)
        context.route('https://raw.githubusercontent.com/**', lambda route: route.fulfill(path=str(ROOT / 'docs/previews/almanac.png'), content_type='image/png'))
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(BASE, wait_until='networkidle')
        expect(page.get_by_role('heading', name='A little room to wander.')).to_be_visible()
        page.screenshot(path=str(SHOTS / 'portal-desktop.png'), full_page=True)
        assert not calls, 'Demo must make no GitHub requests'
        page.get_by_role('button', name='Nature', exact=False).first.click()
        expect(page.locator('.print-card')).to_have_count(2)
        page.get_by_role('button', name='Preview Seasonal flora').click()
        page.get_by_label('The plant').select_option('bamboo')
        page.get_by_role('button', name='Try on the demo frame').click()
        expect(page.locator('#status-text')).to_contain_text('demo only')
        assert not calls, 'Applying in demo must make no GitHub writes'
        page.get_by_role('button', name='All prints', exact=False).first.click()
        page.get_by_role('button', name='Preview A daily poem').click()
        page.locator('#read-poem').click()
        expect(page.locator('#poem-lines p').first).to_be_visible()
        page.keyboard.press('Escape')
        page.get_by_role('button', name='Preview Daily almanac').click()
        page.get_by_label('Dark', exact=True).check()
        assert 'almanac-dark' in page.locator('#artwork').get_attribute('src')
        page.locator('#frame-settings').click()
        page.get_by_label('Frame label', exact=True).fill('山水')
        page.get_by_role('button', name='Keep in draft').click()
        expect(page.locator('#label-error')).to_contain_text('1–24')
        page.get_by_label('Frame label', exact=True).fill('My studio')
        page.get_by_role('button', name='Keep in draft').click()
        expect(page.locator('#label-dialog')).not_to_be_visible()
        page.get_by_role('button', name='Preview Your photographs').click()
        page.locator('#manage-photos').click()
        page.set_input_files('#photo-input', {'name': 'test.png', 'mimeType': 'image/png', 'buffer': (ROOT / 'docs/previews/flora.png').read_bytes()})
        expect(page.locator('.photo-row')).to_have_count(1)
        page.get_by_role('button', name='Remove test.jpg').click()
        page.get_by_role('button', name='Keep photograph', exact=True).click()
        expect(page.locator('.photo-row')).to_have_count(1)
        page.get_by_role('button', name='Remove test.jpg').click()
        page.get_by_role('button', name='Remove', exact=True).click()
        expect(page.locator('.photo-row')).to_have_count(0)
        page.set_input_files('#photo-input', {'name': 'invalid.pdf', 'mimeType': 'application/pdf', 'buffer': b'invalid'})
        expect(page.locator('#photo-status')).to_contain_text('choose a JPG or PNG')
        page.keyboard.press('Escape')
        page.get_by_role('button', name='Discard changes').click()
        page.get_by_role('button', name='Preview Ink landscape').click()
        for width, height, name in [(390, 844, 'mobile'), (360, 800, 'small-mobile'), (900, 900, 'tablet'), (1440, 1100, 'desktop')]:
            page.set_viewport_size({'width': width, 'height': height})
            page.wait_for_timeout(100)
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), f'Horizontal overflow at {width}'
            page.locator('#workspace').focus()
            page.evaluate('window.scrollTo(0, 0)')
            page.screenshot(path=str(SHOTS / f'portal-{name}.png'), full_page=True)
        page.locator('#connect-button').click()
        page.get_by_label('Repository', exact=True).fill('owner/Tylendar')
        page.get_by_label('GitHub personal access token', exact=True).fill('github_pat_' + 'x' * 40)
        page.get_by_role('button', name='Connect frame', exact=True).click()
        try:
            expect(page.locator('#connection-label')).to_have_text('Frame connected')
        except AssertionError:
            print('Connection error:', page.locator('#connection-error').inner_text(), 'requests:', calls, 'page errors:', errors, flush=True)
            raise
        assert calls and all(method == 'GET' for method, _ in calls), 'Connection must use only GET'
        page.get_by_label('NEXT RENDER ONLY', exact=True).select_option('dark')
        page.locator('#render').click()
        expect(page.locator('#status-text')).to_contain_text('Render requested')
        assert dispatches[-1]['inputs']['mode'] == 'dark' and settings['mode'] == 'auto'
        page.locator('#latest-preview').click()
        expect(page.locator('#art-dialog')).to_be_visible()
        expect(page.locator('#enlarged-art')).to_have_attribute('src', re.compile('^blob:'))
        page.keyboard.press('Escape')
        page.get_by_role('button', name='Preview Seasonal flora').click()
        page.get_by_label('The plant').select_option('orchid')
        writes_before = sum(method == 'PUT' for method, _ in calls)
        assert writes_before == 0, 'Browsing and adjusting must not save automatically'
        page.get_by_role('button', name='Apply to frame', exact=True).click()
        expect(page.locator('#status-text')).to_contain_text('Render complete', timeout=15000)
        assert settings['page'] == 'flora' and settings['flora_plant'] == 'orchid'
        assert settings['future'] == {'keep': True}
        assert sum(method == 'PUT' for method, _ in calls) == 1
        state['fail'] = True
        page.get_by_role('button', name='Preview Island weather').click()
        page.get_by_role('button', name='Apply to frame', exact=True).click()
        expect(page.locator('#status-text')).to_contain_text('denied access')
        expect(page.get_by_role('button', name='Apply to frame', exact=True)).to_be_enabled()
        expect(page.get_by_role('heading', name='A feeling for the day.')).to_be_visible()
        page.locator('#connect-button').click()
        page.get_by_role('button', name='Disconnect and return to demo').click()
        expect(page.locator('#connection-label')).to_have_text('Demo collection')
        assert page.evaluate("sessionStorage.getItem('tylendar-studio-session')") is None
        assert not errors, errors
        print('PASS: desktop/mobile/tablet layout, demo isolation, filters, previews, drafts, poem, photo add/remove/cancel, read-only connection, grouped save, matching render, failed-save recovery, disconnect, and no browser errors.')
        browser.close()


if __name__ == '__main__':
    main()
