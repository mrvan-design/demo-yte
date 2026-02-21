<<<<<<< HEAD
# Stage 1: Build stage
FROM python:3.10-slim AS build-stage
WORKDIR /app
RUN apt-get update && apt-get install -y gcc libpq-dev
=======
# --- STAGE 1: BUILDER (Chuyên để cài đặt thư viện) ---
FROM python:3.10-slim AS builder

WORKDIR /build-app
>>>>>>> 823482a (21/2)
COPY requirements.txt .

# Cài đặt các thư viện cần thiết để build (nếu có)
RUN apt-get update && apt-get install -y gcc libpq-dev

# Cài đặt thư viện vào thư mục .local
RUN pip install --user --no-cache-dir -r requirements.txt


<<<<<<< HEAD
# Cài đặt runtime libs
=======
# --- STAGE 2: FINAL (Stage nhẹ để chạy ứng dụng) ---
FROM python:3.10-slim

# Cài đặt runtime libs cho OpenCV & Postgres (Chỉ giữ lại cái cần thiết để chạy)
>>>>>>> 823482a (21/2)
RUN apt-get update && apt-get install -y \
    libglib2.0-0 libsm6 libxext6 libxrender1 libgl1 libpq5 \
    && rm -rf /var/lib/apt/lists/*

<<<<<<< HEAD
RUN useradd -m medicaluser

# SỬA Ở ĐÂY: Dùng đúng tên build-stage đã đặt ở trên
COPY --from=build-stage /root/.local /home/medicaluser/.local
COPY --chown=medicaluser:medicaluser . .

RUN chown -R medicaluser:medicaluser /app

USER medicaluser

ENV PATH=/home/medicaluser/.local/bin:$PATH
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
=======
WORKDIR /app

# 1. Tạo user hệ thống
RUN useradd -m medicaluser

# 2. Copy thư viện ĐÃ BUILD từ stage "builder" sang đây
# Chú ý: --from=builder ở đây là gọi stage số 1
COPY --from=builder /root/.local /home/medicaluser/.local

# 3. Copy mã nguồn và gán quyền sở hữu cho medicaluser
COPY --chown=medicaluser:medicaluser . .

# Đảm bảo PATH nhận diện được thư viện trong .local
ENV PATH=/home/medicaluser/.local/bin:$PATH

USER medicaluser

# Khớp Port 8080 như bạn mong muốn
EXPOSE 80
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
>>>>>>> 823482a (21/2)
