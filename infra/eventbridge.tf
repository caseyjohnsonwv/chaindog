resource "aws_cloudwatch_event_rule" "rule" {
  name                = "invoke_park_id_lambda_${terraform.workspace}"
  schedule_expression = "cron(0/5 * * * ? *)"
}

resource "aws_cloudwatch_event_target" "target" {
  rule = aws_cloudwatch_event_rule.rule.name
  arn  = aws_lambda_function.park_id_lambda.arn
}
