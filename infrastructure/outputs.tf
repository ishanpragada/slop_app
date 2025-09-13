# infrastructure/outputs.tf

# S3 Bucket Outputs
output "videos_bucket_name" {
  description = "Name of the videos S3 bucket"
  value       = module.s3_buckets.videos_bucket_name
}

output "thumbnails_bucket_name" {
  description = "Name of the thumbnails S3 bucket"
  value       = module.s3_buckets.thumbnails_bucket_name
}


output "videos_bucket_url" {
  description = "URL of the videos bucket for LocalStack"
  value       = var.use_localstack ? "${var.localstack_endpoint}/${module.s3_buckets.videos_bucket_name}" : "https://${module.s3_buckets.videos_bucket_name}.s3.${var.aws_region}.amazonaws.com"
}

output "thumbnails_bucket_url" {
  description = "URL of the thumbnails bucket for LocalStack"
  value       = var.use_localstack ? "${var.localstack_endpoint}/${module.s3_buckets.thumbnails_bucket_name}" : "https://${module.s3_buckets.thumbnails_bucket_name}.s3.${var.aws_region}.amazonaws.com"
}

# Environment configuration for backend
output "aws_config" {
  description = "AWS configuration for backend services"
  value = {
    region          = var.aws_region
    use_localstack  = var.use_localstack
    endpoint_url    = var.use_localstack ? var.localstack_endpoint : null
    s3_use_path_style = var.s3_use_path_style
  }
  sensitive = false
} 