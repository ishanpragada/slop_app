# infrastructure/environments/local/terraform.tfvars
# Local development environment with LocalStack

environment = "local"
app_name    = "slop"
aws_region  = "us-east-1"

# LocalStack configuration
use_localstack              = true
localstack_endpoint         = "http://localhost:4566"
skip_credentials_validation = true
skip_metadata_api_check     = true
skip_requesting_account_id  = true
s3_use_path_style          = true

# LocalStack default credentials
aws_access_key = "test"
aws_secret_key = "test" 