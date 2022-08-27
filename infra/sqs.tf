# PARK ID QUEUE


resource "aws_sqs_queue" "park_id_queue" {
  name                      = "park_id_queue_${terraform.workspace}"
  message_retention_seconds = 180
}
