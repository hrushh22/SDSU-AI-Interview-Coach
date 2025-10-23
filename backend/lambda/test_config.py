"""
Test Configuration
Enable mock mode for local testing without AWS dependencies
"""
import os

# Enable mock mode for all Lambda functions (only if not already set)
if 'MOCK_MODE' not in os.environ:
    os.environ['MOCK_MODE'] = 'true'
if 'AWS_REGION' not in os.environ:
    os.environ['AWS_REGION'] = 'us-west-2'
os.environ['SESSIONS_TABLE'] = 'InterviewSessions'
os.environ['RESUME_BUCKET'] = 'interview-coach-resumes'
os.environ['AUDIO_BUCKET'] = 'ai-interview-audio'
os.environ['TRANSCRIBE_OUTPUT_BUCKET'] = 'ai-interview-transcripts'

print("✅ Mock mode enabled for local testing")
print("   All AWS calls will be mocked")