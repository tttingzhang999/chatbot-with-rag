resource "aws_apprunner_service" "hr-chatbot-frontend" {
  service_name = "hr-chatbot-frontend"

  source_configuration {
    auto_deployments_enabled = true

    authentication_configuration {
      access_role_arn = "arn:aws:iam::593713876380:role/hr-chatbot-apprunner-role"
    }

    image_repository {
      image_identifier      = "593713876380.dkr.ecr.ap-northeast-1.amazonaws.com/ting-assignment/hr-chatbot-frontend:v7"
      image_repository_type = "ECR"

      image_configuration {
        port = "7860"
        runtime_environment_variables = {
          BACKEND_API_URL = "https://8lvsiaz5nl.execute-api.ap-northeast-1.amazonaws.com"
          DATABASE_URL    = "postgresql://placeholder:placeholder@localhost/placeholder"
          GRADIO_HOST     = "0.0.0.0"
          GRADIO_PORT     = "7860"
        }
      }
    }
  }

  instance_configuration {
    cpu    = "1024"
    memory = "2048"
  }

  health_check_configuration {
    protocol            = "TCP"
    path                = "/"
    interval            = 10
    timeout             = 10
    healthy_threshold   = 1
    unhealthy_threshold = 3
  }

  network_configuration {
    ingress_configuration {
      is_publicly_accessible = true
    }
    egress_configuration {
      egress_type = "DEFAULT"
    }
  }
}