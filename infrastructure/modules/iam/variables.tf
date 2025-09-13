# infrastructure/modules/iam/variables.tf

variable "app_name" {
  description = "Application name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "bucket_name" {
  description = "S3 bucket name for permissions"
  type        = string
}

variable "bucket_arn" {
  description = "S3 bucket ARN for permissions"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
} 