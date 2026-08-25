FROM python:3.11-slim

# System deps: Playwright's Chromium + WeasyPrint's Pango/Cairo stack
RUN apt-get update && apt-get install -y --no-install-recommends \
    # WeasyPrint
    libpango-1.0-0 libpangoft2-1.0-0 libcairo2 libgdk-pixbuf-2.0-0 \
    libffi-dev shared-mime-info \
    # Playwright / Chromium
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 \
    libxrandr2 libgbm1 libasound2 libpangocairo-1.0-0 \
    # Utilities
    wget curl supervisor \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright's bundled Chromium (with system deps already present)
RUN playwright install chromium

COPY . .

RUN mkdir -p data static

EXPOSE 8501

COPY supervisord.conf /etc/supervisor/conf.d/a11yfix.conf

CMD ["supervisord", "-n", "-c", "/etc/supervisor/conf.d/a11yfix.conf"]
