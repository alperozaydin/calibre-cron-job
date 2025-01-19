import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from aws_lambda_powertools.logging import Logger
from dotenv import load_dotenv

LOGGER = Logger()
load_dotenv()

SENDER_EMAIL=os.getenv("SENDER_EMAIL")
SENDER_PASS=os.getenv("SENDER_PASSWORD")
RECIPIENT_EMAIL=os.getenv("RECIPIENT_EMAIL")

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


def main():
    epub_file = "economist.epub"
    recipe = "The Economist.recipe"
    LOGGER.info(f"Download started for {recipe}")

    os.system(f"ebook-convert '{recipe}' {epub_file}")

    LOGGER.info(f"Download is done for {recipe}!")

    send_email(epub_file, SENDER_EMAIL, SENDER_PASS, RECIPIENT_EMAIL)

if __name__ == "__main__":
    main()