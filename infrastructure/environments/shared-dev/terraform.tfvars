environment = "shared-dev"
app_name    = "slop"
aws_region  = "us-east-2"

# Real AWS configuration (no LocalStack)
use_localstack              = false
skip_credentials_validation = false
skip_metadata_api_check     = false
skip_requesting_account_id  = false
s3_use_path_style          = false

# AWS credentials will come from:
# - Account owner: AWS CLI (aws configure)
# - Team members: Identity Center SSO (aws configure sso)
# - Production: IAM roles

# Note: No hardcoded access keys needed!
# Terraform will use the same credential chain as your application 