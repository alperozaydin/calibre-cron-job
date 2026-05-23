import requests
import subprocess

import json

import time

import os
import sys
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from aws_lambda_powertools.logging import Logger
from dotenv import load_dotenv


LOGGER = Logger()
load_dotenv()

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASS = os.getenv("SENDER_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")
WEBSHARE_API_KEY = os.getenv("WEBSHARE_API_KEY")
WEBSHARE_HEADERS = {"Authorization": f"Token {WEBSHARE_API_KEY}"}
WEBSHARE_LIST_URL = "https://proxy.webshare.io/api/v2/proxy/list/?mode=direct"

def send_email(epub_file, sender_email, sender_password, recipient_email):
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = "The Economist News"

    with open(epub_file, "rb") as f:
        mime = MIMEBase("application", "octet-stream")
        mime.set_payload(f.read())
        encoders.encode_base64(mime)
        mime.add_header("Content-Disposition", "attachment", filename=os.path.basename(epub_file))
        msg.attach(mime)

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())
        LOGGER.info("The Economist news has been sent to your Kindle email.")


BLOCKED_ERROR_MARKER = "Could not find any articles"


WEBSHARE_BASE_URL = "https://proxy.webshare.io/api/v2/proxy/ipauthorization/"


def authorize_current_ip():
    LOGGER.info("Authorizing current IP for Webshare proxy...")
    new_ip = requests.get('https://ifconfig.me').text.strip()

    response = requests.get(WEBSHARE_BASE_URL, headers=WEBSHARE_HEADERS)
    if response.status_code == 200:
        authorizations = response.json().get('results', [])
        for auth in authorizations:
            auth_id = auth['id']
            del_res = requests.delete(f"{WEBSHARE_BASE_URL}{auth_id}/", headers=WEBSHARE_HEADERS)
            if del_res.status_code == 204:
                LOGGER.info(f"Deleted old authorization: {auth['ip_address']}")

    data = {"ip_address": new_ip}
    add_res = requests.post(WEBSHARE_BASE_URL, json=data, headers=WEBSHARE_HEADERS)

    if add_res.status_code == 201:
        LOGGER.info(f"Successfully authorized new IP: {new_ip}")
    else:
        LOGGER.error(f"Failed to authorize: {add_res.text}")


def wait_for_proxy_auth(proxy_url, max_retries=60, delay=10):
    LOGGER.info("Waiting for proxy IP authorization to propagate (this can take up to 10 minutes on Webshare)...")
    proxies = {
        "http": proxy_url,
        "https": proxy_url
    }
    for i in range(max_retries):
        try:
            res = requests.get("https://httpbin.org/ip", proxies=proxies, timeout=10)
            if res.status_code == 200:
                LOGGER.info(f"Proxy is successfully authenticated and ready after {i * delay} seconds!")
                return True
        except requests.exceptions.ProxyError:
            LOGGER.info(f"Proxy returned 407 Authentication Required (attempt {i+1}/{max_retries}). Waiting {delay}s...")
        except requests.exceptions.RequestException as e:
            LOGGER.info(f"Proxy test failed with {e} (attempt {i+1}/{max_retries}). Waiting {delay}s...")
        
        time.sleep(delay)
    
    LOGGER.error("Proxy authorization did not propagate in time.")
    return False


def get_all_proxies():
    LOGGER.info("Fetching proxy list from Webshare API...")
    response = requests.get(WEBSHARE_LIST_URL, headers=WEBSHARE_HEADERS)
    response.raise_for_status()
    results = response.json().get('results', [])

    if not results:
        raise ValueError("No proxies found in your Webshare account!")

    proxies = []
    for p in results:
        proxy_url = f"http://{p['proxy_address']}:{p['port']}"
        proxies.append({
            "url": proxy_url,
            "address": p['proxy_address'],
            "port": p['port'],
            "country": p.get('country_code', 'unknown'),
        })

    LOGGER.info(f"Found {len(proxies)} proxies available")
    return proxies


def try_download_with_proxy(proxy, recipe, epub_file):
    LOGGER.info(
        f"Attempting download with proxy {proxy['address']}:{proxy['port']} "
        f"({proxy['country']})"
    )

    calibre_env = os.environ.copy()
    calibre_env["http_proxy"] = proxy["url"]
    calibre_env["https_proxy"] = proxy["url"]
    calibre_env["HTTP_PROXY"] = proxy["url"]
    calibre_env["HTTPS_PROXY"] = proxy["url"]
    calibre_env["ALL_PROXY"] = proxy["url"]
    calibre_env["no_proxy"] = "localhost,127.0.0.1"
    
    # Fix for Fargate: Chromium crashes silently if /dev/shm is too small (64MB default in Fargate)
    calibre_env["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-dev-shm-usage"

    result = subprocess.run(
        ["xvfb-run", "ebook-convert", recipe, epub_file],
        env=calibre_env,
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        return True

    combined_output = (result.stdout or "") + (result.stderr or "")

    if BLOCKED_ERROR_MARKER in combined_output:
        LOGGER.warning(
            f"Proxy {proxy['address']}:{proxy['port']} ({proxy['country']}) "
            f"is blocked by The Economist. Trying next proxy..."
        )
        return False

    LOGGER.error(
        f"ebook-convert failed with an unexpected error using proxy "
        f"{proxy['address']}:{proxy['port']}:\n{combined_output}"
    )
    raise RuntimeError(
        f"ebook-convert failed with an unexpected error (not a proxy block). "
        f"See logs above for details."
    )


def main():
    epub_file = "economist.epub"
    recipe = "custom_economist.recipe"

    proxies = get_all_proxies()
    
    # Authorize Fargate container's IP
    authorize_current_ip()
    
    # Wait for the first proxy to become authorized (if one works, they all work for this IP)
    wait_for_proxy_auth(proxies[0]["url"])

    LOGGER.info(f"Download started for {recipe}")

    for i, proxy in enumerate(proxies, start=1):
        LOGGER.info(f"--- Proxy attempt {i}/{len(proxies)} ---")
        try:
            success = try_download_with_proxy(proxy, recipe, epub_file)
        except RuntimeError:
            sys.exit(1)

        if success:
            LOGGER.info(f"Download is done for {recipe}!")
            send_email(epub_file, SENDER_EMAIL, SENDER_PASS, RECIPIENT_EMAIL)
            return

    LOGGER.error(
        f"All {len(proxies)} proxies were blocked by The Economist. "
        f"No more proxies to try. Please check your Webshare proxy pool — "
        f"you may need to refresh or add proxies from different regions/ASNs."
    )
    sys.exit(1)


if __name__ == "__main__":
    main()