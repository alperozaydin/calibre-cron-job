import requests
import subprocess

import json

import time

import os
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
WEBSHARE_PROXY_URL = os.getenv("WEBSHARE_PROXY_URL", "")

WEBSHARE_HEADERS = {"Authorization": f"Token {WEBSHARE_API_KEY}"}
WEBSHARE_BASE_URL = "https://proxy.webshare.io/api/v2/proxy/ipauthorization/"

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


def authorize_current_ip():
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


def main():
    epub_file = "economist.epub"
    recipe = "custom_economist.recipe"

    authorize_current_ip()

    LOGGER.info(f"Download started for {recipe}")

    calibre_env = os.environ.copy()

    calibre_env["http_proxy"] = WEBSHARE_PROXY_URL
    calibre_env["https_proxy"] = WEBSHARE_PROXY_URL

    subprocess.run(
        ["xvfb-run", "ebook-convert", recipe, epub_file],
        env=calibre_env,
        check=True
    )

    LOGGER.info(f"Download is done for {recipe}!")

    send_email(epub_file, SENDER_EMAIL, SENDER_PASS, RECIPIENT_EMAIL)

if __name__ == "__main__":
    main()