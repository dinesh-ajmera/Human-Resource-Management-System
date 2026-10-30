   data "aws_ecr_repository" "hrms" { name = "hrms" }
   data "aws_ssm_parameter" "image_tag" { name = "/hrms/dev/image_tag" }