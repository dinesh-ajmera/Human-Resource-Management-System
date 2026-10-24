variable "region" {
  type    = string
  default = "ap-south-1"
}

variable "instance_type" {
  type    = string
  default = "t3.micro"
}

variable "key_name" {
  description = "Name of the existing EC2 key pair"
  type        = string
  default     = "apptestkey"
}

variable "my_ip" {
  description = "Your public IP in CIDR form, e.g. 203.0.113.10/32"
  type        = string
}