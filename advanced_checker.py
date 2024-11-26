import requests
import time
import json
import argparse
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Suppress only the single InsecureRequestWarning from urllib3 needed
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def parse_args():
    parser = argparse.ArgumentParser(description="Advanced HTTP Checker")
    parser.add_argument('input_file', type=str, help="File containing URLs to check")
    parser.add_argument('output_file', type=str, help="File to save the results")
    parser.add_argument('--format', choices=['txt', 'json'], default='txt', help="Output format")
    parser.add_argument('--https', action='store_true', help="Use HTTPS for URLs without protocol")
    return parser.parse_args()

def check_url(url, use_https):
    # Ensure the URL has a proper protocol
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url if use_https else 'http://' + url
        
    try:
        response = requests.get(url, verify=False, timeout=10)
        return {
            'url': url,
            'status_code': response.status_code,
            'title': get_title(response.text),
            'headers': dict(response.headers),
            'server': response.headers.get('Server', 'Unknown')
        }
    except requests.RequestException as e:
        return {
            'url': url,
            'error': str(e)
        }

def get_title(html):
    start = html.find('<title>')
    end = html.find('</title>', start)
    if start == -1 or end == -1:
        return "No Title Found"
    return html[start + 7:end]

def save_results(results, output_file, output_format):
    if output_format == 'json':
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=4)
    else:
        with open(output_file, 'w') as f:
            for result in results:
                f.write(f"URL: {result['url']}\n")
                if 'error' in result:
                    f.write(f"Error: {result['error']}\n")
                else:
                    f.write(f"Status Code: {result['status_code']}\n")
                    f.write(f"Title: {result['title']}\n")
                    f.write(f"Headers: {json.dumps(result['headers'], indent=4)}\n")
                    f.write(f"Server: {result['server']}\n")
                f.write("\n")

def main():
    args = parse_args()
    results = []

    with open(args.input_file, 'r') as file:
        urls = file.readlines()

    for url in urls:
        url = url.strip()
        result = check_url(url, args.https)
        results.append(result)
        save_results(results, args.output_file, args.format)
        time.sleep(0.33)  # Rate limit to 3 requests per second but you can change this if needed, it's like this to not overload servers or get blacklisted 

if __name__ == "__main__":
    main()
