FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Tạo user không phải root
RUN useradd -m appuser

# Copy source
COPY . .

# Tạo thư mục static và cấp quyền cho appuser
RUN mkdir -p /app/static \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
