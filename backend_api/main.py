from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import boto3
import json
import uuid
import time
import os
import PyPDF2
import io

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AWS clients
bedrock = boto3.client('bedrock-runtime', region_name='us-west-2')
transcribe = boto3.client('transcribe', region_name='us-west-2')
s3 = boto3.client('s3', region_name='us-west-2')
polly = boto3.client('polly', region_name='us-west-2')

BUCKET_NAME = os.getenv('S3_BUCKET', 'ai-interview-audio-temp')

class InterviewRequest(BaseModel):
    job_title: str
    job_description: Optional[str] = ""
    resume_text: Optional[str] = ""
    question_number: int = 1

class FeedbackRequest(BaseModel):
    question: str
    response: str
    question_type: str = "behavioral"
    word_count: int = 0
    duration: float = 0

@app.get("/")
def read_root():
    return {"message": "AI Interview Coach API"}

@app.post("/start-interview")
def start_interview(req: InterviewRequest):
    questions = [
        f"Tell me about yourself and why you're interested in this {req.job_title} position.",
        "Tell me about a time when you faced a challenging problem at work.",
        "Describe a situation where you had to work with a difficult team member.",
        f"Why do you want to work as a {req.job_title}?",
        "Tell me about a time when you had to learn something new quickly."
    ]
    return {
        "question": questions[req.question_number - 1], 
        "total_questions": len(questions),
        "question_type": "behavioral" if req.question_number > 1 else "tell_me_about"
    }

@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    try:
        content = await file.read()
        if file.filename.endswith('.pdf'):
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return {"resume_text": text.strip(), "chars": len(text)}
        else:
            text = content.decode('utf-8')
            return {"resume_text": text, "chars": len(text)}
    except Exception as e:
        return {"error": str(e)}

@app.post("/text-to-speech")
def text_to_speech(text: str = Form(...)):
    try:
        response = polly.synthesize_speech(
            Text=text,
            OutputFormat='mp3',
            VoiceId='Joanna',
            Engine='neural'
        )
        audio_data = response['AudioStream'].read()
        import base64
        return {"audio": base64.b64encode(audio_data).decode()}
    except Exception as e:
        return {"error": str(e)}

@app.post("/transcribe-audio")
async def transcribe_audio(audio: UploadFile = File(...)):
    job_name = f"interview-{uuid.uuid4()}"
    s3_key = f"audio/{job_name}.wav"
    
    # Upload to S3
    audio_bytes = await audio.read()
    s3.put_object(Bucket=BUCKET_NAME, Key=s3_key, Body=audio_bytes)
    
    # Start transcription
    transcribe.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={'MediaFileUri': f's3://{BUCKET_NAME}/{s3_key}'},
        MediaFormat='wav',
        LanguageCode='en-US'
    )
    
    # Wait for completion
    while True:
        status = transcribe.get_transcription_job(TranscriptionJobName=job_name)
        if status['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
            break
        time.sleep(2)
    
    if status['TranscriptionJob']['TranscriptionJobStatus'] == 'COMPLETED':
        transcript_uri = status['TranscriptionJob']['Transcript']['TranscriptFileUri']
        import urllib.request
        with urllib.request.urlopen(transcript_uri) as response:
            transcript_data = json.loads(response.read())
            transcript = transcript_data['results']['transcripts'][0]['transcript']
        
        # Cleanup
        transcribe.delete_transcription_job(TranscriptionJobName=job_name)
        s3.delete_object(Bucket=BUCKET_NAME, Key=s3_key)
        
        return {"transcript": transcript}
    
    return {"error": "Transcription failed"}

@app.post("/get-feedback")
def get_feedback(req: FeedbackRequest):
    # Calculate metrics
    pace_wpm = int((req.word_count / req.duration) * 60) if req.duration > 0 else 0
    pace_assessment = 'good' if 120 <= pace_wpm <= 160 else 'slow' if pace_wpm < 120 else 'fast'
    
    prompt = f"""You are an expert interview coach. Analyze this interview response.

Question: {req.question}
Question Type: {req.question_type}
Response: {req.response}

Delivery Metrics:
- Words: {req.word_count}
- Duration: {req.duration:.0f}s
- Pace: {pace_wpm} WPM ({pace_assessment})

Provide feedback in this format:

**Content Analysis:**
[Analyze content quality, structure, and relevance]

**Delivery Assessment:**
[Comment on pace, clarity, and speaking style]

**Strengths:**
[2-3 specific things they did well]

**Areas for Improvement:**
[2-3 specific suggestions with examples]

**Score: X/10**

Be constructive, specific, and encouraging."""
    
    try:
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "temperature": 0.7,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        feedback = response_body['content'][0]['text']
    except:
        # Fallback feedback
        score = 7 if req.word_count > 50 else 4
        feedback = f"""**Content Analysis:**
Response length: {req.word_count} words. {'Good detail level.' if req.word_count > 50 else 'Too brief - expand with examples.'}

**Delivery Assessment:**
Pace: {pace_wpm} WPM ({pace_assessment})

**Strengths:**
• Addresses the question
• Clear communication

**Areas for Improvement:**
• Add specific examples with STAR method
• Include quantifiable results

**Score: {score}/10**"""
    
    return {"feedback": feedback, "pace_wpm": pace_wpm, "pace_assessment": pace_assessment}
