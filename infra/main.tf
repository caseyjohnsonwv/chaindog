locals {
  artifacts_path = "${path.root}/../src/artifacts"

  # enable lower envs to plug into upper env data sources
  create_data_ingestion_module = var.upstream_env_name == null ? 1 : 0
  wait_time_bucket_name        = var.upstream_env_name == null ? module.data_ingestion[0].wait_time_bucket_name : "wait-time-bucket-${var.upstream_env_name}"
  notification_topic_name      = var.upstream_env_name == null ? module.data_ingestion[0].notification_topic_name : "notification_topic_${var.upstream_env_name}"
}

resource "aws_lambda_layer_version" "dependencies" {
  filename            = "${local.artifacts_path}/dependencies.zip"
  layer_name          = "dependencies_${terraform.workspace}"
  compatible_runtimes = ["python3.8"]
}

module "data_ingestion" {
  source   = "./modules/data_ingestion"
  count    = local.create_data_ingestion_module
  env_name = terraform.workspace

  lambda_layer_arns = [
    aws_lambda_layer_version.dependencies.arn
  ]
}

module "sms_handling" {
  source                  = "./modules/sms_handling"
  env_name                = terraform.workspace
  wait_time_bucket_name   = local.wait_time_bucket_name
  notification_topic_name = local.notification_topic_name
  twilio_account_sid      = var.twilio_account_sid
  twilio_auth_token       = var.twilio_auth_token
  twilio_phone_number     = var.twilio_phone_number

  lambda_layer_arns = [
    aws_lambda_layer_version.dependencies.arn
  ]

  depends_on = [
    module.data_ingestion
  ]
}
