# Output for debugging and manual DNS record creation
output "apprunner_validation_records" {
  description = "DNS validation records needed for App Runner custom domain"
  value = aws_apprunner_custom_domain_association.frontend.certificate_validation_records
}

output "frontend_url" {
  description = "Frontend custom domain URL"
  value       = "https://${aws_apprunner_custom_domain_association.frontend.domain_name}"
}

output "apprunner_dns_target" {
  description = "App Runner DNS target for CNAME record"
  value       = aws_apprunner_custom_domain_association.frontend.dns_target
}
