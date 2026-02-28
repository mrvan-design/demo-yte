resource "aws_instance" "web" {
  ami                    = data.aws_ami.amazon_linux_2.id
  instance_type          = "t3.small" 
  associate_public_ip_address = true
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name
  subnet_id              = aws_subnet.public_1.id
  vpc_security_group_ids = [aws_security_group.web_sg.id]
  key_name               = var.key_name # Đảm bảo bạn đã tạo Key Pair này trên AWS

  user_data = <<-EOF
             #!/bin/bash
              sudo yum update -y
              EOF
  # Kích hoạt Ansible sau khi EC2 có IP
  # QUAN TRỌNG: Phải có self.public_ip đứng trước dấu phẩy
}

data "aws_ami" "amazon_linux_2" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}