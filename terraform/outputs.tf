output "public_ip" {
  value = aws_instance.hrms.public_ip
}

output "app_url" {
  value = "http://${aws_instance.hrms.public_ip}:5000"
}

output "ssh_command" {
  value = "ssh -i hrms-key.pem ubuntu@${aws_instance.hrms.public_ip}"
}