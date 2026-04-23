# 🏥 Secure Medical Imaging Pipeline (DevSecOps)

> **Automated, Secure, and Compliant Image Processing Infrastructure for Healthcare**

## 🌟 Tổng quan (Overview)
Dự án triển khai một hệ thống xử lý ảnh y tế toàn diện dựa trên tư duy **DevSecOps**, hướng tới việc tuân thủ các tiêu chuẩn bảo mật dữ liệu y tế nghiêm ngặt (như HIPAA/GDPR). Hệ thống bao phủ toàn bộ vòng đời ứng dụng: từ khâu tự động che giấu thông tin bệnh nhân (De-identification), kiểm thử bảo mật mã nguồn liên tục, đến việc cấp phát hạ tầng trên AWS theo mô hình Zero Trust.

## 🛡️ Tính năng Bảo mật Cốt lõi (Security-First Features)

### 1. Data Privacy & Protection
* **Image Masking (OpenCV):** Tự động nhận diện và làm mờ (masking) các vùng chứa thông tin cá nhân (PII) trên ảnh X-quang trước khi đẩy vào lưu trữ.
* **Encryption at Rest:** Dữ liệu được mã hóa tự động bằng AWS KMS (AES-256) tại S3 (lưu trữ ảnh) và RDS (cơ sở dữ liệu).

### 2. Infrastructure Hardening (IaC với Terraform)
* **Secret Management:** Sử dụng AWS Secrets Manager, loại bỏ hoàn toàn việc lưu trữ mật khẩu dạng plain-text trong mã nguồn.
* **Network Segmentation:** Phân tách rạch ròi Public Subnet (dành cho FastAPI App) và Private Subnet (dành cho Database). RDS chỉ chấp nhận traffic từ dải IP nội bộ của App.
* **Secure State File:** Terraform state được lưu trữ an toàn trên S3, kết hợp cơ chế State Locking bằng DynamoDB để tránh xung đột khi làm việc nhóm.

### 3. CI/CD Security Gates (Jenkins)
Pipeline tích hợp cơ chế **Fail-fast**, tự động dừng tiến trình build/deploy nếu phát hiện rủi ro bảo mật:
* **SCA & Image Scanning (Trivy):** Quét lỗ hổng trong các thư viện phụ thuộc và hệ điều hành của Docker Image (Chặn các lỗi mức độ HIGH/CRITICAL).
* **SAST (Semgrep) - *[Work in Progress]*:** Đang trong quá trình tinh chỉnh rule sets để quét các lỗ hổng bảo mật trực tiếp trong mã nguồn Python một cách chính xác nhất.

## 🏗️ Kiến trúc & Công nghệ (Architecture & Tech Stack)

| Lớp (Layer) | Công nghệ Sử dụng (Technologies) |
| :--- | :--- |
| **Backend & Processing** | Python, FastAPI, OpenCV, SQLAlchemy |
| **Infrastructure (AWS)** | EC2, RDS, S3, KMS, Secrets Manager |
| **IaC & Provisioning** | Terraform |
| **DevSecOps & CI/CD** | Jenkins, Docker, Trivy, Semgrep |
| **Observability (Audit)** | Prometheus, Grafana, Loki |

## 🚀 Hướng dẫn Triển khai (Quick Start)

### Bước 1: Khởi tạo hạ tầng AWS với Terraform
*(Lưu ý: Đảm bảo bạn đã cấu hình AWS CLI credentials)*
```bash
cd terraform
terraform init

# Thực thi cấp phát hạ tầng (Lưu ý: Một số biến môi trường hiện tại đang được truyền thủ công, sẽ được tự động hóa hoàn toàn trong phiên bản tới)
terraform apply -var="db_password=your_secret" -var="my_ip=$(curl -s ifconfig.me)"
