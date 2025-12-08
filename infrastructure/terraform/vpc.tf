resource "aws_vpc" "this" {
  tags = local.common_tags
}

resource "aws_subnet" "this-1a" {
  vpc_id     = aws_vpc.this.id
  cidr_block = var.vpc_cidr_blocks[0]
  tags       = local.common_tags
}

resource "aws_subnet" "this-1c" {
  vpc_id     = aws_vpc.this.id
  cidr_block = var.vpc_cidr_blocks[1]
  tags       = local.common_tags
}

resource "aws_vpc_endpoint" "secretsmanager" {
  vpc_id              = aws_vpc.this.id
  service_name        = local.secretsmanager_endpoint_service
  vpc_endpoint_type   = "Interface"
  subnet_ids          = [aws_subnet.this-1a.id, aws_subnet.this-1c.id]
  security_group_ids  = var.lambda_security_group_ids
  private_dns_enabled = true

  tags = local.common_tags
}

resource "aws_vpc_endpoint" "bedrock-runtime" {
  vpc_id              = aws_vpc.this.id
  service_name        = local.bedrock_runtime_endpoint_service
  vpc_endpoint_type   = "Interface"
  subnet_ids          = [aws_subnet.this-1a.id, aws_subnet.this-1c.id]
  security_group_ids  = var.lambda_security_group_ids
  private_dns_enabled = true

  tags = local.common_tags
}
