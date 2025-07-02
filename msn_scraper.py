import aiohttp
from bs4 import BeautifulSoup
import os
import asyncio

MSN_CHANNEL_URL = "https://www.msn.com/en-us/channel/source/Football%20Analysis/sr-vid-3nh2yhdmyi9p2xgx244cmsvmhtjnvsdfaug0htkndm23it7wui9s?disableErrorRedirect=true&infiniteContentCount=0"
SEEN_FILE = "seen_msn_galleries.txt"

posted_articles = set()  # URLs seen
articles_list = []       # List of tuples (title, url, thumb) in order seen

def load_seen_articles():
    global posted_articles, articles_list
    if not os.path.isfile(SEEN_FILE):
        posted_articles = set()
        articles_list = []
        return

    # We only have URLs saved, so to reconstruct title/thumb, we store minimal placeholders
    with open(SEEN_FILE, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f.readlines()]
    posted_articles = set(urls)
    # Placeholder titles/thumbs for peek_latest_article
    articles_list = [("MSN Gallery", url, None) for url in urls]

def save_seen_articles():
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        for _, url, _ in articles_list:
            f.write(url + "\n")

async def fetch_articles():
    """Fetch new MSN gallery articles.

    Returns list of tuples: (title, url, thumbnail_url)
    Only returns articles that have not been posted before.
    """
    global posted_articles, articles_list
    load_seen_articles()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(MSN_CHANNEL_URL, headers=headers) as resp:
            if resp.status != 200:
                raise Exception(f"Failed to fetch MSN channel page: HTTP {resp.status}")
            html = await resp.text()

    soup = BeautifulSoup(html, "html.parser")

    new_articles = []
    for a in soup.find_all("a", href=True):
        href = a['href']
        
        if "msn.com" in href and "gallery" in href.lower():
            if href in posted_articles:
                continue

            title = a.get_text(strip=True)
            if not title:
                img = a.find("img", alt=True)
                if img:
                    title = img['alt']
                else:
                    title = "MSN Gallery"

            thumb = None
            img = a.find("img", src=True)
            if img:
                thumb = img['src']

            new_articles.append((title, href, thumb))
            posted_articles.add(href)
            articles_list.append((title, href, thumb))

    if new_articles:
        save_seen_articles()

    return new_articles

async def peek_latest_article():
    """Return the latest article previously seen, or None"""
    load_seen_articles()
    if not articles_list:
        return None
    return articles_list[-1]
