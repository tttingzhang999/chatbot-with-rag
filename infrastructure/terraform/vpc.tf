resource "aws_vpc" "this" {
  tags = {
    Owner     = "TingZhang"
    Retention = "2025-12-31"
  }
}

resource "aws_subnet" "this-1a" {
  vpc_id     = aws_vpc.this.id
  cidr_block = "10.0.0.0/25"
  tags = {
    Owner     = "TingZhang"
    Retention = "2025-12-31"
  }
}

resource "aws_subnet" "this-1c" {
  vpc_id     = aws_vpc.this.id
  cidr_block = "10.0.0.128/25"
  tags = {
    Owner     = "TingZhang"
    Retention = "2025-12-31"
  }
}

resource "aws_vpc_endpoint" "secretsmanager" {
  vpc_id              = aws_vpc.this.id
  service_name        = "com.amazonaws.ap-northeast-1.secretsmanager"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = [aws_subnet.this-1a.id, aws_subnet.this-1c.id]
  security_group_ids  = ["sg-0dfc84b0acf5f5565"]
  private_dns_enabled = true

  tags = {
    Owner     = "TingZhang"
    Retention = "2025-12-31"
  }
}

resource "aws_vpc_endpoint" "bedrock-runtime" {
  vpc_id              = aws_vpc.this.id
  service_name        = "com.amazonaws.ap-northeast-1.bedrock-runtime"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = [aws_subnet.this-1a.id, aws_subnet.this-1c.id]
  security_group_ids  = ["sg-0dfc84b0acf5f5565"]
  private_dns_enabled = true

  tags = {
    Owner     = "TingZhang"
    Retention = "2025-12-31"
  }
}