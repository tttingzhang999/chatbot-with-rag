resource "aws_secretsmanager_secret" "app-secrets" {
  description = "Application secrets for HR Chatbot (JWT keys)"
}


resource "aws_secretsmanager_secret" "database" {
  description = "Database credentials for HR Chatbot Aurora PostgreSQL"
}
