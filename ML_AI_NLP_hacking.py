import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import spacy
import pandas as pd
import asyncpg
from aiohttp import ClientTimeout

# Load spaCy model for natural language processing
nlp = spacy.load("en_core_web_lg")

class AdvancedWebCrawler:
    def __init__(self, base_url, db_params):
        self.base_url = base_url
        self.db_params = db_params
        self.visited_urls = set()
        self.queue = asyncio.Queue()  # Initialize queue here for better performance

    async def fetch_html(self, url, session):
        try:
            async with session.get(url, timeout=ClientTimeout(total=10)) as response:
                response.raise_for_status()
                return await response.text()
        except Exception as e:
            print(f"Failed to fetch {url}: {str(e)}")
            return None

    async def extract_links(self, html, base_url):
        soup = BeautifulSoup(html, 'html.parser')
        for link in soup.find_all('a', href=True):
            href = link['href']
            if not urlparse(href).scheme:
                href = urljoin(base_url, href)
            full_url = urljoin(base_url, href)
            if 'http' in urlparse(full_url).scheme:
                yield full_url

    async def scan_url(self, url, session):
        print(f"Scanning {url}")
        html = await self.fetch_html(url, session)
        if html:
            self.analyze_text(html, url)
            async for link in self.extract_links(html, url):
                if link not in self.visited_urls:
                    self.visited_urls.add(link)
                    yield link

    def analyze_text(self, html, url):
        doc = nlp(html)
        for ent in doc.ents:
            print(f"Found entity {ent.text} of type {ent.label_} in {url}")

    async def crawl(self):
        async with aiohttp.ClientSession() as session:
            self.queue.put_nowait(self.base_url)
            self.visited_urls.add(self.base_url)

            while not self.queue.empty():
                url = await self.queue.get()
                async for new_url in self.scan_url(url, session):
                    if new_url not in self.visited_urls:
                        self.visited_urls.add(new_url)
                        await self.queue.put(new_url)

    async def save_to_db(self, data):
        conn = await asyncpg.connect(**self.db_params)
        await conn.execute('''
            INSERT INTO vulnerabilities(url, data, type) VALUES($1, $2, $3)
        ''', data['url'], data['data'], data['type'])
        await conn.close()

if __name__ == "__main__":
    db_params = {
        'user': 'dbuser',
        'password': 'dbpass',
        'database': 'dbname',
        'host': 'localhost'
    }
    crawler = AdvancedWebCrawler("https://buy2.bigeyes.space", db_params)
    asyncio.run(crawler.crawl())
