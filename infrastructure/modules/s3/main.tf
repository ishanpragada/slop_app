# infrastructure/modules/s3/main.tf

# Main videos bucket
resource "aws_s3_bucket" "videos" {
  bucket = "${var.app_name}-videos-${var.environment}"

  tags = merge(var.tags, {
    Name        = "${var.app_name}-videos-${var.environment}"
    Purpose     = "Video storage"
    ContentType = "videos"
  })
}

# Video thumbnails bucket
resource "aws_s3_bucket" "thumbnails" {
  bucket = "${var.app_name}-thumbnails-${var.environment}"

  tags = merge(var.tags, {
    Name        = "${var.app_name}-thumbnails-${var.environment}"
    Purpose     = "Thumbnail storage"
    ContentType = "images"
  })
}


# Configure versioning for videos bucket
resource "aws_s3_bucket_versioning" "videos_versioning" {
  bucket = aws_s3_bucket.videos.id
  versioning_configuration {
    status = var.enable_versioning ? "Enabled" : "Suspended"
  }
}

# Configure server-side encryption (disabled for LocalStack)
resource "aws_s3_bucket_server_side_encryption_configuration" "videos_encryption" {
  count  = var.enable_encryption ? 1 : 0
  bucket = aws_s3_bucket.videos.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Configure CORS for frontend access
resource "aws_s3_bucket_cors_configuration" "videos_cors" {
  bucket = aws_s3_bucket.videos.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST", "DELETE", "HEAD"]
    allowed_origins = ["*"]  # Restrict this in production
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

# Configure CORS for thumbnails
resource "aws_s3_bucket_cors_configuration" "thumbnails_cors" {
  bucket = aws_s3_bucket.thumbnails.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST", "DELETE", "HEAD"]
    allowed_origins = ["*"]  # Restrict this in production
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

# Lifecycle configuration for cost optimization (not needed for LocalStack)
resource "aws_s3_bucket_lifecycle_configuration" "videos_lifecycle" {
  count  = var.environment == "prod" ? 1 : 0
  bucket = aws_s3_bucket.videos.id

  rule {
    id     = "video_lifecycle"
    status = "Enabled"

    # Move to Infrequent Access after 30 days
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    # Move to Glacier after 90 days
    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    # Delete after 2 years
    expiration {
      days = 730
    }
  }
}

# Public read policy for videos (LocalStack-friendly)
resource "aws_s3_bucket_policy" "videos_public_read" {
  bucket = aws_s3_bucket.videos.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.videos.arn}/*"
      }
    ]
  })
}

# Public read policy for thumbnails
resource "aws_s3_bucket_policy" "thumbnails_public_read" {
  bucket = aws_s3_bucket.thumbnails.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.thumbnails.arn}/*"
      }
    ]
  })
} 