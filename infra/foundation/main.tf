terraform {
  required_version = ">= 1.10"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
  backend "s3" {
    bucket       = "hrms-tfstate-205623788823"
    key          = "foundation/terraform.tfstate"
    region       = "ap-south-1"
    use_lockfile = true
    encrypt      = true
  }
}

provider "aws" {
  region = "ap-south-1"
  default_tags {
    tags = {
      Project     = "hrms"
      Environment = "foundation"
      ManagedBy   = "terraform"
    }
  }
}

data "aws_caller_identity" "me" {}

locals {
  region     = "ap-south-1"
  account_id = data.aws_caller_identity.me.account_id
}