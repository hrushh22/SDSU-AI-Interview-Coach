# 🚀 AI Interview Coach - Deployment Guide

## Prerequisites

1. **AWS CLI installed and configured**
   ```bash
   aws --version
   aws configure
   ```

2. **AWS Account with appropriate permissions**
   - Lambda, API Gateway, S3, DynamoDB, IAM, CloudFormation
   - Bedrock access (for Claude model)

3. **PowerShell (for Windows deployment)**

## Quick Deployment

### Option 1: Windows Batch Script
```cmd
deploy.bat
```

### Option 2: Manual Steps

1. **Configure AWS credentials**
   ```bash
   aws configure
   # Enter your AWS Access Key ID, Secret Access Key, Region (us-west-2), and output format (json)
   ```

2. **Deploy infrastructure**
   ```bash
   aws cloudformation deploy \
     --template-file infrastructure/cloudformation/interview-coach-stack.yaml \
     --stack-name interview-coach-stack \
     --parameter-overrides Environment=dev \
     --capabilities CAPABILITY_NAMED_IAM \
     --region us-west-2
   ```

3. **Package and update Lambda functions**
   ```bash
   # Package each function
   cd backend/lambda/interview_orchestrator
   zip -r function.zip .
   cd ../../..

   # Update function code
   aws lambda update-function-code \
     --function-name interview-orchestrator-dev \
     --zip-file fileb://backend/lambda/interview_orchestrator/function.zip
   ```

4. **Get API endpoint**
   ```bash
   aws cloudformation describe-stacks \
     --stack-name interview-coach-stack \
     --query "Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue" \
     --output text
   ```

## Configuration

After deployment, update your environment variables:

```bash
# For Streamlit app
export API_ENDPOINT="https://your-api-id.execute-api.us-west-2.amazonaws.com/dev"

# Run Streamlit
streamlit run streamlit_app.py
```

## Testing

Test your API endpoint:
```bash
curl -X POST https://your-api-endpoint/interview \
  -H "Content-Type: application/json" \
  -d '{"action":"start_session","job_title":"Software Engineer"}'
```

## Troubleshooting

1. **CloudFormation deployment fails**
   - Check IAM permissions
   - Verify region availability for services

2. **Lambda function errors**
   - Check CloudWatch logs: `/aws/lambda/function-name`
   - Verify environment variables

3. **API Gateway 502 errors**
   - Check Lambda function permissions
   - Verify integration configuration

## Clean Up

To remove all resources:
```bash
aws cloudformation delete-stack --stack-name interview-coach-stack
```

## Security Notes

- S3 buckets have lifecycle policies (30-day retention)
- Lambda functions use least-privilege IAM roles
- API Gateway has CORS enabled for development
- Consider adding authentication for production use