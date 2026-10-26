resource "aws_ecr_repository" "hrms" {
  name                 = "hrms"
  image_tag_mutability = "IMMUTABLE" # a tag can never be overwritten
  force_delete         = true        # dev only: lets "terraform destroy" remove images

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }
}

resource "aws_ecr_lifecycle_policy" "hrms" {
  repository = aws_ecr_repository.hrms.name
  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep only the last 10 images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 10
      }
      action = { type = "expire" }
    }]
  })
}

output "ecr_repository_url" {
  value = aws_ecr_repository.hrms.repository_url
}