provider "aws" {
  region = var.default_region
}

# Define explicit provider aliases for each region
provider "aws" {
  alias  = "us-east-2"
  region = "us-east-2"
}

provider "aws" {
  alias  = "us-west-2"
  region = "us-west-2"
}

# IAM Role for Lambda (uses default provider)
module "iam" {
  source       = "./modules/iam"
  role_name    = var.lambda_role_name
  project_name = var.project_name
  policy_json  = file("${path.module}/policies/lambda_policy.json")
}

# SNS Topics in multiple regions
module "sns_us_east_2" {
  source         = "./modules/sns"
  sns_topic_name = var.sns_topic_name
  email_endpoint = var.email_endpoint
  providers = {
    aws = aws.us-east-2
  }
}

module "sns_us_west_2" {
  source         = "./modules/sns"
  sns_topic_name = var.sns_topic_name
  email_endpoint = var.email_endpoint
  providers = {
    aws = aws.us-west-2
  }
}

# Lambda Functions: Modify_Volume_When_Triggered in both regions
module "lambda_us_east_2" {
  source          = "./modules/lambda"
  region          = "us-east-2"
  sns_topic_arn   = module.sns_us_east_2.sns_topic_arn
  lambda_role_arn = module.iam.lambda_role_arn
  lambda_config   = var.lambda_config
  tag_key         = var.tag_key
  tag_value       = var.tag_value
  single_region   = false # Deploy both Lambdas
  providers = {
    aws = aws.us-east-2
  }
}

module "lambda_us_west_2" {
  source          = "./modules/lambda"
  region          = "us-west-2"
  sns_topic_arn   = module.sns_us_west_2.sns_topic_arn
  lambda_role_arn = module.iam.lambda_role_arn
  lambda_config   = var.lambda_config
  tag_key         = var.tag_key
  tag_value       = var.tag_value
  single_region   = true # Deploy only Lambda 1, skip Lambda 2
  providers = {
    aws = aws.us-west-2
  }
}
