resource "aws_lambda_function" "park_id_lambda" {
  filename      = "${local.artifacts_path}/park_id_lambda.zip"
  function_name = "park_id_lambda_${var.env_name}"
  role          = aws_iam_role.park_id_lambda.arn
  handler       = "main.lambda_handler"
  runtime       = "python3.8"
  layers        = var.lambda_layer_arns

  environment {
    variables = {
      queue_url          = aws_sqs_queue.park_id_queue.url
      destination_bucket = aws_s3_bucket.wait_time_bucket.bucket
    }
  }

  timeout = 30
}

resource "aws_lambda_permission" "park_id_lambda" {
  function_name = aws_lambda_function.park_id_lambda.function_name
  principal     = "events.amazonaws.com"
  action        = "lambda:InvokeFunction"
  source_arn    = aws_cloudwatch_event_rule.rule.arn
}

resource "aws_iam_role" "park_id_lambda" {
  name = "park_id_lambda_${var.env_name}"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = "sts:AssumeRole"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "park_id_lambda" {
  name = "park_id_lambda_${var.env_name}"
  role = aws_iam_role.park_id_lambda.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
        ]
        Resource = "${aws_sqs_queue.park_id_queue.arn}"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
        ]
        Resource = [
          "${aws_s3_bucket.wait_time_bucket.arn}",
          "${aws_s3_bucket.wait_time_bucket.arn}/*"
        ]
      }
    ]
  })
}
