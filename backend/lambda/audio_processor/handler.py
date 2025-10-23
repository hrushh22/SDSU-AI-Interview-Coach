import json
import boto3
import os
import base64
import re
from datetime import datetime

# Initialize AWS clients
AWS_REGION = os.environ.get('AWS_REGION', 'us-west-2')
MOCK_MODE = os.environ.get('MOCK_MODE', 'false').lower() == 'true'

if not MOCK_MODE:
    s3_client = boto3.client('s3', region_name=AWS_REGION)
    transcribe_client = boto3.client('transcribe', region_name=AWS_REGION)
else:
    s3_client = None
    transcribe_client = None

# Environment variables
S3_BUCKET = os.environ.get('AUDIO_BUCKET', 'ai-interview-audio')
TRANSCRIBE_OUTPUT_BUCKET = os.environ.get('TRANSCRIBE_OUTPUT_BUCKET', 'ai-interview-transcripts')

# Filler words to detect
FILLER_WORDS = ['um', 'uh', 'like', 'you know', 'basically', 'actually', 'literally', 
                'sort of', 'kind of', 'i mean', 'so', 'well', 'right']


def assess_pace(wpm):
    """
    Assess speaking pace based on words per minute
    
    Args:
        wpm (int): Words per minute
        
    Returns:
        str: Pace assessment
    """
    if wpm < 120:
        return "slow"
    elif 120 <= wpm < 160:
        return "good"
    elif 160 <= wpm < 200:
        return "fast"
    else:
        return "very fast"


def analyze_speech_metrics(transcript, duration):
    """
    Analyze speech metrics from transcript and duration
    
    Args:
        transcript (str): The speech transcript
        duration (float): Duration in seconds
        
    Returns:
        dict: Speech metrics including pace, filler words, etc.
    """
    # Count words
    words = transcript.split()
    word_count = len(words)
    
    # Calculate pace (words per minute)
    pace_wpm = int((word_count / duration) * 60) if duration > 0 else 0
    
    # Count filler words
    transcript_lower = transcript.lower()
    filler_count = 0
    filler_details = []
    
    for filler in FILLER_WORDS:
        # Use word boundaries to avoid partial matches
        pattern = r'\b' + re.escape(filler) + r'\b'
        matches = re.findall(pattern, transcript_lower)
        count = len(matches)
        if count > 0:
            filler_count += count
            filler_details.append({
                'word': filler,
                'count': count
            })
    
    # Calculate filler rate (percentage)
    filler_rate = round((filler_count / word_count * 100), 2) if word_count > 0 else 0
    
    # Assess pace
    pace_assessment = assess_pace(pace_wpm)
    
    # Calculate additional metrics
    avg_word_length = sum(len(word) for word in words) / word_count if word_count > 0 else 0
    
    return {
        'word_count': word_count,
        'pace_wpm': pace_wpm,
        'pace_assessment': pace_assessment,
        'filler_count': filler_count,
        'filler_rate': filler_rate,
        'filler_details': filler_details,
        'duration': duration,
        'avg_word_length': round(avg_word_length, 2)
    }


def lambda_handler(event, context):
    """
    Main handler for audio processing Lambda
    Handles audio upload, transcription, and analysis
    """
    try:
        # Parse the incoming event
        body = json.loads(event.get('body', '{}'))
        action = body.get('action', '')
        
        # Route to appropriate handler
        if action == 'upload':
            return handle_audio_upload(body)
        elif action == 'transcribe':
            return handle_transcription(body)
        elif action == 'status':
            return handle_transcription_status(body)
        elif action == 'analyze_speech':
            return handle_speech_analysis(body)
        elif action == 'analyze':
            return handle_audio_analysis(body)
        else:
            return response(400, {'error': f'Invalid action: {action}'})
            
    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        return response(500, {'error': str(e)})


def handle_speech_analysis(body):
    """
    Analyze speech from transcript and duration
    """
    try:
        # Validate inputs
        transcript = body.get('transcript', '')
        if not transcript or not isinstance(transcript, str):
            return response(400, {'error': 'Valid transcript is required'})
        
        # Limit transcript length
        if len(transcript) > 10000:
            return response(400, {'error': 'Transcript too long (max 10KB)'})
        
        duration = body.get('duration', 0)
        if not isinstance(duration, (int, float)) or duration <= 0:
            return response(400, {'error': 'Valid duration (>0) is required'})
        
        # Analyze the speech
        metrics = analyze_speech_metrics(transcript, duration)
        
        return response(200, {
            'message': 'Speech analysis completed',
            'metrics': metrics
        })
        
    except Exception as e:
        print(f"Error in handle_speech_analysis: {str(e)}")
        return response(500, {'error': str(e)})


def handle_audio_upload(body):
    """
    Upload audio file to S3
    Expects base64 encoded audio data
    """
    try:
        # Validate required fields
        interview_id = body.get('interview_id')
        question_id = body.get('question_id')
        audio_data = body.get('audio_data')
        
        if not interview_id or not isinstance(interview_id, str):
            return response(400, {'error': 'Valid interview_id is required'})
        if not question_id or not isinstance(question_id, str):
            return response(400, {'error': 'Valid question_id is required'})
        if not audio_data or not isinstance(audio_data, str):
            return response(400, {'error': 'Valid audio_data is required'})
        
        # Validate audio format
        audio_format = body.get('format', 'webm')
        valid_formats = ['webm', 'mp3', 'wav', 'ogg']
        if audio_format not in valid_formats:
            return response(400, {'error': f'Invalid format. Must be one of: {valid_formats}'})
        
        # Validate audio data size (10MB limit)
        if len(audio_data) > 13421772:  # base64 encoded 10MB
            return response(400, {'error': 'Audio file too large (max 10MB)'})
        
        # Decode base64 audio
        audio_bytes = base64.b64decode(audio_data)
        
        # Generate S3 key
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        s3_key = f"interviews/{interview_id}/questions/{question_id}/audio_{timestamp}.{audio_format}"
        
        # Upload to S3
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=audio_bytes,
            ContentType=f'audio/{audio_format}',
            Metadata={
                'interview_id': interview_id,
                'question_id': question_id,
                'timestamp': timestamp
            }
        )
        
        # Generate S3 URL
        s3_url = f"s3://{S3_BUCKET}/{s3_key}"
        
        return response(200, {
            'message': 'Audio uploaded successfully',
            'audio_url': s3_url,
            's3_key': s3_key,
            'interview_id': interview_id,
            'question_id': question_id
        })
        
    except Exception as e:
        print(f"Error in handle_audio_upload: {str(e)}")
        return response(500, {'error': str(e)})


def handle_transcription(body):
    """
    Start AWS Transcribe job for audio file
    """
    try:
        # Validate required fields
        audio_url = body.get('audio_url')
        interview_id = body.get('interview_id')
        question_id = body.get('question_id')
        
        if not audio_url or not isinstance(audio_url, str):
            return response(400, {'error': 'Valid audio_url is required'})
        if not interview_id or not isinstance(interview_id, str):
            return response(400, {'error': 'Valid interview_id is required'})
        if not question_id or not isinstance(question_id, str):
            return response(400, {'error': 'Valid question_id is required'})
        
        # Validate S3 URL format
        if not audio_url.startswith('s3://'):
            return response(400, {'error': 'Invalid S3 URL format'})
        
        language_code = body.get('language_code', 'en-US')
        valid_languages = ['en-US', 'en-GB', 'es-US', 'fr-FR', 'de-DE']
        if language_code not in valid_languages:
            return response(400, {'error': f'Invalid language code. Must be one of: {valid_languages}'})
        
        # Generate unique job name
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')
        job_name = f"interview_{interview_id}_q_{question_id}_{timestamp}"
        
        # Start transcription job
        transcribe_client.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': audio_url},
            MediaFormat='webm',  # Adjust based on your audio format
            LanguageCode=language_code,
            OutputBucketName=TRANSCRIBE_OUTPUT_BUCKET,
            Settings={
                'ShowSpeakerLabels': False,
                'MaxSpeakerLabels': 1
            }
        )
        
        return response(200, {
            'message': 'Transcription job started',
            'job_name': job_name,
            'interview_id': interview_id,
            'question_id': question_id,
            'status': 'IN_PROGRESS'
        })
        
    except Exception as e:
        print(f"Error in handle_transcription: {str(e)}")
        return response(500, {'error': str(e)})


def handle_transcription_status(body):
    """
    Check status of transcription job
    """
    try:
        # Validate job_name
        job_name = body.get('job_name')
        if not job_name or not isinstance(job_name, str):
            return response(400, {'error': 'Valid job_name is required'})
        
        # Get job status
        result = transcribe_client.get_transcription_job(
            TranscriptionJobName=job_name
        )
        
        job_status = result['TranscriptionJob']['TranscriptionJobStatus']
        
        response_data = {
            'job_name': job_name,
            'status': job_status
        }
        
        # If completed, include transcript
        if job_status == 'COMPLETED':
            transcript_uri = result['TranscriptionJob']['Transcript']['TranscriptFileUri']
            response_data['transcript_uri'] = transcript_uri
            
        elif job_status == 'FAILED':
            response_data['failure_reason'] = result['TranscriptionJob'].get('FailureReason', 'Unknown')
        
        return response(200, response_data)
        
    except Exception as e:
        print(f"Error in handle_transcription_status: {str(e)}")
        return response(500, {'error': str(e)})


def handle_audio_analysis(body):
    """
    Analyze audio characteristics (tone, pace, clarity, etc.)
    This is a placeholder for more sophisticated audio analysis
    """
    try:
        # Validate inputs
        audio_url = body.get('audio_url')
        if not audio_url or not isinstance(audio_url, str):
            return response(400, {'error': 'Valid audio_url is required'})
        
        transcript = body.get('transcript', '')
        duration = body.get('duration', 0)
        
        if transcript and not isinstance(transcript, str):
            return response(400, {'error': 'Invalid transcript format'})
        if duration and not isinstance(duration, (int, float)):
            return response(400, {'error': 'Invalid duration format'})
        
        # If transcript and duration provided, do speech analysis
        speech_metrics = {}
        if transcript and duration > 0:
            speech_metrics = analyze_speech_metrics(transcript, duration)
        
        # Placeholder for additional audio analysis
        # In production, you might use:
        # - Amazon Comprehend for sentiment analysis
        # - Custom ML models for speech analysis
        # - Audio processing libraries for pace/clarity metrics
        
        analysis = {
            'speech_metrics': speech_metrics,
            'audio_quality': {
                'clarity_score': 0.85,  # 0-1 scale
                'volume_consistency': 0.9,  # 0-1 scale
                'background_noise_level': 'low'
            },
            'delivery': {
                'confidence_level': 'high',
                'energy_level': 'moderate',
                'tone': 'professional'
            }
        }
        
        return response(200, {
            'message': 'Audio analysis completed',
            'analysis': analysis
        })
        
    except Exception as e:
        print(f"Error in handle_audio_analysis: {str(e)}")
        return response(500, {'error': str(e)})


def response(status_code, body):
    """
    Helper function to format API Gateway response
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
        },
        'body': json.dumps(body)
    }