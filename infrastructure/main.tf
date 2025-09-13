# infrastructure/main.tf
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Provider configuration - works with both LocalStack and AWS
provider "aws" {
  region                      = var.aws_region
  access_key                  = var.aws_access_key
  secret_key                  = var.aws_secret_key
  skip_credentials_validation = var.skip_credentials_validation
  skip_metadata_api_check     = var.skip_metadata_api_check
  skip_requesting_account_id  = var.skip_requesting_account_id
  s3_use_path_style          = var.s3_use_path_style

  # LocalStack endpoints
  dynamic "endpoints" {
    for_each = var.use_localstack ? [1] : []
    content {
      s3             = var.localstack_endpoint
      dynamodb       = var.localstack_endpoint
      cloudformation = var.localstack_endpoint
      cloudwatch     = var.localstack_endpoint
      iam            = var.localstack_endpoint
      lambda         = var.localstack_endpoint
      sns            = var.localstack_endpoint
      sqs            = var.localstack_endpoint
    }
  }
}

# S3 buckets for Slop app
module "s3_buckets" {
  source = "./modules/s3"
  
  environment = var.environment
  app_name    = var.app_name
  
  # Video storage configuration
  enable_versioning = var.environment == "prod"
  enable_encryption = var.environment != "local"
  
  tags = {
    Environment = var.environment
    Project     = "slop"
    ManagedBy   = "terraform"
  }
}

# IAM roles and policies
module "iam" {
  source = "./modules/iam"
  
  environment = var.environment
  app_name    = var.app_name
  bucket_name = module.s3_buckets.videos_bucket_name
  bucket_arn  = module.s3_buckets.videos_bucket_arn
  
  tags = {
    Environment = var.environment
    Project     = "slop"
    ManagedBy   = "terraform"
  }
} 