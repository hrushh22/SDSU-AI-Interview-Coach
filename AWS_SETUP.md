# AWS Credentials Setup Guide

## 🔑 Getting AWS Credentials

### Option 1: AWS CLI (Recommended)
```bash
# Install AWS CLI
pip install awscli

# Configure credentials
aws configure
```

**You'll need:**
- AWS Access Key ID
- AWS Secret Access Key  
- Default region: `us-west-2`
- Default output format: `json`

### Option 2: Environment Variables
```bash
export AWS_ACCESS_KEY_ID=your-access-key-here
export AWS_SECRET_ACCESS_KEY=your-secret-key-here
export AWS_DEFAULT_REGION=us-west-2
```

### Option 3: Streamlit Secrets
Add to `.streamlit/secrets.toml`:
```toml
[aws]
AWS_ACCESS_KEY_ID = "your-access-key-here"
AWS_SECRET_ACCESS_KEY = "your-secret-key-here"
AWS_DEFAULT_REGION = "us-west-2"
```

## 🏗️ Getting AWS Access Keys

### If you have AWS Account:
1. Go to AWS Console → IAM
2. Create new user or use existing
3. Attach policies:
   - `AmazonBedrockFullAccess`
   - `AmazonDynamoDBFullAccess`
4. Create Access Key → Download credentials

### If you need AWS Account:
1. Go to https://aws.amazon.com
2. Create free account
3. Follow steps above

## 🚀 Quick Test
```bash
# Test AWS connection
aws sts get-caller-identity

# Test Bedrock access
aws bedrock list-foundation-models --region us-west-2
```

## 🔧 Current System Status

**Fixed Issues:**
- ✅ Proper scoring (1-word response = 2/10, not 6/10)
- ✅ Simple voice recording via file upload
- ✅ Whisper transcription working
- ✅ Real-time feedback system

**Voice Recording Options:**
1. **File Upload** (Recommended): Record on phone → Upload → Transcribe
2. **Browser Recording**: Direct recording if streamlit-audiorecorder works

**Scoring System:**
- 1-9 words: 2-3/10 (Too brief)
- 10-29 words: 3-4/10 (Very short)
- 30-49 words: 4-5/10 (Short)
- 50-200 words: 7-9/10 (Good length)
- 200+ words: 6/10 (Too long)

## 🎯 Ready to Run

Once AWS credentials are set up:
```bash
python -m streamlit run streamlit_app.py --server.port 8504
```

The system will:
1. Use AWS Bedrock Claude for real AI feedback
2. Fall back to intelligent local feedback if AWS unavailable
3. Handle voice recording via file upload + Whisper
4. Provide proper scoring based on response quality