import re
import asyncio
import random
from datetime import datetime, timedelta
from urllib.parse import quote_plus
from playwright.async_api import async_playwright

async def run(playwright):
    keyword = "디스커버리 익스페디션"
    search_url = f"https://search.naver.com/search.naver?where=news&query={quote_plus(keyword)}&sort=0&field=0&pd=3&ds=2025.06.01&de=2025.06.30&start=1"

    browser = await playwright.chromium.launch(
        headless=False,
        args=[
            '--disable-gpu',
            '--no-sandbox',
            '--disable-blink-features=AutomationControlled',
        ]
    )
    context = await browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        viewport={"width": 1280, "height": 800},
        locale="ko-KR",
        extra_http_headers={
            "Referer": "https://www.naver.com/",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
        }
    )
    await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    await context.add_init_script("Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });")
    await context.add_init_script("Object.defineProperty(navigator, 'languages', { get: () => ['ko-KR', 'ko'] });")

    page = await context.new_page()
    await page.goto(search_url, timeout=20000)
    await asyncio.sleep(random.uniform(2, 4))

    # 스크롤 다운(실제 사용자처럼)
    for _ in range(5):
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        await page.evaluate("window.dispatchEvent(new Event('scroll'))")
        await asyncio.sleep(random.uniform(1, 2))

    await page.screenshot(path="naver_news_debug.png")

    # 실제 DOM 구조에 맞는 selector로 기사 정보 추출
    title_elements = await page.query_selector_all("a.W035WwZVZIWyuG66e5iI > span.sds-comps-text-type-headline1")
    summary_elements = await page.query_selector_all("a.ti6bfMWvbomDA5J1fNOX > span.sds-comps-text-type-body1")
    link_elements = await page.query_selector_all("a.W035WwZVZIWyuG66e5iI")

    print(f"기사 개수: {len(title_elements)}")
    for i in range(len(title_elements)):
        title = await title_elements[i].inner_text()
        summary = await summary_elements[i].inner_text() if i < len(summary_elements) else ""
        href = await link_elements[i].get_attribute("href")
        print(f"{i+1}. 제목: {title}")
        print(f"   요약: {summary}")
        print(f"   링크: {href}")

    input("브라우저를 닫으려면 엔터를 누르세요.")
    await context.close()
    await browser.close()

async def main():
    async with async_playwright() as playwright:
        await run(playwright)

if __name__ == "__main__":
    asyncio.run(main())