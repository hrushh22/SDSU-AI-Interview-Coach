# 🎤 AI Interview Coach

AWS-powered mock interview system with real-time AI feedback using Next.js + FastAPI.

## Features
- 🎙️ Voice recording with Amazon Transcribe
- 🤖 AI feedback using Claude (Bedrock)
- 📄 Resume upload and analysis
- 🔊 Text-to-speech questions (Polly)
- 📊 Performance metrics and progress tracking
- 💾 Interview session summaries stored in DynamoDB
- 🎯 Dynamic question generation based on resume + job description
- 🔄 AI-powered follow-up questions
- 💬 Full conversation history tracking

## Tech Stack
- **Frontend:** Next.js 15, TypeScript, shadcn/ui
- **Backend:** FastAPI, Python 3.11
- **AWS Services:** Transcribe, Bedrock (Claude), Polly, S3, DynamoDB

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.9+
- AWS credentials

### 1. Clone & Setup
```bash
git clone <your-repo-url>
cd AI-interview
```

### 2. Configure AWS Credentials
Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and add your AWS credentials.

### 3. Create AWS Resources
```bash
# Create S3 bucket
aws s3 mb s3://ai-interview-audio-temp --region us-west-2

# Create DynamoDB table
cd backend_api
python setup_dynamodb.py
```

### 4. Start Backend
```bash
cd backend_api
pip install -r requirements.txt

# Set AWS credentials
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AWS_SESSION_TOKEN="your-token"

uvicorn main:app --reload --port 8000
```

### 5. Start Frontend
```bash
cd frontend
npm install
npm run dev
```

Visit http://localhost:3000

## API Endpoints

- `POST /start-interview` - Start interview session with dynamic questions
- `POST /upload-resume` - Upload PDF/text resume
- `POST /transcribe-audio` - Transcribe audio via Amazon Transcribe
- `POST /text-to-speech` - Generate speech via Amazon Polly
- `POST /get-feedback` - Get AI feedback (with optional follow-up)
- `POST /get-next-question` - Get next question from session
- `GET /session/{session_id}` - Retrieve session data
- `POST /complete-session/{session_id}` - Mark session complete

## Environment Variables

Backend requires:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_SESSION_TOKEN` (if using temporary credentials)
- `S3_BUCKET` (default: ai-interview-audio-temp)
- `AWS_DEFAULT_REGION` (default: us-west-2)

## How It Works

1. **Input**: User provides job title, job description, and resume
2. **Parsing**: AI extracts structured data from resume and job description
3. **Question Generation**: Claude generates 4-5 customized questions based on:
   - Skills overlap/gaps between resume and job requirements
   - Technical skills mentioned in both documents
   - Company values and behavioral expectations
4. **Interview Flow**: 
   - User answers each question via voice recording
   - AI provides detailed feedback on content and delivery
   - Optional follow-up questions probe deeper into responses
5. **Storage**: All conversations stored in DynamoDB for review
6. **Summary**: Complete interview history with metrics and feedback

## Key Improvements

✅ **No More Hardcoded Questions** - Questions dynamically generated per candidate
✅ **Personalized Interviews** - Based on actual resume and job requirements
✅ **Follow-up Questions** - AI asks clarifying questions based on answers
✅ **Conversation Storage** - All Q&A stored in DynamoDB
✅ **Session Management** - Track multiple interview sessions

## License
MIT
