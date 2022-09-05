resource "aws_sns_topic" "sms_topic" {
  name = "sms_topic_${var.env_name}"
}
