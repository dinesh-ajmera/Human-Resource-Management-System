data "aws_iam_policy_document" "app_param" {
  statement {
    actions   = ["ssm:GetParameter"]
    resources = [data.aws_ssm_parameter.image_tag.arn]
  }
}

resource "aws_iam_role_policy" "app_param" {
  name   = "read-image-tag"
  role   = aws_iam_role.app.id
  policy = data.aws_iam_policy_document.app_param.json
}