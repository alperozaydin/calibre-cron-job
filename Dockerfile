FROM python:3.13-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    CALIBRE_CONFIG_DIRECTORY=/config \
    PYTHONUNBUFFERED=1 \
    QT_QPA_PLATFORM=offscreen \
    QT_GL_OVERRIDE=software \
    QT_QUICK_BACKEND=software \
    QT_XCB_GL_INTEGRATION=none \
    QTWEBENGINE_DISABLE_SANDBOX=1 \
    PATH="/opt/calibre:$PATH"

# Install necessary system libraries for Calibre's Qt engine
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    ca-certificates \
    libgl1 \
    libegl1 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libxtst6 \
    libxkbcommon0 \
    libasound2 \
    libfontconfig1 \
    libxrender1 \
    libdbus-1-3 \
    libglib2.0-0 \
    libopengl0 \
    libxcb-cursor0 \
    libgl1-mesa-dri \
    xvfb \
    x11-xserver-utils \
    xauth \
    xz-utils \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt/calibre && \
    wget -O- https://download.calibre-ebook.com/9.3.1/calibre-9.3.1-arm64.txz | \
    tar xJ -C /opt/calibre


# Ensure Calibre's internal python/binaries are executable
RUN chmod -R +x /opt/calibre


COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY .env /app/
# RUN playwright install chromium --with-deps

COPY calibre_cron_job/main.py /app/main.py
COPY calibre_cron_job/custom_economist.recipe /app/custom_economist.recipe
WORKDIR /app

CMD ["python", "main.py"]