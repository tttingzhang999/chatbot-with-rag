resource "aws_s3_bucket" "example" {
  tags = {
    Owner = "TingZhang"
    Retention = "2025-12-31"
  }
}