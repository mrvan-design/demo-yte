output "web_public_ip" {
  value = aws_instance.web.public_ip
}

output "rds_endpoint" {
  value = aws_db_instance.db.endpoint
}

output "s3_bucket_name" {
  value = aws_s3_bucket.records.id
}

output "kms_key_arn" {
  value = aws_kms_key.medical_key.arn
}
# --- OUTPUT ---
# Sau khi chạy terraform apply, IP này sẽ hiện ra để bạn truy cập trực tiếp
output "ec2_public_ip" {
  value = aws_instance.web.public_ip
  description = "Địa chỉ IP công khai của máy chủ App"
}
