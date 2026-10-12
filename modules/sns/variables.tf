variable "sns_topic_name" {
  description = "Name of the SNS topic"
  type        = string
}

variable "email_endpoint" {
  description = "Email address for SNS subscription"
  type        = string
}
