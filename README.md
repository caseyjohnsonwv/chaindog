# Chaindog

A serverless SMS wrapper on [Queue-Times](https://queue-times.com/), a public data source for theme park wait times.

---

## Prerequisites

1. Install Terraform.
2. Install Docker and start the Docker daemon.
3. Configure a default AWS profile in `.aws/credentials`.
4. Provision a phone number capable of SMS on [Twilio](https://twilio.com/).

## Quickstart

1. Ensure your Docker daemon is running locally, you have a default AWS profile configured in your `.aws/credentials`, and you have Terraform v0.14+ installed.
2. Inside the `src/` folder, run `python build.py` to build the Lambda artifacts.
3. Inside the `infra/` folder, create a `terraform.tfvars` and populate the below variables:
```
twilio_account_sid  = ""
twilio_auth_token   = ""
twilio_phone_number = ""
```
4. Inside the `infra/` folder, run `terraform apply` and type `yes` when prompted.
5. Copy the output `twilio_webhook_target_url` and paste it as the POST request webhook target of your phone number on Twilio.
