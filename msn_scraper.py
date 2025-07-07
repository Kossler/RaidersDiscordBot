import feedparser
import os
import aiohttp
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from validate_url import clean_url, is_valid_url


FEED_URL = "https://footballanalysis1.com/feed/msn-galleries/"
SEEN_FILE = "seen_urls.txt"
CHANNEL_URL = "https://www.msn.com/en-us/channel/source/Football%20Analysis/sr-vid-3nh2yhdmyi9p2xgx244cmsvmhtjnvsdfaug0htkndm23it7wui9s"

async def get_article_metadata(analysis_url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(analysis_url) as resp:
                if resp.status != 200:
                    return None

                html = await resp.text()
                soup = BeautifulSoup(html, "html.parser")

                def og(prop):
                    tag = soup.find("meta", property=f"og:{prop}")
                    return tag["content"].strip() if tag and tag.get("content") else None

                title = og("title") or "New Article"
                description = og("description") or "New update from Football Analysis"
                image = og("image")
                if image:
                    image = clean_url(image)
                author_tag = soup.find("meta", attrs={"name": "author"})
                author = author_tag["content"] if author_tag and author_tag.get("content") else "Football Analysis"

                # Call get_msn_url here to get the MSN link if available
                msn_url = await fetch_msn_article_url(CHANNEL_URL, title)
                if not msn_url:
                    print(f"[SKIP] No MSN URL found for: {title}")
                    return None
                
                return {
                    "title": title,
                    "url": msn_url, 
                    "description": description,
                    "image": image if is_valid_url(image) else None,
                    "author": author
                }

    except Exception as e:
        print(f"[ERROR] Failed to get metadata for {analysis_url}: {e}")
        return None


# Load seen URLs from file
def load_seen_urls():
    if not os.path.exists(SEEN_FILE):
        return set()
    with open(SEEN_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

# Save new seen URLs
def save_seen_urls(urls):
    with open(SEEN_FILE, "a", encoding="utf-8") as f:
        for url in urls:
            f.write(url + "\n")

seen_urls = load_seen_urls()

async def fetch_articles():
    feed = feedparser.parse(FEED_URL)
    new_articles = []
    new_urls = []

    for entry in feed.entries:
        fa_url = entry.link.strip()

        if fa_url not in seen_urls:
            meta = await get_article_metadata(fa_url)
            if meta:  # Only if MSN URL is found
                seen_urls.add(fa_url)
                new_urls.append(fa_url)
                new_articles.append(meta)


    if new_urls:
        save_seen_urls(new_urls)

    return new_articles

async def fetch_msn_article_url(channel_url: str, match_headline: str) -> str | None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/114.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080}
        )

        await page.goto(channel_url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_selector("cs-content-card", timeout=15000)

        # Extract all cards with title + href
        cards = await page.query_selector_all("cs-content-card")
        print(f"[DEBUG] Found {len(cards)} cs-content-card elements.")

        for card in cards:
            title = await card.get_attribute("title")
            href = await card.get_attribute("href")
            print(f"[DEBUG] Title: {title}")
            if title in match_headline:
                print(f"[DEBUG] Matched Title: {title}")
                return href

            if title in match_headline + " - Football Analysis":
                print(f"[DEBUG] Matched Title: {title}")
                print(href)
                return href

        await browser.close()

    return None
