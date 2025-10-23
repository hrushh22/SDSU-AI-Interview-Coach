# 🚀 Quick Start Guide

## ✅ S3 Bucket Created!

Your setup is ready. Follow these steps:

### 1. Start Backend (Terminal 1)
```bash
cd backend_api
pip install -r requirements.txt
```

Then run:
```bash
start_backend.bat
```

Backend will run at: http://localhost:8000

### 2. Start Frontend (Terminal 2)
```bash
cd frontend
npm install
npm run dev
```

Frontend will run at: http://localhost:3000

### 3. Use the App
1. Open http://localhost:3000
2. Enter job title
3. Click "Start Interview"
4. Click "Start Recording" to record your answer
5. Click "Stop Recording" when done
6. Audio is transcribed via Amazon Transcribe
7. Get AI feedback from Claude

## 🔧 If credentials expire:
Update credentials in `start_backend.bat` and `.streamlit/secrets.toml`
