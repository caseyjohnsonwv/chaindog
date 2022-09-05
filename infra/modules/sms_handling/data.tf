data "aws_s3_bucket" "wait_time_bucket" {
  bucket = var.wait_time_bucket_name
}

data "aws_sns_topic" "notification_topic" {
  name = var.notification_topic_name
}

data "aws_region" "current" {}
