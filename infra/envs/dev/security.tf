resource "aws_security_group" "app" {
  name        = "hrms-dev-app-sg"
  description = "App servers"
  vpc_id      = module.vpc.vpc_id
  tags        = { Name = "hrms-dev-app-sg" }
}

resource "aws_vpc_security_group_egress_rule" "app_all" {
  security_group_id = aws_security_group.app.id
  ip_protocol       = "-1"
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_security_group" "db" {
  name        = "hrms-dev-db-sg"
  description = "RDS MySQL"
  vpc_id      = module.vpc.vpc_id
  tags        = { Name = "hrms-dev-db-sg" }
}

# The database accepts connections from the app servers and nobody else
resource "aws_vpc_security_group_ingress_rule" "db_from_app" {
  security_group_id            = aws_security_group.db.id
  referenced_security_group_id = aws_security_group.app.id
  ip_protocol                  = "tcp"
  from_port                    = 3306
  to_port                      = 3306
  description                  = "MySQL from app servers only"
}