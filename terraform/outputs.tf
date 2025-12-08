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

output "api_gateway_url" {
  description = "API Gateway custom domain URL"
  value       = "https://${aws_apigatewayv2_domain_name.api.domain_name}"
}

output "api_gateway_endpoint" {
  description = "API Gateway regional endpoint"
  value       = aws_apigatewayv2_domain_name.api.domain_name_configuration[0].target_domain_name
}
