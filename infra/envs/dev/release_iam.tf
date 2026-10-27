data "aws_iam_policy_document" "app_param" {
  statement {
    actions   = ["ssm:GetParameter"]
    resources = [aws_ssm_parameter.image_tag.arn]
  }
}

resource "aws_iam_role_policy" "app_param" {
  name   = "read-image-tag"
  role   = aws_iam_role.app.id
  policy = data.aws_iam_policy_document.app_param.json
}

data "aws_iam_policy_document" "jenkins_release" {
  statement {
    actions   = ["ssm:GetParameter", "ssm:PutParameter"]
    resources = [aws_ssm_parameter.image_tag.arn]
  }
  statement {
    actions   = ["autoscaling:StartInstanceRefresh", "autoscaling:CancelInstanceRefresh"]
    resources = [aws_autoscaling_group.app.arn]
  }
  statement {
    actions = [
      "autoscaling:DescribeInstanceRefreshes",
      "autoscaling:DescribeAutoScalingGroups",
      "elasticloadbalancing:DescribeLoadBalancers",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "jenkins_release" {
  name   = "release-to-asg"
  role   = aws_iam_role.jenkins.id
  policy = data.aws_iam_policy_document.jenkins_release.json
}