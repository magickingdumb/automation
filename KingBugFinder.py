import os
import subprocess
from urllib.parse import urlparse

# Configuration
domain = "api.deriv.com"
output_dir = "output"
threads = "10"

# Ensure the output directory exists
os.makedirs(output_dir, exist_ok=True)

def run_subdomain_enumeration():
    command = f"subfinder -d {domain} -o {os.path.join(output_dir, 'subdomains.txt')} -t {threads}"
    subprocess.run(command, shell=True)

def run_port_scanning():
    command = f"nmap -sV -p- -T4 {domain} -oN {os.path.join(output_dir, 'ports.txt')}"
    subprocess.run(command, shell=True)

def run_directory_listing():
    command = f"gobuster dir -u https://{domain} -w /usr/share/dirb/wordlists/common.txt -o {os.path.join(output_dir, 'directory_listing.txt')}"
    subprocess.run(command, shell=True)

def run_vulnerability_scanning():
    command = f"nikto -h {domain} -output {os.path.join(output_dir, 'nikto_scan.txt')}"
    subprocess.run(command, shell=True)

def run_ssl_scanning():
    command = f"testssl {domain} > {os.path.join(output_dir, 'ssl_scan.txt')}"
    subprocess.run(command, shell=True)

def run_cms_identification():
    command = f"whatweb {domain} > {os.path.join(output_dir, 'cms_identification.txt')}"
    subprocess.run(command, shell=True)

def run_js_scanning():
    command = f"linkfinder -i {domain} -o cli > {os.path.join(output_dir, 'js_links.txt')}"
    subprocess.run(command, shell=True)

# Execute all functions
run_subdomain_enumeration()
run_port_scanning()
run_directory_listing()
run_vulnerability_scanning()
run_ssl_scanning()
run_cms_identification()
run_js_scanning()

# Generate final report
with open(os.path.join(output_dir, 'final_report.txt'), 'w') as report:
    report.write("Scanning completed. Check the output directory for results.")
