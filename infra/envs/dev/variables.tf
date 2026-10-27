variable "db_instance_class" {
  type    = string
  default = "db.t3.micro"
}

variable "db_multi_az" {
  description = "Standby copy in a second AZ. Doubles the DB cost."
  type        = bool
  default     = true
}
variable "initial_image_tag" {
  description = "An image tag that already exists in ECR"
  type        = string
}

variable "alb_allowed_cidrs" {
  description = "Who may open the load balancer, e.g. your IP and the Jenkins IP"
  type        = list(string)
}

variable "app_instance_type" {
  type    = string
  default = "t3.small"
}