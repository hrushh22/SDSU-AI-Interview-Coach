# Next.js + FastAPI Setup

## Prerequisites
- Node.js 18+
- Python 3.9+
- AWS credentials configured

## Setup Steps

### 1. Create S3 Bucket for Audio
```bash
aws s3 mb s3://ai-interview-audio-temp --region us-west-2
```

### 2. Backend Setup
```bash
cd backend_api
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

**IMPORTANT: Refresh AWS credentials first!**
See `refresh_credentials.md` for instructions.

Set AWS credentials (Windows):
```bash
set AWS_ACCESS_KEY_ID=your_key
set AWS_SECRET_ACCESS_KEY=your_secret
set AWS_SESSION_TOKEN=your_token
```

Or create `.env` file in backend_api/ (copy from .env.example)

Run backend:
```bash
uvicorn main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: http://localhost:3000
Backend API at: http://localhost:8000

## How It Works

1. User enters job title and starts interview
2. Click "Start Recording" to record audio answer
3. Audio is sent to Amazon Transcribe via FastAPI
4. Transcript is displayed and sent to Claude for feedback
5. User can proceed to next question

## API Endpoints

- `POST /start-interview` - Get interview question
- `POST /transcribe-audio` - Transcribe audio file
- `POST /get-feedback` - Get AI feedback on response
