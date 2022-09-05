terraform {
  backend "s3" {
    bucket = "caseyjohnsonwv-tfstate"
    key    = "chaindog.json"
    region = "us-east-2"
  }
}
