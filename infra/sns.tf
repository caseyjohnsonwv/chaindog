resource "aws_sns_topic" "notification_topic" {
  name = "notification_topic_${terraform.workspace}"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "sns:Publish"
        Resource = "arn:aws:sns:*:*:notification_topic_${terraform.workspace}"
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

resource "aws_sns_topic" "sms_topic" {
  name = "sms_topic_${terraform.workspace}"
}
