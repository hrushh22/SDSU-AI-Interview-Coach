# Refresh AWS Credentials

Your AWS session token has expired. Follow these steps:

## Option 1: AWS Academy (If using AWS Academy)
1. Go to AWS Academy
2. Click "AWS Details" 
3. Click "Show" next to AWS CLI credentials
4. Copy the credentials
5. Update `.streamlit/secrets.toml` with new values

## Option 2: AWS CLI
```bash
aws sts get-session-token
```

## Option 3: Use IAM User (No expiration)
If you have permanent IAM credentials, remove the AWS_SESSION_TOKEN line from secrets.toml

## Quick Fix - Update secrets.toml:
```toml
[aws]
AWS_ACCESS_KEY_ID = "your_new_key"
AWS_SECRET_ACCESS_KEY = "your_new_secret"
AWS_SESSION_TOKEN = "your_new_token"  # Remove this line if using IAM user
AWS_DEFAULT_REGION = "us-west-2"
```

## Then create S3 bucket:
```bash
python setup_s3.py
```

Or manually via AWS CLI:
```bash
aws s3 mb s3://ai-interview-audio-temp --region us-west-2
```
