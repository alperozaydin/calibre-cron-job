FROM python:3.9-slim

RUN apt-get update && \
    apt-get install -y calibre && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
COPY .env /app/
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY calibre_cron_job/main.py /app/main.py

WORKDIR /app

CMD ["python", "main.py"]