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