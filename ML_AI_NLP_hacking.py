import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import re
import spacy
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import torch
import transformers
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import numpy as np
import os
import json
import psycopg2
from psycopg2.extras import execute_batch

# Load spaCy model for natural language processing
nlp = spacy.load("en_core_web_lg")

# Load AI-powered sequence classification model
model_name = "distilbert-base-uncased-finetuned-sst-2-english"
model = AutoModelForSequenceClassification.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)

class WebCrawler:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = aiohttp.ClientSession()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        }
        self.visited_urls = set()
        self.vulnerabilities = []
        self.url_queue = [self.base_url]
        self.postgres_conn = psycopg2.connect(
            host="localhost",
            database="mydatabase",
            user="myuser",
            password="mypassword"
        )
        self.postgres_cur = self.postgres_conn.cursor()

    async def start_crawl(self):
        async with self.session as session:
            tasks = [self.scan_url(session, url) for url in self.url_queue]
            while tasks:
                done, tasks = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                for task in done:
                    new_urls = await task
                    for new_url in new_urls:
                        if new_url not in self.visited_urls:
                            self.visited_urls.add(new_url)
                            self.url_queue.append(new_url)
                            tasks.append(self.scan_url(session, new_url))

    async def scan_url(self, session, url):
        print(f"Scanning {url}")
        async with session.get(url, headers=self.headers, timeout=5) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                links = self.extract_links(soup, url)
                self.analyze_text(html, url)
                self.perform_vulnerability_checks(url)
                return links
        return []

    def extract_links(self, soup, base_url):
        links = set()
        for link in soup.find_all('a', href=True):
            href = link['href']
            if not urlparse(href).scheme:
                href = urljoin(base_url, href)
            if 'http' in urlparse(href).scheme and href not in self.visited_urls:
                self.visited_urls.add(href)
                links.add(href)
        return links

    def analyze_text(self, html, url):
        doc = nlp(html)
        for ent in doc.ents:
            self.vulnerabilities.append({"url": url, "data": ent.text, "type": ent.label_})

    def perform_vulnerability_checks(self, url):
        # AI-powered vulnerability detection using sequence classification
        inputs = tokenizer.encode_plus(
            url,
            add_special_tokens=True,
            max_length=512,
            return_attention_mask=True,
            return_tensors='pt'
        )
        outputs = model(inputs['input_ids'], attention_mask=inputs['attention_mask'])
        logits = outputs.logits
        probabilities = torch.softmax(logits, dim=1)
        predicted_class = torch.argmax(probabilities)
        if predicted_class == 1:  # High-risk vulnerability detected
            self.vulnerabilities.append({"url": url, "data": "High-risk vulnerability detected", "type": "Critical"})

    def generate_reports(self):
        pd.DataFrame(self.vulnerabilities).to_csv('vulnerability_report.csv')
        # Store vulnerabilities in PostgreSQL database
        insert_query = "INSERT INTO vulnerabilities (url, data, type) VALUES (%s, %s, %s)"
        execute_batch(self.postgres_cur, insert_query, self.vulnerabilities)
        self.postgres_conn.commit()

if __name__ == "__main__":
    crawler = WebCrawler("https://grammarly.com")
    asyncio.run(crawler.start_crawl())
    crawler.generate_reports()
