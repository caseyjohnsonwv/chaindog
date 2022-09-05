resource "aws_sqs_queue" "park_id_queue" {
  name                       = "park_id_queue_${var.env_name}"
  message_retention_seconds  = 180
  visibility_timeout_seconds = 180
}
