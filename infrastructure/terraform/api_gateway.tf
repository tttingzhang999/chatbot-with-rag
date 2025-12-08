# API Gateway for HR Chatbot Backend
resource "aws_apigatewayv2_api" "hr_chatbot_api" {
  name          = "hr-chatbot-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = [
      "https://ting-hr-chatbot.goingcloud.ai",
    ]
    allow_methods     = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers     = ["*"]
    allow_credentials = true
    expose_headers    = ["*"]
    max_age           = 300
  }

  tags = {
    Owner     = "TingZhang"
    Project   = "hr-chatbot"
    Managed   = "terraform"
    Retention = "2025-12-31"
  }
}

# Lambda Integration
resource "aws_apigatewayv2_integration" "lambda" {
  api_id           = aws_apigatewayv2_api.hr_chatbot_api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.hr-chatbot-backend.invoke_arn

  payload_format_version = "2.0"
}

# Auth Routes
resource "aws_apigatewayv2_route" "auth_register" {
  api_id    = aws_apigatewayv2_api.hr_chatbot_api.id
  route_key = "POST /auth/register"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_route" "auth_login" {
  api_id    = aws_apigatewayv2_api.hr_chatbot_api.id
  route_key = "POST /auth/login"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

# Chat Routes
resource "aws_apigatewayv2_route" "chat_message" {
  api_id    = aws_apigatewayv2_api.hr_chatbot_api.id
  route_key = "POST /chat/message"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_route" "chat_conversations_list" {
  api_id    = aws_apigatewayv2_api.hr_chatbot_api.id
  route_key = "GET /chat/conversations"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_route" "chat_conversations_get" {
  api_id    = aws_apigatewayv2_api.hr_chatbot_api.id
  route_key = "GET /chat/conversations/{conversation_id}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_route" "chat_conversations_create" {
  api_id    = aws_apigatewayv2_api.hr_chatbot_api.id
  route_key = "POST /chat/conversations"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_route" "chat_conversations_delete" {
  api_id    = aws_apigatewayv2_api.hr_chatbot_api.id
  route_key = "DELETE /chat/conversations/{conversation_id}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

# Upload Routes
resource "aws_apigatewayv2_route" "upload_presigned_url" {
  api_id    = aws_apigatewayv2_api.hr_chatbot_api.id
  route_key = "POST /upload/presigned-url"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_route" "upload_process_document" {
  api_id    = aws_apigatewayv2_api.hr_chatbot_api.id
  route_key = "POST /upload/process-document"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_route" "upload_documents_list" {
  api_id    = aws_apigatewayv2_api.hr_chatbot_api.id
  route_key = "GET /upload/documents"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_route" "upload_documents_delete" {
  api_id    = aws_apigatewayv2_api.hr_chatbot_api.id
  route_key = "DELETE /upload/documents/{document_id}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

# Health check / Root route
resource "aws_apigatewayv2_route" "root" {
  api_id    = aws_apigatewayv2_api.hr_chatbot_api.id
  route_key = "GET /"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

# Stage
resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.hr_chatbot_api.id
  name        = "$default"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      routeKey       = "$context.routeKey"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
    })
  }

  tags = {
    Owner     = "TingZhang"
    Project   = "hr-chatbot"
    Managed   = "terraform"
    Retention = "2025-12-31"
  }
}

# CloudWatch Log Group for API Gateway
resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "/aws/apigateway/hr-chatbot-api"
  retention_in_days = 7

  tags = {
    Owner     = "TingZhang"
    Project   = "hr-chatbot"
    Managed   = "terraform"
    Retention = "2025-12-31"
  }
}

# Lambda Permission for API Gateway
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.hr-chatbot-backend.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.hr_chatbot_api.execution_arn}/*/*"
}

# ACM Certificate for API Gateway Custom Domain
resource "aws_acm_certificate" "api" {
  domain_name       = "api.ting-hr-chatbot.goingcloud.ai"
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Owner     = "TingZhang"
    Retention = "2025-12-31"
    Project   = "hr-chatbot"
    Managed   = "terraform"
  }
}

# DNS record for API certificate validation
resource "aws_route53_record" "api_cert_validation" {
  provider = aws.route53

  for_each = {
    for dvo in aws_acm_certificate.api.domain_validation_options : dvo.domain_name => {
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

# API Certificate validation
resource "aws_acm_certificate_validation" "api" {
  certificate_arn         = aws_acm_certificate.api.arn
  validation_record_fqdns = [for record in aws_route53_record.api_cert_validation : record.fqdn]
}

# API Gateway Custom Domain Name
resource "aws_apigatewayv2_domain_name" "api" {
  domain_name = "api.ting-hr-chatbot.goingcloud.ai"

  domain_name_configuration {
    certificate_arn = aws_acm_certificate_validation.api.certificate_arn
    endpoint_type   = "REGIONAL"
    security_policy = "TLS_1_2"
  }

  tags = {
    Owner     = "TingZhang"
    Project   = "hr-chatbot"
    Managed   = "terraform"
    Retention = "2025-12-31"
  }
}

# API Gateway Domain Mapping
resource "aws_apigatewayv2_api_mapping" "api" {
  api_id      = aws_apigatewayv2_api.hr_chatbot_api.id
  domain_name = aws_apigatewayv2_domain_name.api.id
  stage       = aws_apigatewayv2_stage.default.id
}

# Route 53 A Record for API Gateway Custom Domain
resource "aws_route53_record" "api" {
  provider = aws.route53
  zone_id  = data.aws_route53_zone.goingcloud.zone_id
  name     = "api.ting-hr-chatbot.goingcloud.ai"
  type     = "A"

  alias {
    name                   = aws_apigatewayv2_domain_name.api.domain_name_configuration[0].target_domain_name
    zone_id                = aws_apigatewayv2_domain_name.api.domain_name_configuration[0].hosted_zone_id
    evaluate_target_health = false
  }
}
