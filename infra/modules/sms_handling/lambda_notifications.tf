resource "aws_lambda_function" "notification_lambda" {
  filename      = "${local.artifacts_path}/notification_lambda.zip"
  function_name = "notification_lambda_${var.env_name}"
  role          = aws_iam_role.notification_lambda.arn
  handler       = "main.lambda_handler"
  runtime       = "python3.8"
  layers        = var.lambda_layer_arns

  environment {
    variables = {
      aws_region                     = data.aws_region.current.name
      source_bucket                  = data.aws_s3_bucket.wait_time_bucket.bucket
      sns_topic_arn                  = aws_sns_topic.sms_topic.arn
      watch_table_name               = aws_dynamodb_table.watch_table.name
      dynamodb_index_name            = "search_by_park_id"
      watch_extension_window_seconds = "${ceil(var.watch_expiration_window_seconds/4)}"
    }
  }

  timeout = 30
}

resource "aws_lambda_permission" "notification_lambda" {
  function_name = aws_lambda_function.notification_lambda.function_name
  principal     = "sns.amazonaws.com"
  action        = "lambda:InvokeFunction"
  source_arn    = data.aws_sns_topic.notification_topic.arn
}

resource "aws_sns_topic_subscription" "notification_lambda" {
  topic_arn = data.aws_sns_topic.notification_topic.arn
  endpoint  = aws_lambda_function.notification_lambda.arn
  protocol  = "lambda"
}

resource "aws_iam_role" "notification_lambda" {
  name = "notification_lambda_${var.env_name}"
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

resource "aws_iam_role_policy" "notification_lambda" {
  name = "notification_lambda_${var.env_name}"
  role = aws_iam_role.notification_lambda.id
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
          "sns:Publish",
        ]
        Resource = "${aws_sns_topic.sms_topic.arn}"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
        ]
        Resource = [
          "${data.aws_s3_bucket.wait_time_bucket.arn}",
          "${data.aws_s3_bucket.wait_time_bucket.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:UpdateItem",
        ]
        Resource = [
          "${aws_dynamodb_table.watch_table.arn}",
          "${aws_dynamodb_table.watch_table.arn}/*"
        ]
      }
    ]
  })
}
