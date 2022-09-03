resource "aws_lambda_function" "notification_lambda" {
  filename      = "${local.artifacts_path}/notification_lambda.zip"
  function_name = "notification_lambda_${terraform.workspace}"
  role          = aws_iam_role.notification_lambda.arn
  handler       = "main.lambda_handler"
  runtime       = "python3.8"

  layers = [aws_lambda_layer_version.dependencies.arn]

  environment {
    variables = {
      aws_region          = data.aws_region.current.name
      source_bucket       = aws_s3_bucket.wait_time_bucket.bucket
      sns_topic_arn       = aws_sns_topic.sms_topic.arn
      watch_table_name    = aws_dynamodb_table.watch_table.name
      dynamodb_index_name = "search_by_park_id"
    }
  }

  timeout = 30
}

resource "aws_lambda_permission" "notification_lambda" {
  function_name = aws_lambda_function.notification_lambda.function_name
  principal     = "sns.amazonaws.com"
  action        = "lambda:InvokeFunction"
  source_arn    = aws_sns_topic.notification_topic.arn
}

resource "aws_sns_topic_subscription" "notification_lambda" {
  topic_arn = aws_sns_topic.notification_topic.arn
  endpoint  = aws_lambda_function.notification_lambda.arn
  protocol  = "lambda"
}

resource "aws_iam_role" "notification_lambda" {
  name = "notification_lambda_${terraform.workspace}"
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
  name = "notification_lambda_${terraform.workspace}"
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
          "${aws_s3_bucket.wait_time_bucket.arn}",
          "${aws_s3_bucket.wait_time_bucket.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:DeleteItem",
          "dynamodb:Query",
        ]
        Resource = [
          "${aws_dynamodb_table.watch_table.arn}",
          "${aws_dynamodb_table.watch_table.arn}/*"
        ]
      }
    ]
  })
}
