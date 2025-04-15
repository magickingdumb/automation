#!/usr/bin/env python3

import nmap, requests, subprocess, re, os, time, random, socket, base64, zlib
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from rich.console import Console
from rich.table import Table
from rich.progress import Progress
import json
from fake_useragent import UserAgent
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import pandas as pd
import numpy as np
import scapy.all as scapy
import threading
import hashlib
import urllib.parse
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import concurrent.futures

# Initialize console for rich formatting
console = Console()
ua = UserAgent()

# WAF signatures for fingerprinting
WAF_SIGNATURES = {
    'Cloudflare': 'cf-ray',
    'ModSecurity': 'Mod_Security',
    'Incapsula': 'X-CDN'
}

# Dynamic payload adjustment
def generate_payloads(vuln_type, target_info, attempt=0):
    if vuln_type == 'XSS':
        payloads = [
            "<script>alert('XSS')</script>",  # Base
            "<img src=x onerror='alert(\"XSS\")'>",  # Simple bypass
            "<svg/onload=confirm(1)>",  # SVG based
            "<iframe srcdoc='<script>alert(String.fromCharCode(88,83,83))</script>'>",  # iframe bypass
            "<style>@import 'javascript:alert(\"XSS\")';</style>",  # CSS based
        ]
    elif vuln_type == 'SQLi':
        if 'MySQL' in target_info:
            payloads = ["' UNION SELECT 1,2,3 --", "' OR 1=1 #", "' AND 1=1 --"]
        elif 'PostgreSQL' in target_info:
            payloads = ["'; SELECT 1,2,3 --", "' OR '1'='1' --"]
        elif 'MSSQL' in target_info:
            payloads = ["'; EXEC sp_executesql N'SELECT 1,2,3'", "' OR '1'='1';--"]
        else:
            payloads = ["' OR '1'='1", "' UNION SELECT 1,2,3 --"]
    
    return payloads[min(attempt, len(payloads)-1)] if attempt < len(payloads) else None

# Browser Parser Analysis for HTML5, CSS vulnerabilities
def check_parser_vulns(response_text):
    vulns = {}
    # Example checks, would need to be updated with latest vulnerabilities
    if re.search(r'<template>\s*\[\s*', response_text, re.IGNORECASE):
        vulns['HTML5_TemplateInj'] = ["HTML5 Template Injection", "light_pink"]
    if re.search(r'@import\s+url\(data:image/svg\+xml;base64,', response_text, re.IGNORECASE):
        vulns['CSS_Import'] = ["CSS Import Vulnerability", "light_yellow"]
    return vulns

# Thread Management for parallel scanning
def scan_target(target, session, clf, progress):
    vulns, target_info = scan_web(target, session, clf, target_info={})
    display_vulnerabilities(target, vulns, target_info)
    progress.update(1)

# Legal and Ethical Compliance Check
def check_legality(target, scope_file="scope.json"):
    with open(scope_file, 'r') as file:
        scope = json.load(file)
    return any(target.startswith(domain) for domain in scope['allowed_domains'])

def load_model():
    data = pd.read_csv('vulnerability_data.csv')
    X = data.drop('vulnerability', axis=1)
    y = data['vulnerability']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    clf = RandomForestClassifier()
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)
    console.print(f"Model accuracy: {accuracy_score(y_test, y_pred)}", style="bold green")
    return clf

def get_targets():
    targets = []
    if os.path.exists("targets.txt"):
        with open("targets.txt", "r") as file:
            targets = [line.strip() for line in file if line.strip()]
    else:
        target = input("Enter a target URL or IP (or leave blank for file reading): ").strip()
        if target:
            targets.append(target)
        else:
            console.print("No targets provided", style="bold red")
            exit()
    return targets

def scan_network(ip):
    nm = nmap.PortScanner()
    nm.scan(ip, '1-1024', arguments='-T4 -F -sV')
    return nm

def scan_web(url, session, clf, target_info):
    vulns = {}
    attempt = 0
    try:
        response = session.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Detect technologies used
        headers = response.headers
        for key in ['Server', 'X-Powered-By']:
            if key in headers:
                target_info[key] = headers[key]
        
        # WAF Fingerprinting
        for waf, signature in WAF_SIGNATURES.items():
            if signature.lower() in str(headers).lower():
                target_info['WAF'] = waf
                break

        # SOP and CSP Checks
        if 'Content-Security-Policy' not in headers:
            vulns['CSP'] = [url, "Missing Content Security Policy", "light_blue"]
        
        if 'X-Frame-Options' not in headers:
            vulns['XFO'] = [url, "Missing X-Frame-Options", "light_blue"]

        # Vulnerability Scanning
        for vuln_type in ['XSS', 'SQLi']:
            while attempt < 4:  # Try up to 4 different payloads
                payload = generate_payloads(vuln_type, target_info, attempt)
                if payload is None:
                    break
                
                test_payload(url, session, vuln_type, payload, vulns)
                if vuln_type in vulns:
                    break  # Vulnerability confirmed, no need for further attempts
                attempt += 1

        # Additional Checks
        vulns.update(check_parser_vulns(response.text))
        vulns.update(scan_for_XXE(response))

        # ML Classification
        features = np.array([len(vulns), sum([len(v) for v in vulns.values()])]).reshape(1, -1)
        prediction = clf.predict(features)
        if prediction[0] != 'NoVuln':
            vulns[prediction[0]] = [url, f"ML Predicted: {prediction[0]}", "purple"]

    except requests.RequestException as e:
        console.print(f"Error connecting to {url}: {e}", style="bold red")
    
    # Check for hidden data in responses
    if 'Content-Encoding' in response.headers and response.headers['Content-Encoding'] == 'gzip':
        decompressed = zlib.decompress(response.content)
        hidden_data = decrypt_data(decompressed)
        if hidden_data:
            vulns['HiddenData'] = [url, f"Hidden data detected: {hidden_data[:100]}...", "light_slate_blue"]

    return vulns, target_info

def test_payload(url, session, vuln_type, payload, vulns):
    try:
        params = {vuln_type: payload}
        resp = session.get(url, params=params, timeout=5)
        if vuln_type in resp.text or vuln_type in resp.content.decode(errors='ignore'):
            if vuln_type not in vulns:
                vulns[vuln_type] = [url, f"{vuln_type} confirmed with payload!", "red" if vuln_type == 'XSS' else "green"]
            else:
                vulns[vuln_type][1] += " - Confirmed with another payload!"
    except:
        pass

def scan_for_XXE(response):
    vulns = {}
    if 'xml' in response.headers.get('Content-Type', '').lower():
        vulns['XXE'] = [response.url, "Potential XML External Entity injection", "blue"]
    return vulns

def decrypt_data(data):
    try:
        decoded = base64.b64decode(data)
        if b'<html>' in decoded or b'HTTP' in decoded:
            return decoded.decode('utf-8', errors='ignore')
        
        key = get_random_bytes(16)  # In practice, key would be predefined or recovered
        cipher = AES.new(key, AES.MODE_ECB)
        decrypted = unpad(cipher.decrypt(data), AES.block_size)
        return decrypted.decode('utf-8', errors='ignore')
    except:
        return "Decryption failed"

def display_vulnerabilities(url, vulns, target_info):
    table = Table(title=f"Vulnerabilities for {url}")
    table.add_column("Type", style="cyan")
    table.add_column("Details", style="magenta")
    table.add_column("Severity", style="bold red")
    
    for vuln_type, info in vulns.items():
        table.add_row(vuln_type, info[1], "[bold " + info[2] + "]" + info[2])
    
    if target_info:
        table.add_row("\nDetected Technologies:", str(target_info), "white")
    
    if not vulns:
        table.add_row("No vulnerabilities found", "", "white")

    console.print(table)

def main():
    console.print("Starting HyperRecon 2025...", style="bold blue")
    
    clf = load_model()
    targets = get_targets()
    session = requests.Session()
    session.headers.update({'User-Agent': ua.random})
    
    with Progress() as progress:
        task = progress.add_task("[cyan]Scanning Targets...", total=len(targets))
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for target in targets:
                if not check_legality(target):
                    console.print(f"Scanning {target} not allowed. Skipping.", style="bold yellow")
                    continue
                futures.append(executor.submit(scan_target, target, session, clf, progress))
            
            for _ in concurrent.futures.as_completed(futures):
                progress.advance(task)

if __name__ == "__main__":
    main()
