"""Run with Playwright installed on E:, using existing Chrome/Edge; no browser download."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright,expect

def main():
    root=Path(__file__).resolve().parents[1]
    report={'checks':[],'errors':[]}
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
        page=browser.new_page(viewport={'width':1440,'height':1100})
        page.on('pageerror',lambda e:report['errors'].append(str(e)))
        page.goto('http://127.0.0.1:8765/',wait_until='networkidle')
        page.get_by_role('button',name='Coffee & sleep',exact=True).click()
        page.locator('.paper').first.wait_for(timeout=30000)
        assert page.locator('.paper').count()>0
        report['checks'].append('Real query returns paper cards')
        page.screenshot(path=str(root/'docs/screenshots/browser-desktop.png'),full_page=False)
        page.locator('.paper .inspect').nth(1).click()
        page.locator('.highlighted').wait_for(timeout=15000)
        assert page.locator('#source .sourcepassage').count()>1
        report['checks'].append('Source opens exact highlighted passage with full-text sections')
        page.get_by_role('button',name='Close source').click()
        page.get_by_role('button',name='Dietitian',exact=True).click()
        page.locator('.selectpaper').nth(0).check();page.locator('.selectpaper').nth(1).check()
        page.get_by_role('button',name='Compare selected (2)').click()
        page.locator('#comparebody table').wait_for()
        assert page.locator('#comparebody th').count()>5
        report['checks'].append('Side-by-side source-linked comparison')
        page.locator('#closecompare').click()
        page.locator('#notes').fill('Browser verification note; no personal data.')
        page.get_by_role('button',name='Save investigation',exact=True).click()
        expect(page.locator('#status')).to_contain_text('saved locally')
        page.get_by_role('button',name='Saved investigations',exact=True).click()
        page.locator('.loadsession').first.click()
        expect(page.locator('#notes')).to_have_value('Browser verification note; no personal data.')
        report['checks'].append('Saved investigation and notes persist and reload')
        with page.expect_download() as dl:page.get_by_role('button',name='Export evidence',exact=True).click()
        assert dl.value.suggested_filename.endswith('.json')
        report['checks'].append('Evidence JSON export downloads')
        page.get_by_role('button',name='Collection & evaluation',exact=True).click()
        page.locator('.stat').first.wait_for()
        assert 'Not available' in page.locator('#coveragebody').inner_text()
        report['checks'].append('Coverage shows real counts; evaluation pending is explicit')
        expect(page.locator('#ai-audit')).to_contain_text('8/12')
        expect(page.locator('#ai-audit')).to_contain_text('not overall fact-checking accuracy')
        page.locator('#ai-audit summary').click()
        assert page.locator('#ai-audit tbody tr').count()==4
        report['checks'].append('AI audit shows real limited results separately from human validation')
        expect(page.locator('#dense-index')).to_contain_text('37,975 section passages')
        expect(page.locator('#ai-audit')).to_contain_text('Historical paper-level audit')
        report['checks'].append('Active full-text semantic index and historical audit are distinguished')
        page.locator('#ai-audit').scroll_into_view_if_needed()
        page.screenshot(path=str(root/'docs/screenshots/browser-evaluation.png'),full_page=False)
        page.set_viewport_size({'width':390,'height':844})
        page.get_by_role('button',name='Explore evidence',exact=True).first.click()
        page.locator('#filtertoggle').click()
        page.locator('#method').select_option('dense')
        with page.expect_response(lambda r:'/api/search?' in r.url,timeout=60000) as response:
            page.locator('#searchbutton').click()
        result=response.value.json()
        assert result['trace']['level']=='passage' and result['results']
        expect(page.locator('#searchbutton')).to_be_enabled(timeout=15000)
        report['checks'].append('Semantic search uses the completed passage index in the browser')
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        page.screenshot(path=str(root/'docs/screenshots/browser-mobile.png'),full_page=False)
        report['checks'].append('390px layout has no horizontal overflow')
        page.keyboard.press('Escape');page.keyboard.press('Tab')
        assert page.evaluate("document.activeElement !== document.body")
        report['checks'].append('Keyboard focus reaches interactive elements')
        browser.close()
    (root/'docs/checks/browser-check.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
    assert not report['errors']

if __name__=='__main__':main()
