resource "aws_lambda_function" "hr-chatbot-backend" {
  function_name                  = "${var.project_name}-backend"
  package_type                   = "Image"
  image_uri                      = local.lambda_image_uri
  role                           = local.lambda_role_arn
  architectures                  = [var.lambda_architecture]
  reserved_concurrent_executions = var.lambda_reserved_concurrent_executions
  timeout                        = var.lambda_timeout
  memory_size                    = var.lambda_memory_size
  publish                        = false

  vpc_config {
    ipv6_allowed_for_dual_stack = false
    security_group_ids          = var.lambda_security_group_ids
    subnet_ids                  = var.lambda_subnet_ids
  }

  environment {
    variables = local.lambda_environment_vars
  }

  tags = local.common_tags
}
