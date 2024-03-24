# Script 1: Subdomain Discovery
import requests
def subdomain_discovery(domain):
    with open('subdomains_wordlist.txt', 'r') as file:
        for line in file:
            subdomain = line.strip()
            url = f"https://{subdomain}.{domain}"
            try:
                requests.get(url)
                print(f"Discovered subdomain: {url}")
            except requests.ConnectionError:
                pass
subdomain_discovery("example1.com")

# Script 2: Directory Bruteforce
import requests
def dir_bruteforce(domain):
    with open('directory_wordlist.txt', 'r') as file:
        for line in file:
            directory = line.strip()
            url = f"https://{domain}/{directory}"
            response = requests.get(url)
            if response.status_code == 200:
                print(f"Found directory: {url}")
dir_bruteforce("example2.com")

# Script 3: Port Scanner
import socket
def port_scanner(target):
    for port in range(1, 65535):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket.setdefaulttimeout(1)
        result = s.connect_ex((target, port))
        if result == 0:
            print(f"Port {port}: Open")
        s.close()
port_scanner("example3.com")
