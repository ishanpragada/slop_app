# infrastructure/modules/iam/main.tf

# IAM role for the Slop application
resource "aws_iam_role" "slop_app_role" {
  name = "${var.app_name}-app-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

# IAM policy for S3 video operations
resource "aws_iam_policy" "s3_video_policy" {
  name        = "${var.app_name}-s3-video-policy-${var.environment}"
  description = "Policy for S3 video operations"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:GetObjectVersion",
          "s3:PutObjectAcl"
        ]
        Resource = [
          "${var.bucket_arn}/*",
          "${var.bucket_arn}"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
          "s3:GetBucketLocation",
          "s3:GetBucketVersioning"
        ]
        Resource = var.bucket_arn
      }
    ]
  })

  tags = var.tags
}

# Attach policy to role
resource "aws_iam_role_policy_attachment" "slop_app_policy_attachment" {
  role       = aws_iam_role.slop_app_role.name
  policy_arn = aws_iam_policy.s3_video_policy.arn
}

# IAM user for development (LocalStack)
resource "aws_iam_user" "slop_dev_user" {
  count = var.environment == "local" ? 1 : 0
  name  = "${var.app_name}-dev-user"

  tags = var.tags
}

# Access key for development user
resource "aws_iam_access_key" "slop_dev_access_key" {
  count = var.environment == "local" ? 1 : 0
  user  = aws_iam_user.slop_dev_user[0].name
}

# Attach policy to development user
resource "aws_iam_user_policy_attachment" "slop_dev_user_policy" {
  count      = var.environment == "local" ? 1 : 0
  user       = aws_iam_user.slop_dev_user[0].name
  policy_arn = aws_iam_policy.s3_video_policy.arn
} 