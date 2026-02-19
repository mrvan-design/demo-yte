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
  default     = "0.0.0.0/0"
}
variable "key_name" {
  description = "Ten của SSH Key Pair để truy cập EC2"
  type        = string
  default     = "mykey" # Thay bằng tên Key bạn đã tạo trên AWS
}