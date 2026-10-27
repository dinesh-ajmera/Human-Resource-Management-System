resource "random_password" "db" {
  length  = 24
  special = false
}

resource "aws_db_subnet_group" "db" {
  name       = "hrms-dev-db"
  subnet_ids = module.vpc.private_subnet_ids
}

resource "aws_db_parameter_group" "mysql" {
  name   = "hrms-dev-mysql8"
  family = "mysql8.0"

  parameter {
    name  = "time_zone"
    value = "Asia/Kolkata" # keeps CURDATE() and timestamps in IST
  }
}

resource "aws_db_instance" "hrms" {
  identifier     = "hrms-dev"
  engine         = "mysql"
  engine_version = "8.0"
  instance_class = var.db_instance_class

  allocated_storage     = 20
  max_allocated_storage = 50
  storage_type          = "gp3"
  storage_encrypted     = true

  db_name  = "HR_system"
  username = "hrmsadmin"
  password = random_password.db.result

  db_subnet_group_name   = aws_db_subnet_group.db.name
  vpc_security_group_ids = [aws_security_group.db.id]
  parameter_group_name   = aws_db_parameter_group.mysql.name
  publicly_accessible    = false
  multi_az               = var.db_multi_az

  backup_retention_period         = 7
  enabled_cloudwatch_logs_exports = ["error", "slowquery"]
  auto_minor_version_upgrade      = true
  apply_immediately               = true

  # dev settings so that "terraform destroy" works; production would flip both
  deletion_protection = false
  skip_final_snapshot = true
}