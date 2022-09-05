resource "aws_api_gateway_rest_api" "twilio" {
  name = "chaindog_twilio_${terraform.workspace}"
}

resource "aws_api_gateway_resource" "twilio" {
  rest_api_id = aws_api_gateway_rest_api.twilio.id
  parent_id   = aws_api_gateway_rest_api.twilio.root_resource_id
  path_part   = "twilio"
}

resource "aws_api_gateway_method" "twilio" {
  rest_api_id   = aws_api_gateway_rest_api.twilio.id
  resource_id   = aws_api_gateway_resource.twilio.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "twilio" {
  rest_api_id             = aws_api_gateway_rest_api.twilio.id
  resource_id             = aws_api_gateway_resource.twilio.id
  http_method             = aws_api_gateway_method.twilio.http_method
  uri                     = aws_lambda_function.watch_lambda.invoke_arn
  type                    = "AWS"
  integration_http_method = "POST"
  passthrough_behavior    = "WHEN_NO_TEMPLATES"

  request_templates = {
    "application/x-www-form-urlencoded" = file("${local.templates_path}/twilio_integration.template")
  }
}

resource "aws_api_gateway_integration_response" "twilio" {
  rest_api_id = aws_api_gateway_rest_api.twilio.id
  resource_id = aws_api_gateway_resource.twilio.id
  http_method = aws_api_gateway_method.twilio.http_method
  status_code = 200

  response_templates = {
    "application/xml" = file("${local.templates_path}/twilio_integration_response.template")
  }

  depends_on = [
    aws_api_gateway_integration.twilio
  ]
}

resource "aws_api_gateway_method_response" "twilio" {
  rest_api_id = aws_api_gateway_rest_api.twilio.id
  resource_id = aws_api_gateway_resource.twilio.id
  http_method = aws_api_gateway_method.twilio.http_method
  status_code = 200

  response_models = {
    "application/xml" = "Empty"
  }
}

resource "aws_api_gateway_deployment" "twilio" {
  rest_api_id = aws_api_gateway_rest_api.twilio.id

  lifecycle {
    create_before_destroy = true
  }

  triggers = {
    timestamp = sha256(file("${path.root}/apigateway.tf"))
  }

  depends_on = [
    aws_api_gateway_method.twilio,
    aws_api_gateway_integration.twilio,
    aws_api_gateway_integration_response.twilio,
    aws_api_gateway_method_response.twilio,
  ]
}

resource "aws_api_gateway_stage" "twilio" {
  rest_api_id   = aws_api_gateway_rest_api.twilio.id
  deployment_id = aws_api_gateway_deployment.twilio.id
  stage_name    = terraform.workspace
}

resource "aws_iam_role" "twilio" {
  name = "chaindog_twilio_${terraform.workspace}"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "apigateway.amazonaws.com",
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "twilio" {
  name = "chaindog_twilio_${terraform.workspace}"
  role = aws_iam_role.twilio.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "lambda:InvokeFunction"
        Resource = "${aws_lambda_function.watch_lambda.arn}"
      }
    ]
  })
}
