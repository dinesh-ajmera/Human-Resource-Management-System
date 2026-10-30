data "aws_iam_policy_document" "ec2_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "jenkins" {
  name               = "hrms-jenkins-role"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume.json
}

data "aws_iam_policy_document" "jenkins" {
  statement {
    sid       = "EcrLogin"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }

  statement {
    sid = "EcrPushPullThisRepoOnly"
    actions = [
      "ecr:BatchCheckLayerAvailability", "ecr:InitiateLayerUpload",
      "ecr:UploadLayerPart", "ecr:CompleteLayerUpload", "ecr:PutImage",
      "ecr:BatchGetImage", "ecr:GetDownloadUrlForLayer",
      "ecr:DescribeImages", "ecr:DescribeImageScanFindings",
    ]
    resources = [aws_ecr_repository.hrms.arn]
  }

  statement {
    sid       = "ReleaseTag"
    actions   = ["ssm:GetParameter", "ssm:PutParameter"]
    resources = [aws_ssm_parameter.image_tag.arn]
  }

  statement {
    sid     = "RollingRelease"
    actions = ["autoscaling:StartInstanceRefresh", "autoscaling:CancelInstanceRefresh"]
    # matched by name, so it works even when the dev environment doesn't exist yet
    resources = ["arn:aws:autoscaling:${local.region}:${local.account_id}:autoScalingGroup:*:autoScalingGroupName/hrms-dev-asg"]
  }

  statement {
    sid = "ReadOnlyChecks"
    actions = [
      "autoscaling:DescribeInstanceRefreshes",
      "autoscaling:DescribeAutoScalingGroups",
      "elasticloadbalancing:DescribeLoadBalancers",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "jenkins" {
  name   = "hrms-jenkins"
  role   = aws_iam_role.jenkins.id
  policy = data.aws_iam_policy_document.jenkins.json
}

resource "aws_iam_instance_profile" "jenkins" {
  name = "hrms-jenkins-profile"
  role = aws_iam_role.jenkins.name
}

output "ecr_repository_url" { value = aws_ecr_repository.hrms.repository_url }
output "jenkins_instance_profile" { value = aws_iam_instance_profile.jenkins.name }