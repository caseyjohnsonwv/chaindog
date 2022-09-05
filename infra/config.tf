locals {
  artifacts_path = "${path.root}/../src/artifacts"
  templates_path  = "${path.root}/templates"
}


terraform {
  backend "s3" {
    bucket = "caseyjohnsonwv-tfstate"
    key    = "chaindog.json"
    region = "us-east-2"
  }
}


data "aws_region" "current" {}
