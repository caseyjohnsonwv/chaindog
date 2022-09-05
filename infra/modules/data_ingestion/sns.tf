resource "aws_sns_topic" "notification_topic" {
  name = "notification_topic_${var.env_name}"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "sns:Publish"
        Resource = "arn:aws:sns:*:*:notification_topic_${var.env_name}"
        Principal = {
          Service = "s3.amazonaws.com"
        }
        Condition = {
          ArnLike = {
            "aws:SourceArn" : "${aws_s3_bucket.wait_time_bucket.arn}"
          }
        }
      }
    ]
  })
}
