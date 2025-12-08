# Data source to reference existing hosted zone
# Using a different AWS account/profile for Route 53 management
data "aws_route53_zone" "goingcloud" {
  provider = aws.route53
  zone_id  = "Z085163319K6AHT4RRWR4"
}

# ACM Certificate for HTTPS (must be in us-east-1 for App Runner)
resource "aws_acm_certificate" "frontend" {
  provider          = aws.us-east-1
  domain_name       = "ting-hr-chatbot.goingcloud.ai"
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Owner     = "TingZhang"
    Retention = "2025-12-31"
    Project   = "hr-chatbot"
  }
}

# DNS record for certificate validation
resource "aws_route53_record" "frontend_cert_validation" {
  provider = aws.route53

  for_each = {
    for dvo in aws_acm_certificate.frontend.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = data.aws_route53_zone.goingcloud.zone_id
}

# Certificate validation
resource "aws_acm_certificate_validation" "frontend" {
  provider                = aws.us-east-1
  certificate_arn         = aws_acm_certificate.frontend.arn
  validation_record_fqdns = [for record in aws_route53_record.frontend_cert_validation : record.fqdn]
}

# A record pointing to CloudFront distribution
resource "aws_route53_record" "frontend" {
  provider = aws.route53
  zone_id  = data.aws_route53_zone.goingcloud.zone_id
  name     = "ting-hr-chatbot.goingcloud.ai"
  type     = "A"

  alias {
    name                   = aws_cloudfront_distribution.frontend.domain_name
    zone_id                = aws_cloudfront_distribution.frontend.hosted_zone_id
    evaluate_target_health = false
  }
}

# AAAA record for IPv6 support
resource "aws_route53_record" "frontend_ipv6" {
  provider = aws.route53
  zone_id  = data.aws_route53_zone.goingcloud.zone_id
  name     = "ting-hr-chatbot.goingcloud.ai"
  type     = "AAAA"

  alias {
    name                   = aws_cloudfront_distribution.frontend.domain_name
    zone_id                = aws_cloudfront_distribution.frontend.hosted_zone_id
    evaluate_target_health = false
  }
}
