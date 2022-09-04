resource "aws_lambda_event_source_mapping" "wait_time_lambda" {
  event_source_arn                   = aws_sqs_queue.park_id_queue.arn
  function_name                      = aws_lambda_function.wait_time_lambda.function_name
  batch_size                         = 100
  maximum_batching_window_in_seconds = 15
}

resource "aws_lambda_function" "wait_time_lambda" {
  filename      = "${local.artifacts_path}/wait_time_lambda.zip"
  function_name = "wait_time_lambda_${terraform.workspace}"
  role          = aws_iam_role.wait_time_lambda.arn
  handler       = "main.lambda_handler"
  runtime       = "python3.8"

  layers = [aws_lambda_layer_version.dependencies.arn]

  environment {
    variables = {
      destination_bucket = aws_s3_bucket.wait_time_bucket.bucket
    }
  }

  timeout = 120
}

resource "aws_lambda_permission" "wait_time_lambda" {
  function_name = aws_lambda_function.wait_time_lambda.function_name
  principal     = "sqs.amazonaws.com"
  action        = "lambda:InvokeFunction"
  source_arn    = aws_sqs_queue.park_id_queue.arn
}

resource "aws_iam_role" "wait_time_lambda" {
  name = "wait_time_lambda_${terraform.workspace}"
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

resource "aws_iam_role_policy" "wait_time_lambda" {
  name = "wait_time_lambda_${terraform.workspace}"
  role = aws_iam_role.wait_time_lambda.id
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
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
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
