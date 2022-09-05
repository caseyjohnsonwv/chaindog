resource "aws_dynamodb_table" "watch_table" {
  name           = "Watches_${terraform.workspace}"
  hash_key       = "watch_id"
  billing_mode   = "PROVISIONED"
  read_capacity  = 10
  write_capacity = 10

  global_secondary_index {
    hash_key        = "park_id"
    range_key       = "ride_id"
    name            = "search_by_park_id"
    projection_type = "ALL"
    read_capacity   = 10
    write_capacity  = 10
  }

  global_secondary_index {
    hash_key        = "phone_number"
    name            = "search_by_phone_number"
    projection_type = "ALL"
    read_capacity   = 10
    write_capacity  = 10
  }

  global_secondary_index {
    hash_key        = "expiration"
    name            = "search_by_expiration"
    projection_type = "ALL"
    read_capacity   = 10
    write_capacity  = 10
  }

  attribute {
    name = "watch_id"
    type = "S"
  }

  attribute {
    name = "park_id"
    type = "N"
  }

  attribute {
    name = "ride_id"
    type = "N"
  }

  attribute {
    name = "phone_number"
    type = "S"
  }

  attribute {
    name = "expiration"
    type = "S"
  }
}
