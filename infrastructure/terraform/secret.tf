resource "aws_secretsmanager_secret" "app-secrets" {
  name        = local.app_secret_name
  description = "Application secrets for ${var.project_name} (JWT keys)"

  tags = local.common_tags
}


resource "aws_secretsmanager_secret" "database" {
  name        = local.db_secret_name
  description = "Database credentials for ${var.project_name} Aurora PostgreSQL"

  tags = local.common_tags
}
