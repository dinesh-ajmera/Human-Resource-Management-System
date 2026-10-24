terraform {
  required_version = ">= 1.5"
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

# Latest Ubuntu 24.04 image, published by Canonical
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }
}

# The default VPC that every AWS account already has
data "aws_vpc" "default" {
  default = true
}

# Firewall: SSH and the app port, only from your IP
resource "aws_security_group" "hrms" {
  name        = "hrms-sg"
  description = "Allow SSH and app access from my IP"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.my_ip]
  }

  ingress {
    description = "HRMS app"
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = [var.my_ip]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "hrms-sg" }
}

# The server
resource "aws_instance" "hrms" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  key_name               = var.key_name
  vpc_security_group_ids = [aws_security_group.hrms.id]

  root_block_device {
    volume_size = 10
    volume_type = "gp3"
  }

  metadata_options {
    http_tokens = "required" # IMDSv2 only (safer)
  }

  # Runs once on first boot: swap + Docker. No secrets here.
  user_data = <<-EOF
    #!/bin/bash
    set -e
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    apt-get update -y
    apt-get install -y docker.io docker-compose-v2 git
    systemctl enable --now docker
    usermod -aG docker ubuntu
  EOF

  tags = { Name = "hrms-server" }
}