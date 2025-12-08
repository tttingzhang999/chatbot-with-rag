resource "aws_apigatewayv2_api" "hr_chatbot_api" {
  name                       = "hr-chatbot-api"
  protocol_type              = "HTTP"
  region                     = "ap-northeast-1"

  api_key_selection_expression = "$request.header.x-api-key"
  route_selection_expression   = "$request.method $request.path"

  tags = {
    Owner     = "TingZhang"
    Project   = "hr-chatbot"
    Managed   = "terraform"
    Retention = "2025-12-31"
  }
}

# API Gateway Custom Domain
resource "aws_apigatewayv2_domain_name" "api" {
  domain_name = "api.ting-hr-chatbot.goingcloud.ai"

  domain_name_configuration {
    certificate_arn = aws_acm_certificate.api.arn
    endpoint_type   = "REGIONAL"
    security_policy = "TLS_1_2"
  }

  depends_on = [aws_acm_certificate_validation.api]

  tags = {
    Owner     = "TingZhang"
    Project   = "hr-chatbot"
    Retention = "2025-12-31"
  }
}

# API Gateway Stage (auto-deploy)
resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.hr_chatbot_api.id
  name        = "$default"
  auto_deploy = true

  tags = {
    Owner     = "TingZhang"
    Project   = "hr-chatbot"
    Retention = "2025-12-31"
  }
}

# API Gateway Domain Mapping
resource "aws_apigatewayv2_api_mapping" "api" {
  api_id      = aws_apigatewayv2_api.hr_chatbot_api.id
  domain_name = aws_apigatewayv2_domain_name.api.id
  stage       = aws_apigatewayv2_stage.default.id
}
