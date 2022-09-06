variable "env_name" {
  type = string
}

variable "wait_time_bucket_name" {
  type = string
}

variable "notification_topic_name" {
  type = string
}

variable "lambda_layer_arns" {
  type    = list(string)
  default = []
}

variable "twilio_account_sid" {
  type      = string
  sensitive = true
}

variable "twilio_auth_token" {
  type      = string
  sensitive = true
}

variable "twilio_phone_number" {
  type      = string
  sensitive = true
}

variable "watch_expiration_window_seconds" {
  type    = number
  default = 7200
}
