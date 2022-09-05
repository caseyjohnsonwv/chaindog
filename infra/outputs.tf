output "twilio_webhook_target_url" {
  value = "${aws_api_gateway_stage.twilio.invoke_url}${aws_api_gateway_resource.twilio.path}"
}
