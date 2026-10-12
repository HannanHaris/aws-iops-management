variable "default_region" {
  description = "Default AWS region for the provider"
  type        = string
  default     = "us-east-2"
}

variable "regions" {
  description = "List of AWS regions to deploy resources"
  type        = list(string)
  default     = ["us-east-2", "us-west-2"]
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "my_IOPS_project"
}

variable "lambda_role_name" {
  description = "Name of the IAM role for Lambda"
  type        = string
  default     = "lambda_exec_role"
}

variable "sns_topic_name" {
  description = "Name of the SNS topic"
  type        = string
  default     = "IOPs_Alerts"
}

variable "email_endpoint" {
  description = "Email address for SNS subscription"
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
  default = {
    increase_iops = {
      filename    = "./modules/lambda/lambda1.zip"
      handler     = "lambda1.lambda_handler"
      runtime     = "python3.9"
      timeout     = 900
      memory_size = 128
    }
    setup_alarms = {
      filename    = "./modules/lambda/lambda2.zip"
      handler     = "lambda2.lambda_handler"
      runtime     = "python3.9"
      timeout     = 900
      memory_size = 128
    }
  }
}

variable "tag_key" {
  description = "Tag key to filter EC2 instances"
  type        = string
  default     = "env"
}

variable "tag_value" {
  description = "Tag value to filter EC2 instances"
  type        = string
  default     = "k8s"
}

variable "single_region" {
  description = "Deploy Setup_CloudWatch_Alarms in a single region only"
  type        = bool
  default     = false
}
