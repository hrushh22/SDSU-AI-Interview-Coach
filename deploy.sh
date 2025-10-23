#!/bin/bash

# AI Interview Coach - Deployment Script
# This script deploys the complete infrastructure and Lambda functions to AWS

set -e  # Exit on error

echo "🚀 AI Interview Coach - Deployment Script"
echo "=========================================="

# Configuration
STACK_NAME="interview-coach-stack"
ENVIRONMENT="dev"
AWS_REGION="${AWS_REGION:-us-west-2}"
# Validate AWS CLI and credentials
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install AWS CLI first."
    exit 1
fi

if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Please run 'aws configure' first."
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "📋 Deployment Configuration:"
echo "   Stack Name: $STACK_NAME"
echo "   Environment: $ENVIRONMENT"
echo "   Region: $AWS_REGION"
echo "   Account ID: $ACCOUNT_ID"
echo ""

# Step 1: Package Lambda functions
echo "📦 Step 1: Packaging Lambda functions..."

package_lambda() {
    local function_name=$1
    local source_dir=$2
    
    echo "   Packaging $function_name..."
    
    cd "$source_dir"
    
    # Create deployment package
    rm -f function.zip
    zip -r function.zip . -x "*.pyc" "__pycache__/*" "*.git/*" "tests/*"
    
    cd - > /dev/null
    
    echo "   ✅ $function_name packaged"
}

# Package each Lambda function
package_lambda "interview-orchestrator" "backend/lambda/interview_orchestrator"
package_lambda "audio-processor" "backend/lambda/audio_processor"
package_lambda "resume-analyzer" "backend/lambda/resume_analyzer"
package_lambda "feedback-generator" "backend/lambda/feedback_generator"

echo ""

# Step 2: Deploy CloudFormation Stack
echo "📤 Step 2: Deploying CloudFormation stack..."

aws cloudformation deploy \
    --template-file infrastructure/cloudformation/interview-coach-stack.yaml \
    --stack-name "$STACK_NAME" \
    --parameter-overrides Environment="$ENVIRONMENT" \
    --capabilities CAPABILITY_NAMED_IAM \
    --region "$AWS_REGION"

echo "   ✅ CloudFormation stack deployed"
echo ""

# Step 3: Get stack outputs
echo "📋 Step 3: Retrieving stack outputs..."

get_output() {
    local output
    output=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue" \
        --output text \
        --region "$AWS_REGION" 2>/dev/null)
    
    if [ $? -ne 0 ] || [ -z "$output" ]; then
        echo "❌ Failed to get stack output: $1"
        exit 1
    fi
    
    echo "$output"
}

API_ENDPOINT=$(get_output "ApiEndpoint")
AUDIO_BUCKET=$(get_output "AudioBucketName")
RESUME_BUCKET=$(get_output "ResumeBucketName")
SESSIONS_TABLE=$(get_output "SessionsTableName")

echo "   API Endpoint: $API_ENDPOINT"
echo "   Audio Bucket: $AUDIO_BUCKET"
echo "   Resume Bucket: $RESUME_BUCKET"
echo "   Sessions Table: $SESSIONS_TABLE"
echo ""

# Step 4: Update Lambda function code
echo "🔄 Step 4: Updating Lambda function code..."

update_lambda() {
    local function_name=$1
    local zip_file=$2
    
    echo "   Updating $function_name..."
    
    if [ ! -f "$zip_file" ]; then
        echo "   ❌ Zip file not found: $zip_file"
        exit 1
    fi
    
    if ! aws lambda update-function-code \
        --function-name "${function_name}-${ENVIRONMENT}" \
        --zip-file "fileb://$zip_file" \
        --region "$AWS_REGION" \
        > /dev/null 2>&1; then
        echo "   ❌ Failed to update $function_name"
        exit 1
    fi
    
    echo "   ✅ $function_name updated"
}

update_lambda "interview-orchestrator" "backend/lambda/interview_orchestrator/function.zip"
update_lambda "audio-processor" "backend/lambda/audio_processor/function.zip"
update_lambda "resume-analyzer" "backend/lambda/resume_analyzer/function.zip"
update_lambda "feedback-generator" "backend/lambda/feedback_generator/function.zip"

echo ""

# Step 5: Save configuration
echo "💾 Step 5: Saving configuration..."

cat > config/deployment-config.json <<EOF
{
  "environment": "$ENVIRONMENT",
  "region": "$AWS_REGION",
  "accountId": "$ACCOUNT_ID",
  "apiEndpoint": "$API_ENDPOINT",
  "audioBucket": "$AUDIO_BUCKET",
  "resumeBucket": "$RESUME_BUCKET",
  "sessionsTable": "$SESSIONS_TABLE",
  "deployedAt": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

echo "   ✅ Configuration saved to config/deployment-config.json"
echo ""

# Step 6: Test deployment
echo "🧪 Step 6: Testing deployment..."

# Test API endpoint
response=$(curl -s -o /dev/null -w "%{http_code}" "${API_ENDPOINT}/interview" \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{"action":"start_session","job_title":"Software Engineer"}' 2>/dev/null || echo "000")

if [ "$response" = "200" ]; then
    echo "   ✅ API endpoint is responding correctly"
else
    echo "   ⚠️  API endpoint returned status code: $response"
fi

echo ""

# Summary
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "📝 Next Steps:"
echo "1. Update frontend configuration with API endpoint:"
echo "   export REACT_APP_API_ENDPOINT='$API_ENDPOINT'"
echo ""
echo "2. Test the API endpoints:"
echo "   curl -X POST $API_ENDPOINT/interview \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"action\":\"start_session\",\"job_title\":\"Software Engineer\"}'"
echo ""
echo "3. Deploy frontend:"
echo "   cd frontend && npm run build"
echo ""
echo "4. View CloudWatch logs:"
echo "   aws logs tail /aws/lambda/interview-orchestrator-$ENVIRONMENT --follow"
echo ""
echo "🎉 Happy interviewing!"