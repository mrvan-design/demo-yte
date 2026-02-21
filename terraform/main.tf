# --- NETWORK ---
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  tags                 = { Name = "${var.project_name}-vpc" }
}


resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id
}

resource "aws_subnet" "public_1" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = false
  availability_zone       = "${var.region}a"
  tags                    = { Name = "public-app-subnet" }
}

resource "aws_subnet" "private_1" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "${var.region}a"
  tags              = { Name = "private-db-1" }
}

resource "aws_subnet" "private_2" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.3.0/24"
  availability_zone = "${var.region}b"
  tags              = { Name = "private-db-2" }
}

resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }
}

resource "aws_route_table_association" "public_assoc_1" {
  subnet_id      = aws_subnet.public_1.id
  route_table_id = aws_route_table.public_rt.id
}

# --- SECURITY & IAM ---
resource "aws_kms_key" "medical_key" {
  description             = "Encryption key for medical records"
  enable_key_rotation     = true
}

resource "aws_iam_role" "ec2_log_role" {
  name = "logrole-ec2"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "cloudwatch_logs" {
  role       = aws_iam_role.ec2_log_role.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
}

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "healthcare-ec2-profile"
  role = aws_iam_role.ec2_log_role.name
}

resource "aws_security_group" "web_sg" {
  name   = "web-server-sg"
  vpc_id = aws_vpc.main.id

  # Port 80 cho HTTP
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Cổng 9090: CHO PROMETHEUS (Chỉ cho IP của bạn)
  ingress {
    from_port   = 9090
    to_port     = 9090
    protocol    = "tcp"
    cidr_blocks = [var.my_ip] # <--- Dùng biến này để bảo mật
  }

  # Cổng 9100: CHO NODE EXPORTER (Chỉ cho IP của bạn)
  ingress {
    from_port   = 9100
    to_port     = 9100
    protocol    = "tcp"
    cidr_blocks = [var.my_ip] # <--- Giám sát phần cứng an toàn
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.my_ip]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "rds_sg" {
  name   = "rds-internal-sg"
  vpc_id = aws_vpc.main.id
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.web_sg.id]
  }
}

# --- STORAGE ---
resource "aws_s3_bucket" "records" {
  bucket_prefix = "medical-data-"
}

resource "aws_s3_bucket_public_access_block" "records_access" {
  bucket                  = aws_s3_bucket.records.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "records_encryption" {
  bucket = aws_s3_bucket.records.id
  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.medical_key.arn
      sse_algorithm     = "aws:kms"
    }
  }
}

resource "aws_s3_bucket_versioning" "records_versioning" {
  bucket = aws_s3_bucket.records.id
  versioning_configuration { status = "Enabled" }
}

# --- DATABASE ---
resource "aws_db_subnet_group" "rds_group" {
  name       = "medical-db-group"
  subnet_ids = [aws_subnet.private_1.id, aws_subnet.private_2.id]
}

resource "aws_db_instance" "db" {
  allocated_storage      = 20
  engine                 = "postgres"
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  instance_class         = "db.t3.micro" # Đảm bảo Free Tier
  db_name                = "med_db"
  username               = "admin_user"
  password               = var.db_password
  db_subnet_group_name   = aws_db_subnet_group.rds_group.name
  vpc_security_group_ids = [aws_security_group.rds_sg.id]
  storage_encrypted      = true
  kms_key_id             = aws_kms_key.medical_key.arn
  
  deletion_protection       = false # Để dễ dàng xóa Lab sau khi xong
  skip_final_snapshot       = true
}

# --- COMPUTE ---


# --- MONITORING ---
resource "aws_cloudwatch_log_group" "app_logs" {
  name              = "/healthcare/app-logs"
  retention_in_days = 7
  # kms_key_id      = aws_kms_key.log_key.arn (Nếu bạn có cấu hình KMS)
}
