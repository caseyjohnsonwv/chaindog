resource "aws_s3_bucket" "wait_time_bucket" {
  bucket        = "wait-time-bucket-${terraform.workspace}"
  force_destroy = true
}

resource "aws_s3_bucket_lifecycle_configuration" "wait_time_bucket" {
  bucket = aws_s3_bucket.wait_time_bucket.bucket

  rule {
    id     = "RetentionPolicy"
    status = "Enabled"

    expiration {
      days = 1
    }
  }
}
