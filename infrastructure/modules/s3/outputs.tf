# infrastructure/modules/s3/outputs.tf

output "videos_bucket_name" {
  description = "Name of the videos S3 bucket"
  value       = aws_s3_bucket.videos.bucket
}

output "videos_bucket_arn" {
  description = "ARN of the videos S3 bucket"
  value       = aws_s3_bucket.videos.arn
}

output "videos_bucket_domain_name" {
  description = "Domain name of the videos S3 bucket"
  value       = aws_s3_bucket.videos.bucket_domain_name
}

output "thumbnails_bucket_name" {
  description = "Name of the thumbnails S3 bucket"
  value       = aws_s3_bucket.thumbnails.bucket
}

output "thumbnails_bucket_arn" {
  description = "ARN of the thumbnails S3 bucket"
  value       = aws_s3_bucket.thumbnails.arn
}
