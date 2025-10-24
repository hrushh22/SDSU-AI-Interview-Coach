from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import boto3
import json
import uuid
import time
import os
import PyPDF2
import io
from dotenv import load_dotenv
from interview_generator import generate_interview_questions, generate_followup_question
from dynamodb_service import create_table_if_not_exists, create_session, add_conversation, get_session, complete_session, get_conversation_history
from resume_parser import parse_resume, parse_job_description

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    create_table_if_not_exists()

# Initialize AWS clients
bedrock = boto3.client('bedrock-runtime', region_name='us-west-2')
transcribe = boto3.client('transcribe', region_name='us-west-2')
s3 = boto3.client('s3', region_name='us-west-2')
polly = boto3.client('polly', region_name='us-west-2')

BUCKET_NAME = os.getenv('S3_BUCKET', 'ai-interview-audio-temp')

class InterviewRequest(BaseModel):
    job_title: str
    job_description: str
    resume_text: str

class QuestionRequest(BaseModel):
    session_id: str
    question_index: int = 0

class FeedbackRequest(BaseModel):
    session_id: str
    question: str
    response: str
    question_type: str = "behavioral"
    word_count: int = 0
    duration: float = 0
    request_followup: bool = False

class BodyLanguageRequest(BaseModel):
    session_id: str
    image_base64: str
    timestamp: float
    question: str
    question_type: str = "behavioral"
    user_state: str = "speaking"

@app.get("/")
def read_root():
    return {"message": "AI Interview Coach API"}

@app.post("/start-interview")
def start_interview(req: InterviewRequest):
    try:
        resume_data = parse_resume(req.resume_text) if req.resume_text else {"error": "No resume"}
        job_data = parse_job_description(req.job_description, req.job_title) if req.job_description else {"title": req.job_title}
        
        questions_result = generate_interview_questions(resume_data, job_data)
        
        if "error" in questions_result:
            all_questions = [
                f"Tell me about your experience relevant to this {req.job_title} position.",
                "Describe a challenging technical problem you've solved.",
                "Tell me about a time you worked in a team to deliver a project.",
                "Describe a situation where you had to handle a difficult deadline.",
                "Give me an example of when you had to learn something new quickly."
            ]
        else:
            # Ensure we get both technical and behavioral questions
            tech_questions = questions_result.get('technical_questions', [])
            behavioral_questions = questions_result.get('behavioral_questions', [])
            
            # Combine: behavioral first, then technical (for better flow)
            all_questions = behavioral_questions + tech_questions
            
            # Fallback if parsing failed
            if len(all_questions) < 3:
                all_questions = [
                    f"Tell me about your experience with the key responsibilities in this {req.job_title} role.",
                    "Describe a challenging situation you faced and how you resolved it.",
                    "Tell me about a time you collaborated with a team to achieve a goal.",
                    "How do you approach problem-solving in your work?",
                    "Give me an example of a project you're proud of and why."
                ]
        
        session_id = create_session(req.job_title, req.job_description, req.resume_text)
        
        from dynamodb_service import dynamodb, TABLE_NAME
        table = dynamodb.Table(TABLE_NAME)
        table.update_item(
            Key={'session_id': session_id},
            UpdateExpression='SET questions = :q, resume_data = :r, job_data = :j',
            ExpressionAttributeValues={':q': all_questions, ':r': resume_data, ':j': job_data}
        )
        
        # Determine question type based on content
        first_question = all_questions[0]
        question_type = "behavioral" if any(phrase in first_question.lower() for phrase in ["tell me about", "describe a", "give me an example"]) else "technical"
        
        return {
            "session_id": session_id,
            "question": first_question,
            "total_questions": len(all_questions),
            "question_type": question_type,
            "debug_info": {
                "tech_count": len(questions_result.get('technical_questions', [])),
                "behavioral_count": len(questions_result.get('behavioral_questions', [])),
                "rationale": questions_result.get('rationale', 'N/A')
            }
        }
    except Exception as e:
        return {"error": str(e)}

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
    try:
        pace_wpm = int((req.word_count / req.duration) * 60) if req.duration > 0 else 0
        pace_assessment = 'good' if 120 <= pace_wpm <= 160 else 'slow' if pace_wpm < 120 else 'fast'
        
        prompt = f"""You are a BRUTALLY HONEST interview coach. Your job is to give REAL feedback that will actually help candidates improve.

Question: {req.question}
Question Type: {req.question_type}
Response: {req.response}

Delivery Metrics:
- Words: {req.word_count}
- Duration: {req.duration:.0f}s
- Pace: {pace_wpm} WPM ({pace_assessment})

BE HONEST AND DIRECT:
- If the answer is terrible, say so (score 1-3/10)
- If they didn't answer the question, call it out
- If they gave a generic/vague answer, point it out
- If they refused to answer or gave a joke response, score it 0-1/10
- Only give high scores (8-10) for truly excellent answers with specific examples

Provide feedback in this format:

**Content Analysis:**
[Be HONEST - did they actually answer the question? Was it specific or vague? Did they use real examples?]

**Delivery Assessment:**
[Comment on pace, clarity, and speaking style - be direct about issues]

**Strengths:**
[List ONLY if there are actual strengths - don't make them up]

**Areas for Improvement:**
[Be SPECIFIC and DIRECT about what needs to change]

**Expected Answer:**
[Provide a concrete example of what a GOOD answer would include]

**Score: X/10**

SCORING GUIDE:
0-2: Didn't answer, refused, or completely off-topic
3-4: Answered but very weak, generic, no examples
5-6: Adequate but missing key details or structure
7-8: Good answer with examples and structure
9-10: Excellent answer with specific examples, metrics, and clear impact

Be BRUTALLY HONEST. This is practice - they need real feedback to improve."""
        
        score = 5
        expected_answer = "A strong answer would include specific examples using the STAR method, quantifiable results, and clear demonstration of relevant skills."
        
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
            
            # Extract score from feedback
            import re
            score_match = re.search(r'\*\*Score:\s*(\d+)/10\*\*', feedback)
            if score_match:
                score = int(score_match.group(1))
            
            # Extract expected answer
            expected_match = re.search(r'\*\*Expected Answer:\*\*\s*([^*]+)', feedback, re.DOTALL)
            if expected_match:
                expected_answer = expected_match.group(1).strip()
                
        except Exception as bedrock_error:
            print(f"Bedrock error: {bedrock_error}")
            score = 3 if req.word_count > 50 else 1
            feedback = f"""**Content Analysis:**
Response length: {req.word_count} words. {'Lacks specific examples and structure.' if req.word_count > 50 else 'Far too brief - this would fail in a real interview.'}

**Delivery Assessment:**
Pace: {pace_wpm} WPM ({pace_assessment})

**Strengths:**
None identified - answer needs significant improvement.

**Areas for Improvement:**
• Provide specific examples using STAR method (Situation, Task, Action, Result)
• Include quantifiable results and metrics
• Answer the question directly and completely

**Expected Answer:**
{expected_answer}

**Score: {score}/10**

This answer would not pass in a real interview. Practice with concrete examples."""
        
        metrics = {"word_count": req.word_count, "duration": req.duration, "pace_wpm": pace_wpm, "pace_assessment": pace_assessment}
        
        # Store conversation in DynamoDB
        try:
            add_conversation(req.session_id, req.question, req.response, feedback, metrics)
        except Exception as db_error:
            print(f"DynamoDB error: {db_error}")
            # Continue even if storage fails
        
        followup_question = None
        if req.request_followup:
            try:
                session = get_session(req.session_id)
                job_context = f"{session.get('job_title', '')} - {session.get('job_description', '')[:200]}"
                followup_question = generate_followup_question(req.question, req.response, job_context)
            except Exception as followup_error:
                print(f"Follow-up generation error: {followup_error}")
        
        return {
            "feedback": feedback,
            "pace_wpm": pace_wpm,
            "pace_assessment": pace_assessment,
            "followup_question": followup_question,
            "score": score,
            "expected_answer": expected_answer
        }
    
    except Exception as e:
        print(f"Error in get_feedback: {e}")
        return {"error": str(e)}


@app.post("/get-next-question")
def get_next_question(req: QuestionRequest):
    """Get next question from session"""
    try:
        session = get_session(req.session_id)
        questions = session.get('questions', [])
        
        if req.question_index >= len(questions):
            return {"completed": True, "message": "Interview completed"}
        
        return {
            "question": questions[req.question_index],
            "question_index": req.question_index,
            "total_questions": len(questions),
            "completed": False
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/session/{session_id}")
def get_session_data(session_id: str):
    """Get full session data including all conversations"""
    try:
        session = get_session(session_id)
        return session
    except Exception as e:
        return {"error": str(e)}

@app.post("/complete-session/{session_id}")
def finish_session(session_id: str):
    """Mark session as complete"""
    try:
        complete_session(session_id)
        return {"message": "Session completed", "session_id": session_id}
    except Exception as e:
        return {"error": str(e)}

@app.post("/analyze-body-language")
def analyze_body_language(req: BodyLanguageRequest):
    """Analyze body language from webcam frame"""
    try:
        from decimal import Decimal
        
        prompt = f"""You are a BRUTALLY HONEST body language coach analyzing a mock interview.

Analyze this frame at {req.timestamp:.0f} seconds:
Question: '{req.question}'
User state: {req.user_state}

BE HONEST AND STRICT:
- Multiple people in frame = HIGH severity ("Only one person should be visible")
- Looking away from camera = MEDIUM/HIGH severity ("Look directly at the camera")
- Slouched posture = MEDIUM severity ("Sit up straight")
- Fidgeting, head shaking = MEDIUM severity ("Stay still and composed")
- Distracted/bored expression = MEDIUM severity ("Show engagement and interest")
- Unprofessional background = MEDIUM severity ("Use a clean, professional background")
- Poor lighting = LOW severity ("Improve lighting on your face")

SCORING (be strict):
- 0-4: Major issues (multiple people, looking away, slouched)
- 5-6: Noticeable issues (occasional poor posture, some fidgeting)
- 7-8: Good but minor improvements needed
- 9-10: Excellent professional presence

Respond in JSON format:
{{
  "strengths": ["brief strength if any"],
  "improvements": ["specific issue"],
  "actionable_tip": "IMMEDIATE action to take NOW",
  "severity_level": "low/medium/high",
  "eye_contact_score": 0-10,
  "posture_score": 0-10,
  "engagement_score": 0-10,
  "professionalism_score": 0-10
}}

Be BRUTALLY HONEST. Set severity to HIGH for serious issues. Don't be lenient."""
        
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 800,
            "temperature": 0.5,
            "messages": [{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": req.image_base64
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }]
        }
        
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        feedback_text = response_body['content'][0]['text']
        
        # Parse JSON from response
        import re
        json_match = re.search(r'\{[^}]+\}', feedback_text, re.DOTALL)
        if json_match:
            feedback_data = json.loads(json_match.group())
        else:
            feedback_data = {
                "strengths": ["Maintaining presence"],
                "improvements": ["Continue monitoring posture"],
                "actionable_tip": "Keep engaging with the camera",
                "severity_level": "low",
                "eye_contact_score": 7,
                "posture_score": 7,
                "engagement_score": 7,
                "professionalism_score": 7
            }
        
        # Store in DynamoDB with Decimal conversion
        from dynamodb_service import dynamodb, TABLE_NAME
        table = dynamodb.Table(TABLE_NAME)
        session = table.get_item(Key={'session_id': req.session_id}).get('Item', {})
        body_language_data = session.get('body_language_analysis', [])
        
        # Convert to DynamoDB-compatible format
        db_feedback = {
            'timestamp': Decimal(str(req.timestamp)),
            'feedback': {
                'strengths': feedback_data.get('strengths', []),
                'improvements': feedback_data.get('improvements', []),
                'actionable_tip': feedback_data.get('actionable_tip', ''),
                'severity_level': feedback_data.get('severity_level', 'low'),
                'eye_contact_score': Decimal(str(feedback_data.get('eye_contact_score', 7))),
                'posture_score': Decimal(str(feedback_data.get('posture_score', 7))),
                'engagement_score': Decimal(str(feedback_data.get('engagement_score', 7))),
                'professionalism_score': Decimal(str(feedback_data.get('professionalism_score', 7)))
            },
            'question': req.question
        }
        
        body_language_data.append(db_feedback)
        table.update_item(
            Key={'session_id': req.session_id},
            UpdateExpression='SET body_language_analysis = :b',
            ExpressionAttributeValues={':b': body_language_data}
        )
        
        severity = feedback_data.get('severity_level', 'low')
        tip = feedback_data.get('actionable_tip', '')
        print(f"{'🚨' if severity == 'high' else '⚠️' if severity == 'medium' else '✅'} [{req.timestamp:.0f}s] {severity.upper()}: {tip}")
        return feedback_data
        
    except Exception as e:
        print(f"❌ Body language analysis error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "strengths": ["Participating in interview"],
            "improvements": ["Keep monitoring your posture"],
            "actionable_tip": "Maintain eye contact with camera",
            "severity_level": "low",
            "eye_contact_score": 7,
            "posture_score": 7,
            "engagement_score": 7,
            "professionalism_score": 7,
            "error": str(e)
        }

@app.get("/body-language-report/{session_id}")
def get_body_language_report(session_id: str):
    """Get comprehensive body language report for session"""
    try:
        from dynamodb_service import dynamodb, TABLE_NAME
        from decimal import Decimal
        
        table = dynamodb.Table(TABLE_NAME)
        session = table.get_item(Key={'session_id': session_id}).get('Item', {})
        body_language_data = session.get('body_language_analysis', [])
        
        if not body_language_data:
            return {"message": "No body language data available"}
        
        # Calculate aggregated metrics (convert Decimal to float)
        total_frames = len(body_language_data)
        avg_eye_contact = sum(float(f['feedback'].get('eye_contact_score', 0)) for f in body_language_data) / total_frames
        avg_posture = sum(float(f['feedback'].get('posture_score', 0)) for f in body_language_data) / total_frames
        avg_engagement = sum(float(f['feedback'].get('engagement_score', 0)) for f in body_language_data) / total_frames
        avg_professionalism = sum(float(f['feedback'].get('professionalism_score', 0)) for f in body_language_data) / total_frames
        
        # Collect all strengths and improvements
        all_strengths = []
        all_improvements = []
        critical_moments = []
        
        for frame in body_language_data:
            feedback = frame['feedback']
            all_strengths.extend(feedback.get('strengths', []))
            all_improvements.extend(feedback.get('improvements', []))
            if feedback.get('severity_level') in ['high', 'medium']:
                critical_moments.append({
                    'timestamp': float(frame['timestamp']),
                    'issue': feedback.get('actionable_tip', 'Review this moment')
                })
        
        # Get top 3 unique strengths and improvements
        from collections import Counter
        top_strengths = [s for s, _ in Counter(all_strengths).most_common(3)]
        top_improvements = [i for i, _ in Counter(all_improvements).most_common(3)]
        
        print(f"📊 Body language report: {total_frames} frames, avg scores: eye={avg_eye_contact:.1f}, posture={avg_posture:.1f}")
        
        return {
            "overall_scores": {
                "eye_contact": round(avg_eye_contact, 1),
                "posture": round(avg_posture, 1),
                "engagement": round(avg_engagement, 1),
                "professionalism": round(avg_professionalism, 1)
            },
            "top_strengths": top_strengths,
            "top_improvements": top_improvements,
            "critical_moments": critical_moments,
            "total_frames_analyzed": total_frames
        }
        
    except Exception as e:
        print(f"❌ Error generating body language report: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}
