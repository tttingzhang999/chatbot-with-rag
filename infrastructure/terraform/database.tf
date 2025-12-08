resource "aws_rds_cluster" "prod-cluster" {
  cluster_identifier = "${var.project_name}-cluster"
  engine             = "aurora-postgresql"
  availability_zones = var.database_availability_zones
  database_name      = var.database_name
  master_username    = var.database_master_username

  tags = local.common_tags
}


resource "aws_rds_cluster_instance" "prod-instance" {
  identifier         = "${var.project_name}-instance"
  cluster_identifier = aws_rds_cluster.prod-cluster.id
  instance_class     = "db.serverless"
  engine             = aws_rds_cluster.prod-cluster.engine
  engine_version     = aws_rds_cluster.prod-cluster.engine_version
  depends_on         = [aws_rds_cluster.prod-cluster]

  tags = local.common_tags
}
