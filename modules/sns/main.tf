terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 4.0"
    }
  }
}

resource "aws_sns_topic" "iops_alerts" {
  name = var.sns_topic_name
}

resource "aws_sns_topic_subscription" "email_subscription" {
  topic_arn = aws_sns_topic.iops_alerts.arn
  protocol  = "email"
  endpoint  = var.email_endpoint
}

output "sns_topic_arn" {
  value = aws_sns_topic.iops_alerts.arn
}
