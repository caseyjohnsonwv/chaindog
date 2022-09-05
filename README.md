# Chaindog

A serverless SMS wrapper on [Queue-Times](https://queue-times.com/), a public data source for theme park wait times.

---

## Prerequisites

1. Install Terraform.
2. Install Docker and start the Docker daemon.
3. Configure a default AWS profile in `.aws/credentials`.
4. Provision a phone number capable of SMS on [Twilio](https://twilio.com/).
5. Create an S3 bucket for your Terraform state.

---

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
5. Run `terraform init`, then `terraform apply`. Type `yes` when prompted.
6. Copy the output `twilio_webhook_target_url` and paste it as the `A MESSAGE COMES IN` webhook target of your phone number in the Twilio console. Set the method to `HTTP POST`.
7. Send a text to your Twilio phone number. For example:
```
Cedar Point
Steel Vengeance
30
```

---

## Managing Multiple Environments

The variable `upstream_env_name` in `terraform.tfvars` allows lower environments to optionally plug into data from upper environments.
This is to reduce your impact on the upstream data source Queue-Times; it also reduces the number of Lambda functions executing concurrently in your AWS account.

To create separate production and development environments **consuming the same data**:
1. Follow the Quickstart guide for a workspace named `dev`.
2. Follow the Quickstart guide again for a workspace named `prod`. When setting variables in `terraform.tfvars`, change the Twilio phone number to a new number for the new environment. Also add the below variable:
```
upstream_env_name = "prod"
```

After completing the Quickstart guide the second time, `dev` will be consuming from SNS topic `notifcation_topic_prod` and pointing to S3 bucket `wait-time-bucket-prod`, but using its own Lambda functions, Dynamo table, Twilio phone number, etc.
This allows you to reuse the data from `prod` while safely developing new SMS features in an isolated `dev` environment.
