output "ecr_repository_url" {
  value = aws_ecr_repository.app.repository_url
}

output "api_url" {
  value = "http://${aws_lb.app.dns_name}"
}

