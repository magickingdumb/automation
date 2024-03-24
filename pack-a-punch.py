# Advanced Script 1: Asynchronous Subdomain Discovery
import asyncio
import aiohttp

async def check_subdomain(domain, subdomain):
    url = f"https://{subdomain}.{domain}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                if resp.status != 404:
                    print(f"Discovered subdomain: {url}")
        except Exception as e:
            pass

async def subdomain_discovery(domain):
    tasks = []
    with open('subdomains_wordlist.txt', 'r') as file:
        for line in file:
            subdomain = line.strip()
            task = asyncio.ensure_future(check_subdomain(domain, subdomain))
            tasks.append(task)
        await asyncio.gather(*tasks)

asyncio.run(subdomain_discovery("example1.com"))

# Advanced Script 2: Concurrent Directory Bruteforce
import asyncio
import aiohttp

async def check_directory(domain, directory):
    url = f"https://{domain}/{directory}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    print(f"Found directory: {url}")
        except Exception as e:
            pass

async def dir_bruteforce(domain):
    tasks = []
    with open('directory_wordlist.txt', 'r') as file:
        for line in file:
            directory = line.strip()
            task = asyncio.ensure_future(check_directory(domain, directory))
            tasks.append(task)
        await asyncio.gather(*tasks)

asyncio.run(dir_bruteforce("example2.com"))

# Advanced Script 3: Asynchronous Port Scanner
import asyncio
import socket

async def scan_port(ip, port):
    conn = asyncio.open_connection(ip, port)
    try:
        reader, writer = await asyncio.wait_for(conn, timeout=1)
        print(f"Port {port}: Open")
        writer.close()
        await writer.wait_closed()
    except:
        pass

async def port_scanner(target):
    tasks = []
    for port in range(1, 65535):
        task = asyncio.ensure_future(scan_port(target, port))
        tasks.append(task)
    await asyncio.gather(*tasks)

asyncio.run(port_scanner("example3.com"))
