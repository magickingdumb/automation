import requests
from concurrent.futures import ThreadPoolExecutor
import os
import subprocess
from bs4 import BeautifulSoup

# Configuration
TARGET_FILE = "targets.txt"
OUTPUT_DIR = "bug_hunt_results"
THREADS = 20  # Adjust based on network capabilities and ethical considerations
HEADERS = {"User-Agent": "BugHunterBot/1.0"}

# Advanced paths and common files to check for vulnerabilities
COMMON_PATHS = ["/admin", "/login", "/dashboard", "/.env", "/wp-login.php", "/config.php", "/db.php"]

# Subdomain Enumeration with Amass
def enumerate_subdomains(domain):
    command = f"amass enum -passive -d {domain}"
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    return stdout.decode().splitlines()

# Scan URLs and log potential vulnerabilities
def scan_url(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=5, verify=False)
        if response.status_code in [200, 401, 403]:
            print(f"[+] Potential target found: {url} (Status: {response.status_code})")
            with open(os.path.join(OUTPUT_DIR, "potential_targets.txt"), "a") as f:
                f.write(f"{url} (Status: {response.status_code})\n")
                
            # Check for common vulnerabilities
            if response.headers.get('Server'):
                check_server_vulnerabilities(url, response.headers['Server'])
    except requests.RequestException as e:
        print(f"[!] Error scanning {url}: {e}")

# Scan for subdomains and paths
def scan_domain(domain):
    subdomains = enumerate_subdomains(domain)
    for subdomain in subdomains:
        scan_url(f"http://{subdomain}")
        for path in COMMON_PATHS:
            scan_url(f"http://{subdomain}{path}")

# Example function to check for known server vulnerabilities
def check_server_vulnerabilities(url, server_header):
    # Placeholder: Replace with actual vulnerability checks based on the server header
    print(f"[+] Checking server vulnerabilities for {url} (Server: {server_header})")

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    with open(TARGET_FILE, 'r') as file:
        domains = [line.strip() for line in file.readlines()]

    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        for domain in domains:
            executor.submit(scan_domain, domain)

if __name__ == "__main__":
    main()
