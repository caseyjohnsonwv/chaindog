# Chaindog

A serverless SMS wrapper on [Queue-Times](https://queue-times.com/), a public data source for theme park wait times.

---

## Prerequisites

1. Install Terraform.
2. Install Docker and start the Docker daemon.
3. Configure a default AWS profile in `.aws/credentials`.
4. Provision a phone number capable of SMS on [Twilio](https://twilio.com/).
5. Create an S3 bucket for your Terraform state.

## Quickstart

1. Inside the `src/` folder, run `python build.py` to build the Lambda artifacts.
2. Inside the `infra/` folder, create a `terraform.tfvars` and populate the below variables:
```
twilio_account_sid  = ""
twilio_auth_token   = ""
twilio_phone_number = ""
```
3. Update the Terraform backend in `config.tf` to point to your Terraform state bucket on S3.
4. Run `terraform workspace new dev` to create a development workspace.
5. Run terraform apply` and type `yes` when prompted.
6. Copy the output `twilio_webhook_target_url` and paste it as the POST request webhook target of your phone number on Twilio.
7. Send a text to your Twilio phone number. For example:
```
Cedar Point
Steel Vengeance
30
```
