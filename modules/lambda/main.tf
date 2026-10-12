data "aws_caller_identity" "current" {}

resource "aws_lambda_function" "increase_iops" {
  function_name = "Modify_Volume_When_Triggered"
  handler       = var.lambda_config.increase_iops.handler
  runtime       = var.lambda_config.increase_iops.runtime
  role          = var.lambda_role_arn
  filename      = var.lambda_config.increase_iops.filename
  timeout       = var.lambda_config.increase_iops.timeout
  memory_size   = var.lambda_config.increase_iops.memory_size

  environment {
    variables = {
      SNS_TOPIC_ARN = var.sns_topic_arn
    }
  }
}

resource "aws_lambda_function" "setup_alarms" {
  count         = var.single_region ? 0 : 1  # Deploy only if single_region is false
  function_name = "Setup_CloudWatch_Alarms"
  handler       = var.lambda_config.setup_alarms.handler
  runtime       = var.lambda_config.setup_alarms.runtime
  role          = var.lambda_role_arn
  filename      = var.lambda_config.setup_alarms.filename
  timeout       = var.lambda_config.setup_alarms.timeout
  memory_size   = var.lambda_config.setup_alarms.memory_size

  environment {
    variables = {
      TAG_KEY   = var.tag_key
      TAG_VALUE = var.tag_value
      REGIONS   = join(",", var.regions)  # Pass regions as a comma-separated string
    }
  }
}

resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.increase_iops.function_name
  principal     = "lambda.alarms.cloudwatch.amazonaws.com"
  source_arn    = "arn:aws:cloudwatch:${var.region}:${data.aws_caller_identity.current.account_id}:alarm:*"
}

resource "aws_cloudwatch_event_rule" "trigger_lambda2_hourly" {
  count               = var.single_region ? 0 : 1  # Only in one region
  name                = "trigger_lambda2_every_2_hours"
  description         = "Trigger Lambda2 every 2 hours"
  schedule_expression = "rate(2 hours)"
}

resource "aws_cloudwatch_event_target" "lambda2_target" {
  count     = var.single_region ? 0 : 1  # Only in one region
  rule      = aws_cloudwatch_event_rule.trigger_lambda2_hourly[0].name
  target_id = "Lambda2Target"
  arn       = aws_lambda_function.setup_alarms[0].arn
}

resource "aws_lambda_permission" "allow_eventbridge_lambda2" {
  count         = var.single_region ? 0 : 1  # Only in one region
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.setup_alarms[0].function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.trigger_lambda2_hourly[0].arn
}

output "lambda_arn" {
  value = aws_lambda_function.increase_iops.arn
}

output "lambda2_arn" {
  value = var.single_region ? null : aws_lambda_function.setup_alarms[0].arn
}
