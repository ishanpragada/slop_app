# infrastructure/variables.tf

variable "environment" {
  description = "Environment name (local, dev, prod)"
  type        = string
  default     = "local"
}

variable "app_name" {
  description = "Application name"
  type        = string
  default     = "slop"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "aws_access_key" {
  description = "AWS access key"
  type        = string
  default     = "test"  # LocalStack default
}

variable "aws_secret_key" {
  description = "AWS secret key"
  type        = string
  default     = "test"  # LocalStack default
}

# LocalStack specific variables
variable "use_localstack" {
  description = "Whether to use LocalStack for local development"
  type        = bool
  default     = true
}

variable "localstack_endpoint" {
  description = "LocalStack endpoint URL"
  type        = string
  default     = "http://localhost:4566"
}

variable "skip_credentials_validation" {
  description = "Skip AWS credentials validation (for LocalStack)"
  type        = bool
  default     = true
}

variable "skip_metadata_api_check" {
  description = "Skip metadata API check (for LocalStack)"
  type        = bool
  default     = true
}

variable "skip_requesting_account_id" {
  description = "Skip requesting account ID (for LocalStack)"
  type        = bool
  default     = true
}

variable "s3_use_path_style" {
  description = "Use path-style S3 URLs (required for LocalStack)"
  type        = bool
  default     = true
} 