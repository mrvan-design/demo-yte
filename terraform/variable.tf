variable "region" {
  default = "ap-southeast-1"
}

variable "project_name" {
  default = "medical-portal"
}

variable "db_password" {
  description = "Mat khau cho RDS"
  default     = "SecurePass12345"
  type        = string
  sensitive   = true
}

variable "my_ip" {
  description = "IP cua ban de SSH"
  type        = string
  default     = "14.175.233.87/32"
}
variable "key_name" {
  description = "Ten của SSH Key Pair để truy cập EC2"
  type        = string
  default     = "mykey" # Thay bằng tên Key bạn đã tạo trên AWS
}
variable "private_key_path" {
  description = "Đường dẫn đến file .pem để SSH vào EC2"
  type        = string
  default     = "~/.ssh/mykey.pem" # Thay bằng đường dẫn thực tế của bạn
}