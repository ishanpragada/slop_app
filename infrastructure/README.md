# 🏗️ Slop Infrastructure

This directory contains Terraform configurations for Slop's AWS infrastructure for development and production environments.

## 📁 Structure

```
infrastructure/
├── main.tf              # Main Terraform configuration
├── variables.tf         # Input variables
├── outputs.tf          # Output values
├── environments/       # Environment-specific configurations
│   ├── dev/            # Development environment
│   ├── shared-dev/     # Shared development environment
│   └── prod/           # Production environment
└── modules/            # Reusable Terraform modules
    ├── s3/             # S3 bucket configurations
    └── iam/            # IAM roles and policies
```

## 🚀 Quick Start

### 1. Configure AWS Credentials

```bash
# Option 1: AWS CLI
aws configure

# Option 2: AWS SSO (recommended for teams)
aws configure sso

# Option 3: Environment variables
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
```

### 2. Deploy Development Infrastructure

```bash
# Initialize Terraform
cd infrastructure
terraform init

# Plan deployment
terraform plan -var-file=environments/dev/terraform.tfvars

# Apply infrastructure
terraform apply -var-file=environments/dev/terraform.tfvars
```

## 🪣 S3 Buckets

The infrastructure creates three S3 buckets for each environment:

| Bucket | Purpose | Content Type |
|--------|---------|-------------|
| `slop-videos-{env}` | Video storage | MP4 files |
| `slop-thumbnails-{env}` | Thumbnail images | JPEG files |
| `slop-metadata-{env}` | Video metadata | JSON files with video info |

### Configuration by Environment

| Feature | Dev | Shared-Dev | Prod |
|---------|-----|------------|------|
| **Encryption** | ✅ AES256 | ✅ AES256 | ✅ AES256 |
| **Versioning** | ❌ Disabled | ❌ Disabled | ✅ Enabled |
| **Lifecycle** | ❌ None | ❌ None | ✅ IA → Glacier |
| **Access** | 🌐 Public read | 🌐 Public read | 🔒 Controlled |

## 🧪 Testing the Setup

### Test S3 Integration

```bash
# From backend directory
python upload_video_test.py
```

### Test with AWS CLI

```bash
# List your buckets
aws s3 ls

# Upload test file
echo "test" | aws s3 cp - s3://slop-videos-dev/test.txt

# Download test file
aws s3 cp s3://slop-videos-dev/test.txt -
```

### View AWS Console

- S3 Console: https://s3.console.aws.amazon.com/s3/buckets/
- IAM Console: https://console.aws.amazon.com/iam/

## 🔄 Environment Management

### Deploy to Development

```bash
# Configure AWS credentials
aws configure

# Deploy to dev
terraform apply -var-file=environments/dev/terraform.tfvars
```

### Deploy to Shared Development

```bash
# Deploy to shared development
terraform apply -var-file=environments/shared-dev/terraform.tfvars
```

### Deploy to Production

```bash
# Deploy to production
terraform apply -var-file=environments/prod/terraform.tfvars
```

## 📊 Outputs

After applying Terraform, you'll get important outputs:

```bash
terraform output
```

Example outputs:
```
videos_bucket_name = "slop-videos-dev"
videos_bucket_url = "https://slop-videos-dev.s3.us-east-1.amazonaws.com"
aws_config = {
  region = "us-east-1"
  environment = "dev"
}
```

## 🔧 Backend Integration

Your FastAPI backend automatically detects the environment:

```python
from app.services.aws_service import AWSService

# Automatically uses your AWS credentials
aws_service = AWSService()

# Upload video
video_url = aws_service.upload_video(video_data, video_id)

# Save metadata
metadata_url = aws_service.save_video_metadata(video_id, metadata)
```

## 🐛 Troubleshooting

### AWS Credentials Issues

```bash
# Check current AWS identity
aws sts get-caller-identity

# Check AWS configuration
aws configure list

# Test S3 access
aws s3 ls
```

### Terraform Errors

```bash
# Clean Terraform state
rm -rf .terraform .terraform.lock.hcl

# Re-initialize
terraform init

# Check AWS connectivity
aws sts get-caller-identity
```

### Permission Errors

```bash
# Check IAM policies
terraform plan -var-file=environments/dev/terraform.tfvars

# Verify bucket policies
aws s3api get-bucket-policy --bucket slop-videos-dev
```

## 🚀 Production Deployment

### Prerequisites for AWS

1. **AWS Account** with appropriate permissions
2. **S3 bucket names** must be globally unique
3. **IAM permissions** for Terraform
4. **Route53** (optional) for custom domains

### Production Checklist

- [ ] Update bucket names in `environments/prod/terraform.tfvars`
- [ ] Configure proper CORS origins
- [ ] Set up CloudFront distribution
- [ ] Enable CloudTrail logging
- [ ] Configure backup strategies
- [ ] Set up monitoring and alerts

### Cost Optimization

```bash
# Estimate costs
terraform plan -var-file=environments/prod/terraform.tfvars

# Monitor usage
aws s3api list-objects-v2 --bucket your-prod-bucket --query 'sum(Contents[].Size)'
```

## 📚 Additional Resources

- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS S3 Best Practices](https://docs.aws.amazon.com/AmazonS3/latest/userguide/best-practices.html)
- [Boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [AWS CLI Documentation](https://docs.aws.amazon.com/cli/) 