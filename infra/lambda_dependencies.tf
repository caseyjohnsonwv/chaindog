resource "aws_lambda_layer_version" "dependencies" {
  filename            = "${local.artifacts_path}/dependencies.zip"
  layer_name          = "dependencies_${terraform.workspace}"
  compatible_runtimes = ["python3.8"]
}
