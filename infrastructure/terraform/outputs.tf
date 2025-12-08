# CloudFront and Frontend Outputs
output "cloudfront_distribution_id" {
  description = "CloudFront Distribution ID (needed for cache invalidation)"
  value       = aws_cloudfront_distribution.frontend.id
}

output "cloudfront_domain_name" {
  description = "CloudFront Distribution Domain Name"
  value       = aws_cloudfront_distribution.frontend.domain_name
}

output "frontend_url" {
  description = "Frontend custom domain URL"
  value       = "https://ting-hr-chatbot.goingcloud.ai"
}

output "s3_bucket_name" {
  description = "S3 bucket name for frontend static files"
  value       = aws_s3_bucket.frontend.id
}

output "acm_certificate_arn" {
  description = "ACM certificate ARN for HTTPS"
  value       = aws_acm_certificate.frontend.arn
}
