terraform {
backend "s3" {
    bucket         = "medical-app-terraform-state-xyz"
    key            = "medical-portal/terraform.tfstate" # Đường dẫn file trong bucket
    region         = "ap-southeast-1"
    encrypt        = true
    #dynamodb_table = "terraform-lock" 
  }  # dynamodb_table = "terraform-lock" # Tùy chọn: Dùng để khóa file khi có 2 người cùng sửa
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}