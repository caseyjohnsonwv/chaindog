output "wait_time_bucket_name" {
  value = aws_s3_bucket.wait_time_bucket.bucket
}

output "notification_topic_name" {
  value = aws_sns_topic.notification_topic.name
}