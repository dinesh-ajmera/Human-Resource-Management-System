resource "random_password" "flask" {
  length  = 48
  special = false
}

resource "aws_secretsmanager_secret" "app" {
  name                    = "hrms/dev/app"
  recovery_window_in_days = 0 # dev only: lets you destroy and recreate the same name
}

resource "aws_secretsmanager_secret_version" "app" {
  secret_id = aws_secretsmanager_secret.app.id
  secret_string = jsonencode({
    DB_HOST     = aws_db_instance.hrms.address
    DB_PORT     = "3306"
    DB_NAME     = "HR_system"
    DB_USER     = "hrmsadmin"
    DB_PASSWORD = random_password.db.result
    SECRET_KEY  = random_password.flask.result
  })
}