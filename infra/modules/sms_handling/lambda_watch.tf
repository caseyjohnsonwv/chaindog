resource "aws_lambda_function" "watch_lambda" {
  filename      = "${local.artifacts_path}/watch_lambda.zip"
  function_name = "watch_lambda_${var.env_name}"
  role          = aws_iam_role.watch_lambda.arn
  handler       = "main.lambda_handler"
  runtime       = "python3.8"
  layers        = var.lambda_layer_arns

  environment {
    variables = {
      aws_region                      = data.aws_region.current.name
      source_bucket                   = data.aws_s3_bucket.wait_time_bucket.bucket
      watch_table_name                = aws_dynamodb_table.watch_table.name
      dynamodb_index_name             = "search_by_phone_number"
      watch_expiration_window_seconds = 7200
    }
  }

  timeout = 10
}

resource "aws_lambda_permission" "watch_lambda" {
  function_name = aws_lambda_function.watch_lambda.function_name
  principal     = "apigateway.amazonaws.com"
  action        = "lambda:InvokeFunction"
}

resource "aws_iam_role" "watch_lambda" {
  name = "watch_lambda_${var.env_name}"
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

resource "aws_iam_role_policy" "watch_lambda" {
  name = "watch_lambda_${var.env_name}"
  role = aws_iam_role.watch_lambda.id
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
          "dynamodb:PutItem",
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
