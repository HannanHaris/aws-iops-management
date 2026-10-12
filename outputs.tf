output "lambda_role_arn" {
  value = module.iam.lambda_role_arn
}

output "sns_topic_arns" {
  value = {
    "us-east-2" = module.sns_us_east_2.sns_topic_arn
    "us-west-2" = module.sns_us_west_2.sns_topic_arn
  }
}

output "lambda_arns" {
  value = {
    "us-east-2" = module.lambda_us_east_2.lambda_arn
    "us-west-2" = module.lambda_us_west_2.lambda_arn
  }
}

output "lambda2_arn" {
  value = module.lambda_us_east_2.lambda2_arn  # Only in us-east-2
}
