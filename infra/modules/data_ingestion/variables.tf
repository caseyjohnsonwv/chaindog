variable "env_name" {
  type = string
}

variable "lambda_layer_arns" {
  type    = list(string)
  default = []
}
