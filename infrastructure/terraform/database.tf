resource "aws_rds_cluster" "prod-cluster" {
  cluster_identifier = "hr-chatbot-cluster"
  engine = "aurora-postgresql"
  availability_zones = ["ap-northeast-1a", "ap-northeast-1c", "ap-northeast-1d"]
  database_name      = "hr_chatbot"
  master_username    = "postgres"
}


resource "aws_rds_cluster_instance" "prod-instance" {
  identifier         = "hr-chatbot-instance"
  cluster_identifier = aws_rds_cluster.prod-cluster.id
  instance_class     = "db.serverless"
  engine             = aws_rds_cluster.prod-cluster.engine
  engine_version     = aws_rds_cluster.prod-cluster.engine_version
  depends_on = [ aws_rds_cluster.prod-cluster ]
}
