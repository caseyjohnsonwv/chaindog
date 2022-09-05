resource "aws_lambda_function" "sms_lambda" {
  filename      = "${local.artifacts_path}/sms_lambda.zip"
  function_name = "sms_lambda_${var.env_name}"
  role          = aws_iam_role.sms_lambda.arn
  handler       = "main.lambda_handler"
  runtime       = "python3.8"
  layers        = var.lambda_layer_arns

  environment {
    variables = {
      twilio_account_sid  = var.twilio_account_sid
      twilio_auth_token   = var.twilio_auth_token
      twilio_phone_number = var.twilio_phone_number
    }
  }

  timeout = 5
}

resource "aws_lambda_permission" "sms_lambda" {
  function_name = aws_lambda_function.sms_lambda.function_name
  principal     = "sns.amazonaws.com"
  action        = "lambda:InvokeFunction"
  source_arn    = aws_sns_topic.sms_topic.arn
}

resource "aws_sns_topic_subscription" "sms_lambda" {
  topic_arn = aws_sns_topic.sms_topic.arn
  endpoint  = aws_lambda_function.sms_lambda.arn
  protocol  = "lambda"
}

resource "aws_iam_role" "sms_lambda" {
  name = "sms_lambda_${var.env_name}"
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

resource "aws_iam_role_policy" "sms_lambda" {
  name = "sms_lambda_${var.env_name}"
  role = aws_iam_role.sms_lambda.id
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
    ]
  })
}
