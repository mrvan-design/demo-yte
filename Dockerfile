# --- STAGE 1: BUILDER ---
FROM python:3.10-slim AS builder

WORKDIR /build-app

# Cài đặt công cụ cần thiết để build thư viện
RUN apt-get update && apt-get install -y gcc libpq-dev

COPY requirements.txt .

# Cài đặt thư viện vào thư mục .local của root để dễ copy sang stage sau
RUN pip install --user --no-cache-dir -r requirements.txt

# --- STAGE 2: FINAL ---
FROM python:3.10-slim

# Cài đặt runtime libs cần thiết cho OpenCV và Postgres
RUN apt-get update && apt-get install -y \
    libglib2.0-0 libsm6 libxext6 libxrender1 libgl1 libpq5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Tạo user hệ thống để chạy app cho an toàn (Security Best Practice)
RUN useradd -m medicaluser

# Copy thư viện đã cài từ stage builder sang
COPY --from=builder /root/.local /home/medicaluser/.local
# Copy toàn bộ mã nguồn vào /app
COPY --chown=medicaluser:medicaluser . .

# Cập nhật biến môi trường PATH để nhận diện uvicorn và thư viện
ENV PATH=/home/medicaluser/.local/bin:$PATH

USER medicaluser

# Mở port 8080 và chạy ứng dụng
EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
