variable "db_instance_class" {
  type    = string
  default = "db.t3.micro"
}

variable "db_multi_az" {
  description = "Standby copy in a second AZ. Doubles the DB cost."
  type        = bool
  default     = true
}