resource "aws_ecr_repository" "hrms" {
  name                 = "hrms"
  image_tag_mutability = "IMMUTABLE"
  force_delete         = false

  image_scanning_configuration { scan_on_push = true }
  encryption_configuration { encryption_type = "AES256" }

  lifecycle { prevent_destroy = true }
}

resource "aws_ecr_lifecycle_policy" "hrms" {
  repository = aws_ecr_repository.hrms.name
  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep only the last 10 images"
      selection    = { tagStatus = "any", countType = "imageCountMoreThan", countNumber = 10 }
      action       = { type = "expire" }
    }]
  })
}

# The tag every new app server runs. Jenkins writes it; dev only reads it.
resource "aws_ssm_parameter" "image_tag" {
  name  = "/hrms/dev/image_tag"
  type  = "String"
  value = "unset"

  lifecycle { ignore_changes = [value] }
}