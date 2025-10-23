@echo off
REM AI Interview Coach - Windows Deployment Script

echo 🚀 AI Interview Coach - Deployment Script
echo ==========================================

REM Configuration
set STACK_NAME=interview-coach-stack
set ENVIRONMENT=dev
set AWS_REGION=us-west-2

echo 📋 Deployment Configuration:
echo    Stack Name: %STACK_NAME%
echo    Environment: %ENVIRONMENT%
echo    Region: %AWS_REGION%
echo.

REM Check AWS CLI
aws --version >nul 2>&1
if errorlevel 1 (
    echo ❌ AWS CLI not found. Please install AWS CLI first.
    pause
    exit /b 1
)

REM Check AWS credentials
aws sts get-caller-identity >nul 2>&1
if errorlevel 1 (
    echo ❌ AWS credentials not configured. Please run 'aws configure' first.
    pause
    exit /b 1
)

echo ✅ AWS CLI configured

REM Step 1: Package Lambda functions
echo.
echo 📦 Step 1: Packaging Lambda functions...

cd backend\lambda\interview_orchestrator
powershell -Command "Compress-Archive -Path * -DestinationPath function.zip -Force"
cd ..\..\..

cd backend\lambda\audio_processor
powershell -Command "Compress-Archive -Path * -DestinationPath function.zip -Force"
cd ..\..\..

cd backend\lambda\resume_analyzer
powershell -Command "Compress-Archive -Path * -DestinationPath function.zip -Force"
cd ..\..\..

cd backend\lambda\feedback_generator
powershell -Command "Compress-Archive -Path * -DestinationPath function.zip -Force"
cd ..\..\..

echo ✅ Lambda functions packaged

REM Step 2: Deploy CloudFormation Stack
echo.
echo 📤 Step 2: Deploying CloudFormation stack...

aws cloudformation deploy ^
    --template-file infrastructure\cloudformation\interview-coach-stack.yaml ^
    --stack-name %STACK_NAME% ^
    --parameter-overrides Environment=%ENVIRONMENT% ^
    --capabilities CAPABILITY_NAMED_IAM ^
    --region %AWS_REGION%

if errorlevel 1 (
    echo ❌ CloudFormation deployment failed
    pause
    exit /b 1
)

echo ✅ CloudFormation stack deployed

REM Step 3: Get stack outputs
echo.
echo 📋 Step 3: Retrieving stack outputs...

for /f "tokens=*" %%i in ('aws cloudformation describe-stacks --stack-name %STACK_NAME% --query "Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue" --output text --region %AWS_REGION%') do set API_ENDPOINT=%%i
for /f "tokens=*" %%i in ('aws cloudformation describe-stacks --stack-name %STACK_NAME% --query "Stacks[0].Outputs[?OutputKey=='AudioBucketName'].OutputValue" --output text --region %AWS_REGION%') do set AUDIO_BUCKET=%%i
for /f "tokens=*" %%i in ('aws cloudformation describe-stacks --stack-name %STACK_NAME% --query "Stacks[0].Outputs[?OutputKey=='ResumeBucketName'].OutputValue" --output text --region %AWS_REGION%') do set RESUME_BUCKET=%%i
for /f "tokens=*" %%i in ('aws cloudformation describe-stacks --stack-name %STACK_NAME% --query "Stacks[0].Outputs[?OutputKey=='SessionsTableName'].OutputValue" --output text --region %AWS_REGION%') do set SESSIONS_TABLE=%%i

echo    API Endpoint: %API_ENDPOINT%
echo    Audio Bucket: %AUDIO_BUCKET%
echo    Resume Bucket: %RESUME_BUCKET%
echo    Sessions Table: %SESSIONS_TABLE%

REM Step 4: Update Lambda function code
echo.
echo 🔄 Step 4: Updating Lambda function code...

aws lambda update-function-code --function-name interview-orchestrator-%ENVIRONMENT% --zip-file fileb://backend/lambda/interview_orchestrator/function.zip --region %AWS_REGION%
aws lambda update-function-code --function-name audio-processor-%ENVIRONMENT% --zip-file fileb://backend/lambda/audio_processor/function.zip --region %AWS_REGION%
aws lambda update-function-code --function-name resume-analyzer-%ENVIRONMENT% --zip-file fileb://backend/lambda/resume_analyzer/function.zip --region %AWS_REGION%
aws lambda update-function-code --function-name feedback-generator-%ENVIRONMENT% --zip-file fileb://backend/lambda/feedback_generator/function.zip --region %AWS_REGION%

echo ✅ Lambda functions updated

REM Step 5: Save configuration
echo.
echo 💾 Step 5: Saving configuration...

echo { > config\deployment-config.json
echo   "environment": "%ENVIRONMENT%", >> config\deployment-config.json
echo   "region": "%AWS_REGION%", >> config\deployment-config.json
echo   "apiEndpoint": "%API_ENDPOINT%", >> config\deployment-config.json
echo   "audioBucket": "%AUDIO_BUCKET%", >> config\deployment-config.json
echo   "resumeBucket": "%RESUME_BUCKET%", >> config\deployment-config.json
echo   "sessionsTable": "%SESSIONS_TABLE%" >> config\deployment-config.json
echo } >> config\deployment-config.json

echo ✅ Configuration saved

REM Summary
echo.
echo ✅ Deployment Complete!
echo ==========================================
echo.
echo 📝 Your API Endpoint: %API_ENDPOINT%
echo.
echo 📝 Next Steps:
echo 1. Test the API:
echo    curl -X POST %API_ENDPOINT%/interview -H "Content-Type: application/json" -d "{\"action\":\"start_session\",\"job_title\":\"Software Engineer\"}"
echo.
echo 2. Update Streamlit configuration:
echo    Set API_ENDPOINT=%API_ENDPOINT% in your environment
echo.
echo 🎉 Happy interviewing!
pause