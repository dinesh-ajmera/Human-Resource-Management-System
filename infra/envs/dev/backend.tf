terraform {
  backend "s3" {
    bucket       = "hrms-tfstate-205623788823"
    key          = "dev/terraform.tfstate"
    region       = "ap-south-1"
    use_lockfile = true
    encrypt      = true
  }
}