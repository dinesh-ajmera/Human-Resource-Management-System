data "aws_ssm_parameter" "al2023" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}

resource "aws_cloudwatch_log_group" "app" {
  name              = "/hrms/dev/app"
  retention_in_days = 14
}


resource "aws_launch_template" "app" {
  name_prefix            = "hrms-dev-app-"
  image_id               = data.aws_ssm_parameter.al2023.value
  instance_type          = var.app_instance_type
  vpc_security_group_ids = [aws_security_group.app.id]
  update_default_version = true

  iam_instance_profile {
    name = aws_iam_instance_profile.app.name
  }

  metadata_options {
    http_tokens   = "required"
    http_endpoint = "enabled"
  }

  block_device_mappings {
    device_name = "/dev/xvda"
    ebs {
      volume_size = 20
      volume_type = "gp3"
      encrypted   = true
    }
  }

  user_data = base64encode(templatefile("${path.module}/user_data.sh.tftpl", {
    region    = "ap-south-1"
    param     = data.aws_ssm_parameter.image_tag.name
    secret    = aws_secretsmanager_secret.app.name
    log_group = aws_cloudwatch_log_group.app.name
  }))

  tag_specifications {
    resource_type = "instance"
    tags          = { Name = "hrms-app", Project = "hrms" }
  }
}

resource "aws_autoscaling_group" "app" {
  name                      = "hrms-dev-asg"
  min_size                  = 2
  max_size                  = 4
  desired_capacity          = 2
  vpc_zone_identifier       = module.vpc.private_subnet_ids
  target_group_arns         = [aws_lb_target_group.app.arn]
  health_check_type         = "ELB"
  health_check_grace_period = 300

  launch_template {
    id      = aws_launch_template.app.id
    version = aws_launch_template.app.latest_version
  }

  instance_refresh {
    strategy = "Rolling"
    preferences {
      min_healthy_percentage = 50
      instance_warmup        = 120
    }
  }

  tag {
    key                 = "Name"
    value               = "hrms-app"
    propagate_at_launch = true
  }

  depends_on = [
    module.vpc,
    aws_db_instance.hrms,
    aws_secretsmanager_secret_version.app,
  ]
}

# Add servers when average CPU stays above 50%
resource "aws_autoscaling_policy" "cpu" {
  name                   = "hrms-dev-cpu-target"
  autoscaling_group_name = aws_autoscaling_group.app.name
  policy_type            = "TargetTrackingScaling"

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }
    target_value = 50
  }
}

metrics_granularity = "1Minute"
enabled_metrics     = ["GroupInServiceInstances", "GroupDesiredCapacity", "GroupTotalInstances"]

lifecycle {
  precondition {
    condition     = data.aws_ssm_parameter.image_tag.insecure_value != "unset"
    error_message = "No image has been released yet. Run the Jenkins pipeline first."
  }
}