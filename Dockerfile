# -------- STAGE 1: BUILDER --------
FROM python:3.12-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /build

# Cài tool build rồi xoá cache ngay
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Tạo wheel để final stage chỉ copy file build sẵn
RUN pip install --upgrade pip setuptools wheel && \
    pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt


# -------- STAGE 2: FINAL --------
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Cài runtime libs cần thiết
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libglib2.0-0 libsm6 libxext6 libxrender1 libgl1 libpq5 && \
    rm -rf /var/lib/apt/lists/*

# Tạo user an toàn
RUN useradd -m -u 1001 medicaluser

# Copy wheels và cài đặt
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Copy source
COPY --chown=medicaluser:medicaluser . .

USER medicaluser

EXPOSE 80

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
