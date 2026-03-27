# ==============================================================
# Stage 1 — Build Tailwind CSS (DaisyUI)
# ==============================================================
FROM node:20-alpine AS css-builder

WORKDIR /build

# Install dependencies first (cache-friendly)
COPY package.json package-lock.json ./
RUN npm ci

# Copy only what Tailwind needs to scan for classes
COPY static/input.css static/style.css static/script.js ./static/
COPY templates/ ./templates/

# Generate minified CSS
RUN npm run build:css

# ==============================================================
# Stage 2 — Python production image
# ==============================================================
FROM python:3.13-slim

# System deps: WeasyPrint (pango, cairo, gdk-pixbuf) + unrar
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    libcairo2 \
    unrar-free \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py gunicorn.conf.py relatorio_pdf.py ConfereEmpresa.py runtime.txt ./
COPY services/ ./services/
COPY utils/ ./utils/
COPY templates/ ./templates/
COPY static/ ./static/

# Overwrite with minified CSS from Stage 1
COPY --from=css-builder /build/static/tailwind.css ./static/tailwind.css

EXPOSE 5000

# 1 worker + 8 threads: preserves threading.Lock / Semaphore in-memory state
CMD ["gunicorn", "app:app", "--workers", "1", "--threads", "8", "--bind", "0.0.0.0:5000", "--timeout", "120"]
