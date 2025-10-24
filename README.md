# 🎤 AI Interview Coach

AWS-powered mock interview system with real-time AI feedback, body language analysis, and text-to-speech using Next.js + FastAPI.

## Features

### Interview Modes
- 📚 **Practice Mode** - Instant feedback after each question, end anytime
- 🎯 **Mock Mode** - 10-minute timed interview with comprehensive end report

### Core Capabilities
- 🎙️ Voice recording with browser Speech Recognition API
- 🤖 Brutally honest AI feedback using Claude 3.5 Sonnet (Bedrock)
- 📄 Resume upload and intelligent parsing (PDF/text)
- 🔊 Text-to-speech questions using Amazon Polly (Neural voice)
- 📹 **Real-time body language analysis** - Webcam monitoring every 5 seconds
- 🚨 **Immediate alerts** - Pop-up warnings for posture, eye contact, multiple people
- 📊 Strict performance scoring (0-10 scale)
- 💾 Interview session storage in DynamoDB
- 🎯 Dynamic question generation based on resume + job description
- 💬 Full conversation history tracking

### Body Language Analysis
- Eye contact monitoring
- Posture assessment
- Engagement detection
- Multiple people detection
- Fidgeting and head shaking alerts
- Professional presence scoring
- Comprehensive post-interview report

## Tech Stack

### Frontend
- **Framework:** Next.js 15 (App Router)
- **Language:** TypeScript
- **UI:** shadcn/ui, Tailwind CSS
- **Speech:** Browser Speech Recognition API
- **Video:** MediaDevices API for webcam

### Backend
- **Framework:** FastAPI
- **Language:** Python 3.11
- **Environment:** python-dotenv

### AWS Services
- **Bedrock (Claude 3.5 Sonnet)** - Answer feedback & body language analysis
- **Polly (Neural)** - Text-to-speech for questions
- **S3** - Temporary audio storage
- **DynamoDB** - Session and conversation storage

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.9+
- AWS credentials with access to Bedrock, Polly, S3, DynamoDB

### 1. Clone Repository
```bash
git clone https://github.com/hrushh22/SDSU-AI-Interview-Coach.git
cd AI-interview
```

### 2. Setup Backend
```bash
cd backend_api

# Create virtual environment
python -m venv venv
source venv/Scripts/activate  # Windows Git Bash
# source venv/bin/activate     # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your AWS credentials

# Create DynamoDB table
python setup_dynamodb.py

# Start server
uvicorn main:app --reload --port 8000
```

### 3. Setup Frontend
```bash
cd frontend
npm install
npm run dev
```

### 4. Access Application
Visit http://localhost:3000

## Environment Variables

Create `backend_api/.env`:
```env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_SESSION_TOKEN=your_session_token
AWS_DEFAULT_REGION=us-west-2
S3_BUCKET=ai-interview-audio-temp
```

## API Endpoints

### Interview Management
- `POST /start-interview` - Start session with dynamic questions
- `POST /get-next-question` - Get next question from session
- `GET /session/{session_id}` - Retrieve session data
- `POST /complete-session/{session_id}` - Mark session complete

### Content Processing
- `POST /upload-resume` - Upload PDF/text resume
- `POST /text-to-speech` - Generate speech via Polly
- `POST /get-feedback` - Get AI feedback with strict scoring

### Body Language
- `POST /analyze-body-language` - Analyze webcam frame
- `GET /body-language-report/{session_id}` - Get comprehensive report

## How It Works

### 1. Setup Phase
- User provides job title, job description, and resume
- AI parses resume and job description
- Claude generates 4-5 personalized questions based on:
  - Skills overlap/gaps
  - Technical requirements
  - Behavioral expectations

### 2. Interview Phase

**Practice Mode:**
- Answer each question via voice
- Get immediate AI feedback after each answer
- End interview anytime
- View summary with all feedback

**Mock Mode:**
- 10-minute timed session
- Webcam monitoring active (if enabled)
- Body language analysis every 5 seconds
- Immediate alerts for critical issues
- Comprehensive feedback at the end

### 3. Body Language Monitoring
- Captures frame every 5 seconds
- Sends to Claude for analysis
- Checks for:
  - Multiple people in frame
  - Poor eye contact (looking away)
  - Slouched posture
  - Excessive fidgeting
  - Disengaged expression
- Shows immediate pop-up alerts for medium/high severity issues
- Generates detailed report with scores (0-10)

### 4. Feedback & Scoring

**Answer Scoring (Brutally Honest):**
- 0-2: Didn't answer, refused, or off-topic
- 3-4: Very weak, generic, no examples
- 5-6: Adequate but missing details
- 7-8: Good with examples and structure
- 9-10: Excellent with metrics and impact

**Body Language Scoring:**
- 0-4: Major issues (multiple people, looking away, slouched)
- 5-6: Noticeable issues
- 7-8: Good with minor improvements
- 9-10: Excellent professional presence

### 5. Storage & Reports
- All conversations stored in DynamoDB
- Body language analysis stored per session
- Comprehensive reports with:
  - Answer scores and feedback
  - Body language metrics
  - Strengths and improvements
  - Expected answers
  - Timeline of issues

## Project Structure

```
AI-interview/
├── backend_api/
│   ├── main.py                    # FastAPI app with all endpoints
│   ├── dynamodb_service.py        # DynamoDB operations
│   ├── interview_generator.py     # Question generation
│   ├── resume_parser.py           # Resume/job parsing
│   ├── requirements.txt           # Python dependencies
│   ├── .env                       # AWS credentials
│   └── setup_dynamodb.py          # Table creation
├── frontend/
│   ├── app/
│   │   └── page.tsx               # Landing page
│   ├── components/
│   │   ├── PracticeInterview.tsx  # Practice mode
│   │   └── MockInterview.tsx      # Mock mode with body language
│   └── package.json
└── README.md
```

## Key Features Explained

### Dynamic Question Generation
Questions are generated based on:
- Resume skills vs job requirements
- Technical competencies
- Behavioral indicators
- Company culture fit

### Text-to-Speech
- Questions are spoken using Amazon Polly
- Neural voice (Joanna) for natural sound
- Replay button available during interview

### Body Language Analysis
- Real-time monitoring via webcam
- Claude analyzes each frame for:
  - Professional appearance
  - Engagement level
  - Posture and positioning
  - Eye contact with camera
- Immediate feedback for critical issues

### Brutally Honest Feedback
- No sugar-coating
- Specific, actionable suggestions
- Realistic scoring
- Helps candidates truly improve

## Dependencies

### Backend
```
fastapi==0.115.5
uvicorn==0.32.1
python-multipart==0.0.20
boto3==1.35.76
pydantic==2.10.3
PyPDF2==3.0.1
python-dotenv==1.0.0
```

### Frontend
```
next@15.x
react@18.x
typescript@5.x
tailwindcss@3.x
shadcn/ui components
```

## AWS Setup

### Required Services
1. **Bedrock** - Enable Claude 3.5 Sonnet model access
2. **Polly** - Neural voice access
3. **S3** - Create bucket: `ai-interview-audio-temp`
4. **DynamoDB** - Table created automatically by setup script

### IAM Permissions
Your AWS credentials need:
- `bedrock:InvokeModel`
- `polly:SynthesizeSpeech`
- `s3:PutObject`, `s3:GetObject`, `s3:DeleteObject`
- `dynamodb:PutItem`, `dynamodb:GetItem`, `dynamodb:UpdateItem`, `dynamodb:CreateTable`

## Troubleshooting

### Backend Issues
- **DynamoDB errors**: Run `python setup_dynamodb.py`
- **Bedrock access**: Ensure Claude 3.5 Sonnet is enabled in AWS Console
- **Token expired**: Refresh AWS credentials in `.env`

### Frontend Issues
- **Speech recognition**: Use Chrome browser
- **Webcam access**: Grant camera permissions
- **CORS errors**: Ensure backend is running on port 8000

## License
MIT

## Contributors
Built with ❤️ using AWS AI services
