variable "region" {
  description = "AWS region"
  type        = string
}

variable "sns_topic_arn" {
  description = "SNS Topic ARN"
  type        = string
}

variable "lambda_role_arn" {
  description = "ARN of the IAM role for Lambda execution"
  type        = string
}

variable "lambda_config" {
  description = "Configuration for Lambda functions"
  type = object({
    increase_iops = object({
      filename    = string
      handler     = string
      runtime     = string
      timeout     = number
      memory_size = number
    })
    setup_alarms = object({
      filename    = string
      handler     = string
      runtime     = string
      timeout     = number
      memory_size = number
    })
  })
}

variable "tag_key" {
  description = "Tag key to filter EC2 instances"
  type        = string
}

variable "tag_value" {
  description = "Tag value to filter EC2 instances"
  type        = string
}

variable "regions" {
  description = "List of regions for Setup_CloudWatch_Alarms to manage"
  type        = list(string)
  default     = ["us-east-2", "us-west-2"]
}

variable "single_region" {
  description = "Deploy Setup_CloudWatch_Alarms in a single region only"
  type        = bool
  default     = false
}
