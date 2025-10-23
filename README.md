# 🎤 AI Interview Coach

AWS-powered mock interview system with real-time AI feedback using Next.js + FastAPI.

## Features
- 🎙️ Voice recording with Amazon Transcribe
- 🤖 AI feedback using Claude (Bedrock)
- 📄 Resume upload and analysis
- 🔊 Text-to-speech questions (Polly)
- 📊 Performance metrics and progress tracking
- 💾 Interview session summaries

## Tech Stack
- **Frontend:** Next.js 15, TypeScript, shadcn/ui
- **Backend:** FastAPI, Python 3.11
- **AWS Services:** Transcribe, Bedrock (Claude), Polly, S3

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

### 3. Create S3 Bucket
```bash
aws s3 mb s3://ai-interview-audio-temp --region us-west-2
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

- `POST /start-interview` - Start interview session
- `POST /upload-resume` - Upload PDF/text resume
- `POST /transcribe-audio` - Transcribe audio via Amazon Transcribe
- `POST /text-to-speech` - Generate speech via Amazon Polly
- `POST /get-feedback` - Get AI feedback via Claude

## Environment Variables

Backend requires:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_SESSION_TOKEN` (if using temporary credentials)
- `S3_BUCKET` (default: ai-interview-audio-temp)

## License
MIT
