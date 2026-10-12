variable "role_name" {
  description = "Name of the IAM role"
  type        = string
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "policy_json" {
  description = "IAM policy JSON"
  type        = string
}
