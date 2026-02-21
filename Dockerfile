# ===== BASE IMAGE =====
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Chỉ cài những lib thật sự cần cho runtime
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq5 \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements trước để tận dụng cache layer
COPY requirements.txt .

# Tăng timeout + không cache pip
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --default-timeout=300 -r requirements.txt

# Tạo user non-root
RUN useradd -m -u 1001 appuser

# Copy source code
COPY --chown=appuser:appuser app ./app

USER appuser

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]

